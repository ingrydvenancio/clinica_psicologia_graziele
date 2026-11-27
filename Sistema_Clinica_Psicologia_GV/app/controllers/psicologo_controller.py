import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from app.controllers.decorators import perfil_requerido
from app.models import (
    db, Paciente, Consulta, Prontuario, Evolucao,
    DocumentoClinico, Notificacao, LogAuditoria
)
from app.services.document_generator import gerar_arquivos_clinicos

psicologo_bp = Blueprint("psicologo", __name__, url_prefix="/psicologo")

@psicologo_bp.route("/dashboard")
@login_required
@perfil_requerido("PSICOLOGO")
def dashboard():
    psi = current_user.psicologo
    hoje = datetime.now().date()
    inicio_hoje = datetime.combine(hoje, datetime.min.time())
    fim_hoje = datetime.combine(hoje, datetime.max.time())

    consultas_hoje = Consulta.query.filter(
        Consulta.psicologo_id == psi.id,
        Consulta.data_hora >= inicio_hoje,
        Consulta.data_hora <= fim_hoje
    ).order_by(Consulta.data_hora.asc()).all()

    proximas_consultas = Consulta.query.filter(
        Consulta.psicologo_id == psi.id,
        Consulta.data_hora > fim_hoje,
        Consulta.status.in_(["PENDENTE", "CONFIRMADA"])
    ).order_by(Consulta.data_hora.asc()).limit(10).all()

    notificacoes = Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).order_by(Notificacao.criada_em.desc()).all()
    meus_pacientes = Paciente.query.filter_by(psicologo_id=psi.id).all()

    return render_template(
        "psicologo/dashboard.html",
        psi=psi,
        consultas_hoje=consultas_hoje,
        proximas_consultas=proximas_consultas,
        notificacoes=notificacoes,
        meus_pacientes=meus_pacientes
    )

@psicologo_bp.route("/notificacoes/<int:notif_id>/ler", methods=["POST"])
@login_required
@perfil_requerido("PSICOLOGO")
def ler_notificacao(notif_id):
    n = Notificacao.query.filter_by(id=notif_id, usuario_id=current_user.id).first_or_404()
    n.lida = True
    db.session.commit()
    return redirect(url_for("psicologo.dashboard"))

@psicologo_bp.route("/atendimento/<int:consulta_id>", methods=["GET", "POST"])
@login_required
@perfil_requerido("PSICOLOGO")
def atendimento(consulta_id):
    psi = current_user.psicologo
    consulta = Consulta.query.filter_by(id=consulta_id, psicologo_id=psi.id).first_or_404()
    paciente = consulta.paciente

    if consulta.status in ["PENDENTE", "CONFIRMADA"]:
        consulta.status = "EM_ATENDIMENTO"
        db.session.commit()

    prontuario = Prontuario.query.filter_by(paciente_id=paciente.id).first()
    if not prontuario:
        prontuario = Prontuario(paciente_id=paciente.id, psicologo_id=psi.id)
        db.session.add(prontuario)
        db.session.commit()

    if request.method == "POST":
        prontuario.queixa_principal = request.form.get("queixa_principal")
        prontuario.anamnese_geral = request.form.get("anamnese_geral")
        prontuario.plano_terapeutico = request.form.get("plano_terapeutico")
        prontuario.hipotese_diagnostica = request.form.get("hipotese_diagnostica")

        desc_sessao = request.form.get("descricao_sessao", "").strip()
        if desc_sessao:
            ev = Evolucao(
                prontuario_id=prontuario.id,
                consulta_id=consulta.id,
                psicologo_id=psi.id,
                descricao_sessao=desc_sessao,
                observacoes_clinicas=request.form.get("observacoes_clinicas"),
                encaminhamentos=request.form.get("encaminhamentos")
            )
            db.session.add(ev)

        if request.form.get("finalizar_consulta") == "1":
            consulta.status = "CONCLUIDA"

        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="ATUALIZAR_PRONTUARIO",
            detalhes=f"Prontuário/Evolução atualizado para paciente ID {paciente.id}"
        ))
        db.session.commit()
        flash("Evolução e prontuário salvos com sigilo!", "success")
        return redirect(url_for("psicologo.atendimento", consulta_id=consulta.id))

    evolucoes = Evolucao.query.filter_by(prontuario_id=prontuario.id).order_by(Evolucao.data_registro.desc()).all()
    documentos = DocumentoClinico.query.filter_by(paciente_id=paciente.id).order_by(DocumentoClinico.criado_em.desc()).all()
    return render_template(
        "psicologo/atendimento.html",
        consulta=consulta,
        paciente=paciente,
        prontuario=prontuario,
        evolucoes=evolucoes,
        documentos=documentos
    )

@psicologo_bp.route("/relatorios-clinicos", methods=["GET", "POST"])
@login_required
@perfil_requerido("PSICOLOGO")
def relatorios_clinicos():
    psi = current_user.psicologo
    pacientes = Paciente.query.filter_by(psicologo_id=psi.id).order_by(Paciente.nome_completo.asc()).all()
    if not pacientes:
        pacientes = Paciente.query.order_by(Paciente.nome_completo.asc()).all()

    if request.method == "POST":
        paciente_id = int(request.form.get("paciente_id"))
        tipo_documento = request.form.get("tipo_documento")
        formato_download = request.form.get("formato_download", "pdf")
        paciente = Paciente.query.get_or_404(paciente_id)

        dados_form = request.form.to_dict()
        dados_form["paciente_nome"] = paciente.nome_completo

        ultima_consulta = Consulta.query.filter_by(paciente_id=paciente.id).order_by(Consulta.data_hora.desc()).first()
        data_ref = ultima_consulta.data_hora if ultima_consulta else datetime.now()

        logo_path = os.path.join(current_app.root_path, "static", "img", "logo_gv.png")
        base_dir = current_app.config["EXPORT_BASE_DIR"]

        caminho_pdf, caminho_docx = gerar_arquivos_clinicos(
            base_dir=base_dir,
            tipo_documento=tipo_documento,
            dados=dados_form,
            nome_paciente=paciente.nome_completo,
            data_consulta=data_ref,
            logo_path=logo_path
        )

        doc_reg = DocumentoClinico(
            paciente_id=paciente.id,
            psicologo_id=psi.id,
            consulta_id=ultima_consulta.id if ultima_consulta else None,
            tipo_documento=tipo_documento,
            dados_json=json.dumps(dados_form, ensure_ascii=False),
            caminho_pdf=caminho_pdf,
            caminho_docx=caminho_docx
        )
        db.session.add(doc_reg)
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="GERAR_DOCUMENTO_CLINICO",
            detalhes=f"Gerou {tipo_documento} para {paciente.nome_completo} em {os.path.dirname(caminho_pdf)}"
        ))
        db.session.commit()

        arquivo_baixar = caminho_docx if formato_download == "docx" else caminho_pdf
        return send_file(arquivo_baixar, as_attachment=True)

    documentos_recentes = DocumentoClinico.query.filter_by(psicologo_id=psi.id).order_by(DocumentoClinico.criado_em.desc()).limit(20).all()
    return render_template("psicologo/relatorios_clinicos.html", pacientes=pacientes, psi=psi, documentos=documentos_recentes)

@psicologo_bp.route("/documento/<int:doc_id>/baixar/<formato>")
@login_required
@perfil_requerido("PSICOLOGO")
def baixar_documento(doc_id, formato):
    doc = DocumentoClinico.query.filter_by(id=doc_id, psicologo_id=current_user.psicologo.id).first_or_404()
    caminho = doc.caminho_docx if formato == "docx" else doc.caminho_pdf
    return send_file(caminho, as_attachment=True)
