from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app.controllers.decorators import perfil_requerido
from app.models import (
    db, Usuario, Psicologo, Recepcionista, Administrador,
    Paciente, Consulta, Pagamento, ConfiguracaoClinica, LogAuditoria
)
from app.services.excel_exporter import gerar_excel_administrativo

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
@login_required
@perfil_requerido("ADMINISTRADOR")
def dashboard():
    hoje = datetime.now().date()
    inicio_hoje = datetime.combine(hoje, datetime.min.time())
    fim_hoje = datetime.combine(hoje, datetime.max.time())

    total_pacientes = Paciente.query.count()
    pacientes_ativos = Paciente.query.filter_by(status="ATIVO").count()
    consultas_hoje = Consulta.query.filter(Consulta.data_hora >= inicio_hoje, Consulta.data_hora <= fim_hoje).order_by(Consulta.data_hora.asc()).all()
    total_consultas_mes = Consulta.query.filter(db.extract("month", Consulta.data_hora) == hoje.month).count()
    
    pagamentos_pagos = Pagamento.query.filter_by(status="PAGO").all()
    receita_total = sum(p.valor_final for p in pagamentos_pagos)
    pagamentos_pendentes = Pagamento.query.filter_by(status="PENDENTE").count()
    faltas_cancelamentos = Consulta.query.filter(Consulta.status.in_(["FALTA", "CANCELADA"])).count()

    return render_template(
        "admin/dashboard.html",
        total_pacientes=total_pacientes,
        pacientes_ativos=pacientes_ativos,
        consultas_hoje=consultas_hoje,
        total_consultas_mes=total_consultas_mes,
        receita_total=receita_total,
        pagamentos_pendentes=pagamentos_pendentes,
        faltas_cancelamentos=faltas_cancelamentos
    )

@admin_bp.route("/exportar-excel")
@login_required
@perfil_requerido("ADMINISTRADOR")
def exportar_excel():
    pacientes = Paciente.query.order_by(Paciente.nome_completo.asc()).all()
    consultas = Consulta.query.order_by(Consulta.data_hora.desc()).all()
    pagamentos = Pagamento.query.all()

    excel_io = gerar_excel_administrativo(pacientes, consultas, pagamentos)
    log = LogAuditoria(usuario_id=current_user.id, acao="EXPORTAR_EXCEL", detalhes="Relatório gerencial Excel exportado.", ip_origem=request.remote_addr)
    db.session.add(log)
    db.session.commit()

    nome_arquivo = f"Relatorio_Clinica_GV_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(
        excel_io,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=nome_arquivo
    )

@admin_bp.route("/usuarios", methods=["GET", "POST"])
@login_required
@perfil_requerido("ADMINISTRADOR")
def usuarios():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha")
        perfil = request.form.get("perfil")

        if Usuario.query.filter_by(email=email).first():
            flash("Já existe um usuário com este e-mail.", "danger")
            return redirect(url_for("admin.usuarios"))

        novo_user = Usuario(nome=nome, email=email, perfil=perfil, ativo=True)
        novo_user.set_senha(senha)
        db.session.add(novo_user)
        db.session.flush()

        if perfil == "PSICOLOGO":
            psi = Psicologo(
                usuario_id=novo_user.id,
                crp=request.form.get("crp", "CRP 06/00000"),
                especialidade=request.form.get("especialidade", "Psicologia Clínica"),
                telefone=request.form.get("telefone", "")
            )
            db.session.add(psi)
        elif perfil == "RECEPCIONISTA":
            rec = Recepcionista(
                usuario_id=novo_user.id,
                turno=request.form.get("turno", "Integral"),
                telefone=request.form.get("telefone", "")
            )
            db.session.add(rec)
        else:
            adm = Administrador(usuario_id=novo_user.id, cargo=request.form.get("cargo", "Administrador"))
            db.session.add(adm)

        db.session.add(LogAuditoria(usuario_id=current_user.id, acao="CRIAR_USUARIO", detalhes=f"Criou {email} ({perfil})"))
        db.session.commit()
        flash("Usuário cadastrado com sucesso!", "success")
        return redirect(url_for("admin.usuarios"))

    lista_usuarios = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    return render_template("admin/usuarios.html", usuarios=lista_usuarios)

@admin_bp.route("/usuarios/<int:user_id>/toggle-status", methods=["POST"])
@login_required
@perfil_requerido("ADMINISTRADOR")
def toggle_usuario(user_id):
    u = Usuario.query.get_or_404(user_id)
    if u.id == current_user.id:
        flash("Você não pode bloquear a própria conta.", "warning")
    else:
        u.ativo = not u.ativo
        db.session.commit()
        flash(f"Status de {u.nome} atualizado para {'Ativo' if u.ativo else 'Bloqueado'}.", "info")
    return redirect(url_for("admin.usuarios"))

@admin_bp.route("/configuracoes", methods=["GET", "POST"])
@login_required
@perfil_requerido("ADMINISTRADOR")
def configuracoes():
    config = ConfiguracaoClinica.query.first()
    if request.method == "POST":
        config.nome_clinica = request.form.get("nome_clinica")
        config.cnpj = request.form.get("cnpj")
        config.endereco = request.form.get("endereco")
        config.telefone = request.form.get("telefone")
        config.email_contato = request.form.get("email_contato")
        config.valor_consulta_padrao = float(request.form.get("valor_consulta_padrao", 180.0))
        config.quem_somos_titulo = request.form.get("quem_somos_titulo")
        config.quem_somos_texto = request.form.get("quem_somos_texto")
        config.especialista_nome = request.form.get("especialista_nome")
        config.especialista_crp = request.form.get("especialista_crp")
        config.especialista_formacao = request.form.get("especialista_formacao")
        db.session.commit()
        flash("Configurações da clínica e da seção 'Quem Somos Nós' atualizadas!", "success")
        return redirect(url_for("admin.configuracoes"))
    return render_template("admin/configuracoes.html", config=config)

@admin_bp.route("/logs")
@login_required
@perfil_requerido("ADMINISTRADOR")
def logs():
    registros = LogAuditoria.query.order_by(LogAuditoria.data_hora.desc()).limit(100).all()
    return render_template("admin/logs.html", logs=registros)
