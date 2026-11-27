import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from flask import current_app
from app.models import db, Consulta, Notificacao

def enviar_email_confirmacao(destinatario, nome_paciente, nome_psicologo, data_hora, link_confirmacao):
    mail_user = current_app.config.get("MAIL_USERNAME")
    mail_pass = current_app.config.get("MAIL_PASSWORD")
    mail_server = current_app.config.get("MAIL_SERVER")
    mail_port = current_app.config.get("MAIL_PORT")

    assunto = f"Lembrete de Consulta (Faltam 5 dias) - Clínica Graziele Venancio"
    corpo_html = f"""
    <div style="font-family: Arial, sans-serif; color: #1e293b; max-width: 600px; margin: auto; border: 1px solid #cbd5e1; border-radius: 8px; padding: 24px;">
        <h2 style="color: #0F3460;">Olá, {nome_paciente}!</h2>
        <p>Faltam exatamente <strong>5 dias corridos</strong> para a sua consulta psicológica.</p>
        <p><strong>Profissional:</strong> {nome_psicologo}<br>
           <strong>Data e Horário:</strong> {data_hora.strftime('%d/%m/%Y às %H:%M')}</p>
        <p>Por favor, confirme sua presença clicando no botão abaixo:</p>
        <p style="text-align: center; margin: 28px 0;">
            <a href="{link_confirmacao}" style="background-color: #0F3460; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                Confirmar Presença na Consulta
            </a>
        </p>
        <p style="font-size: 12px; color: #64748b;">Caso precise remarcar, entre em contato com nossa recepção com antecedência.</p>
    </div>
    """

    if not mail_user or not mail_pass:
        print(f"[SIMULAÇÃO SMTP - 5 DIAS] Para: {destinatario} | Link: {link_confirmacao}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = mail_user
        msg["To"] = destinatario
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        with smtplib.SMTP(mail_server, mail_port) as server:
            server.starttls()
            server.login(mail_user, mail_pass)
            server.sendmail(mail_user, destinatario, msg.as_string())
        return True
    except Exception as e:
        print(f"[ERRO SMTP]: {e}")
        return False


def verificar_alertas_5_dias(app, base_url="http://127.0.0.1:5000"):
    """
    Verifica consultas agendadas que ocorrerão em exatamente 5 dias corridos:
    1) Envia e-mail para o paciente com link de confirmação de presença.
    2) Cria notificação no calendário / painel do Doutor Especialista.
    """
    with app.app_context():
        hoje = datetime.now().date()
        data_alvo = hoje + timedelta(days=5)
        inicio_dia = datetime.combine(data_alvo, datetime.min.time())
        fim_dia = datetime.combine(data_alvo, datetime.max.time())

        consultas_alvo = Consulta.query.filter(
            Consulta.data_hora >= inicio_dia,
            Consulta.data_hora <= fim_dia,
            Consulta.status.in_(["PENDENTE", "CONFIRMADA"]),
            Consulta.alerta_5dias_enviado == False
        ).all()

        for c in consultas_alvo:
            paciente = c.paciente
            psicologo = c.psicologo
            link = f"{base_url}/confirmar-presenca/{c.token_confirmacao}"

            # 1. Envia e-mail ao paciente
            if paciente.email:
                enviar_email_confirmacao(
                    paciente.email,
                    paciente.nome_completo,
                    psicologo.usuario.nome,
                    c.data_hora,
                    link
                )

            # 2. Cria notificação no calendário do Doutor Especialista
            notif = Notificacao(
                usuario_id=psicologo.usuario_id,
                titulo="Lembrete de Consulta (5 dias corridos)",
                mensagem=(
                    f"Faltam 5 dias corridos para a consulta com {paciente.nome_completo} "
                    f"em {c.data_hora.strftime('%d/%m/%Y às %H:%M')} ({c.sala}). "
                    f"E-mail de confirmação enviado ao paciente."
                )
            )
            db.session.add(notif)
            c.alerta_5dias_enviado = True

        if consultas_alvo:
            db.session.commit()
