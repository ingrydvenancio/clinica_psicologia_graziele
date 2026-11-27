import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.controllers.decorators import perfil_requerido
from app.models import db, Paciente, Psicologo, Consulta, Pagamento, ConfiguracaoClinica, LogAuditoria
from app.services.notification_scheduler import verificar_alertas_5_dias

recepcao_bp = Blueprint("recepcao", __name__, url_prefix="/recepcao")

@recepcao_bp.route("/dashboard")
@login_required
@perfil_requerido("RECEPCIONISTA", "ADMINISTRADOR")
def dashboard():
    hoje = datetime.now().date()
    inicio_hoje = datetime.combine(hoje, datetime.min.time())
    fim_hoje = datetime.combine(hoje, datetime.max.time())

    consultas_hoje = Consulta.query.filter(Consulta.data_hora >= inicio_hoje, Consulta.data_hora <= fim_hoje).order_by(Consulta.data_hora.asc()).all()
    total_pacientes = Paciente.query.count()
    pendentes = Consulta.query.filter_by(status="PENDENTE").count()
    cancelamentos = Consulta.query.filter_by(status="CANCELADA").count()
    pgtos_pendentes = Pagamento.query.filter_by(status="PENDENTE").count()

    return render_template(
        "recepcao/dashboard.html",
        consultas_hoje=consultas_hoje,
        total_pacientes=total_pacientes,
        pendentes=pendentes,
        cancelamentos=cancelamentos,
        pgtos_pendentes=pgtos_pendentes
    )

@recepcao_bp.route("/pacientes", methods=["GET", "POST"])
@login_required
@perfil_requerido("RECEPCIONISTA", "ADMINISTRADOR")
def pacientes():
    if request.method == "POST":
        cpf = request.form.get("cpf", "").strip()
        if Paciente.query.filter_by(cpf=cpf).first():
            flash("Já existe um paciente cadastrado com este CPF.", "danger")
            return redirect(url_for("recepcao.pacientes"))

        dt_nasc = datetime.strptime(request.form.get("data_nascimento"), "%Y-%m-%d").date()
        psi_id = request.form.get("psicologo_id")
        novo_pac = Paciente(
            nome_completo=request.form.get("nome_completo"),
            cpf=cpf,
            data_nascimento=dt_nasc,
            telefone=request.form.get("telefone"),
            email=request.form.get("email"),
            endereco=request.form.get("endereco"),
            contato_emergencia=request.form.get("contato_emergencia"),
            psicologo_id=int(psi_id) if psi_id else None,
            observacoes_admin=request.form.get("observacoes_admin"),
            status="ATIVO"
        )
        db.session.add(novo_pac)
        db.session.commit()
        flash("Paciente cadastrado com sucesso!", "success")
        return redirect(url_for("recepcao.pacientes"))

    busca = request.args.get("q", "").strip()
    query = Paciente.query
    if busca:
        query = query.filter(
            db.or_(
                Paciente.nome_completo.ilike(f"%{busca}%"),
                Paciente.cpf.ilike(f"%{busca}%"),
                Paciente.telefone.ilike(f"%{busca}%")
            )
        )
    lista = query.order_by(Paciente.nome_completo.asc()).all()
    psicologos = Psicologo.query.all()
    return render_template("recepcao/pacientes.html", pacientes=lista, psicologos=psicologos, busca=busca)

@recepcao_bp.route("/agenda", methods=["GET", "POST"])
@login_required
@perfil_requerido("RECEPCIONISTA", "ADMINISTRADOR")
def agenda():
    config = ConfiguracaoClinica.query.first()
    if request.method == "POST":
        paciente_id = int(request.form.get("paciente_id"))
        psicologo_id = int(request.form.get("psicologo_id"))
        data_str = request.form.get("data")
        hora_str = request.form.get("hora")
        data_hora = datetime.strptime(f"{data_str} {hora_str}", "%Y-%m-%d %H:%M")

        # Verifica conflito de horário do psicólogo
        conflito = Consulta.query.filter(
            Consulta.psicologo_id == psicologo_id,
            Consulta.data_hora == data_hora,
            Consulta.status.notin_(["CANCELADA"])
        ).first()
        if conflito:
            flash("Este psicólogo já possui consulta marcada neste horário!", "danger")
            return redirect(url_for("recepcao.agenda"))

        valor = float(request.form.get("valor", config.valor_consulta_padrao if config else 180.0))
        desconto = float(request.form.get("desconto", 0.0))
        convenio = request.form.get("convenio", "Particular")

        consulta = Consulta(
            paciente_id=paciente_id,
            psicologo_id=psicologo_id,
            data_hora=data_hora,
            sala=request.form.get("sala", "Sala 01"),
            valor=valor,
            desconto=desconto,
            convenio=convenio,
            token_confirmacao=str(uuid.uuid4()),
            observacoes=request.form.get("observacoes", "")
        )
        db.session.add(consulta)
        db.session.flush()

        pgto = Pagamento(
            consulta_id=consulta.id,
            valor_final=max(valor - desconto, 0.0),
            forma_pagamento=request.form.get("forma_pagamento", "PIX"),
            status="PENDENTE",
            recibo_numero=f"REC-{datetime.now().strftime('%Y')}-{consulta.id:05d}"
        )
        db.session.add(pgto)
        db.session.commit()

        # Dispara verificação imediata caso já falte exatamente 5 dias corridos
        verificar_alertas_5_dias(current_app._get_current_object(), request.url_root.rstrip("/"))
        flash("Consulta agendada com sucesso!", "success")
        return redirect(url_for("recepcao.agenda"))

    pacientes = Paciente.query.filter_by(status="ATIVO").order_by(Paciente.nome_completo.asc()).all()
    psicologos = Psicologo.query.all()
    consultas = Consulta.query.order_by(Consulta.data_hora.desc()).all()
    return render_template("recepcao/agenda.html", pacientes=pacientes, psicologos=psicologos, consultas=consultas, config=config)

@recepcao_bp.route("/api/eventos-calendario")
@login_required
def api_eventos_calendario():
    query = Consulta.query
    if current_user.perfil == "PSICOLOGO" and current_user.psicologo:
        query = query.filter_by(psicologo_id=current_user.psicologo.id)

    cores = {
        "PENDENTE": "#f59e0b",
        "CONFIRMADA": "#10b981",
        "EM_ATENDIMENTO": "#3b82f6",
        "CONCLUIDA": "#6366f1",
        "CANCELADA": "#ef4444",
        "FALTA": "#64748b"
    }
    eventos = []
    for c in query.all():
        eventos.append({
            "id": c.id,
            "title": f"{c.paciente.nome_completo} ({c.status})",
            "start": c.data_hora.isoformat(),
            "color": cores.get(c.status, "#0F3460"),
            "extendedProps": {
                "psicologo": c.psicologo.usuario.nome,
                "sala": c.sala,
                "status": c.status
            }
        })
    return jsonify(eventos)

@recepcao_bp.route("/consultas/<int:consulta_id>/status", methods=["POST"])
@login_required
@perfil_requerido("RECEPCIONISTA", "ADMINISTRADOR", "PSICOLOGO")
def atualizar_status_consulta(consulta_id):
    c = Consulta.query.get_or_404(consulta_id)
    novo_status = request.form.get("status")
    nova_data = request.form.get("nova_data")
    nova_hora = request.form.get("nova_hora")

    if nova_data and nova_hora:
        c.data_hora = datetime.strptime(f"{nova_data} {nova_hora}", "%Y-%m-%d %H:%M")
        c.alerta_5dias_enviado = False
        flash("Consulta remarcada com sucesso!", "info")
    if novo_status:
        c.status = novo_status
        flash(f"Status alterado para {novo_status}.", "success")

    db.session.commit()
    return redirect(request.referrer or url_for("recepcao.agenda"))

@recepcao_bp.route("/financeiro")
@login_required
@perfil_requerido("RECEPCIONISTA", "ADMINISTRADOR")
def financeiro():
    status_filtro = request.args.get("status", "")
    query = Pagamento.query.join(Consulta)
    if status_filtro:
        query = query.filter(Pagamento.status == status_filtro)
    pagamentos = query.order_by(Consulta.data_hora.desc()).all()
    return render_template("recepcao/financeiro.html", pagamentos=pagamentos, status_filtro=status_filtro)

@recepcao_bp.route("/pagamentos/<int:pgto_id>/confirmar", methods=["POST"])
@login_required
@perfil_requerido("RECEPCIONISTA", "ADMINISTRADOR")
def confirmar_pagamento(pgto_id):
    pgto = Pagamento.query.get_or_404(pgto_id)
    pgto.status = "PAGO"
    pgto.forma_pagamento = request.form.get("forma_pagamento", pgto.forma_pagamento)
    pgto.data_pagamento = datetime.now()
    db.session.commit()
    flash("Pagamento registrado com sucesso!", "success")
    return redirect(url_for("recepcao.financeiro"))

@recepcao_bp.route("/pagamentos/<int:pgto_id>/recibo")
@login_required
@perfil_requerido("RECEPCIONISTA", "ADMINISTRADOR")
def emitir_recibo(pgto_id):
    pgto = Pagamento.query.get_or_404(pgto_id)
    config = ConfiguracaoClinica.query.first()
    return render_template("recepcao/recibo.html", pgto=pgto, config=config)
