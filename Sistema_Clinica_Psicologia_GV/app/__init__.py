from datetime import datetime, timedelta, date
import uuid
from flask import Flask
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from app.models import (
    db, Usuario, Psicologo, Recepcionista, Administrador,
    ConfiguracaoClinica, Paciente, Consulta, Pagamento
)
from app.controllers.public_controller import public_bp
from app.controllers.admin_controller import admin_bp
from app.controllers.recepcao_controller import recepcao_bp
from app.controllers.psicologo_controller import psicologo_bp
from app.services.notification_scheduler import verificar_alertas_5_dias

login_manager = LoginManager()
login_manager.login_view = "public.login"
login_manager.login_message = "Faça login para acessar esta área restrita."

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def seed_dados_iniciais():
    if not ConfiguracaoClinica.query.first():
        db.session.add(ConfiguracaoClinica())

    if not Usuario.query.filter_by(email="admin@clinica.com").first():
        u_admin = Usuario(nome="Administrador Geral", email="admin@clinica.com", perfil="ADMINISTRADOR")
        u_admin.set_senha("admin123")
        db.session.add(u_admin)
        db.session.flush()
        db.session.add(Administrador(usuario_id=u_admin.id))

    if not Usuario.query.filter_by(email="graziele@clinica.com").first():
        u_psi = Usuario(nome="Dra. Graziele Venancio", email="graziele@clinica.com", perfil="PSICOLOGO")
        u_psi.set_senha("psi123")
        db.session.add(u_psi)
        db.session.flush()
        psi = Psicologo(usuario_id=u_psi.id, crp="CRP 06/123456", especialidade="Neuropsicologia e Psicodiagnóstico")
        db.session.add(psi)
        db.session.flush()

        # Paciente exemplo e consulta daqui a 5 dias corridos para demonstração automática
        pac = Paciente(
            nome_completo="Lucas Mendes Oliveira",
            cpf="123.456.789-00",
            data_nascimento=date(2015, 5, 14),
            telefone="(11) 98888-7777",
            email="responsavel.lucas@exemplo.com",
            psicologo_id=psi.id
        )
        db.session.add(pac)
        db.session.flush()

        dt_5dias = datetime.now() + timedelta(days=5)
        c = Consulta(
            paciente_id=pac.id,
            psicologo_id=psi.id,
            data_hora=dt_5dias.replace(hour=14, minute=0, second=0, microsecond=0),
            valor=180.00,
            token_confirmacao=str(uuid.uuid4())
        )
        db.session.add(c)
        db.session.flush()
        db.session.add(Pagamento(consulta_id=c.id, valor_final=180.00, recibo_numero="REC-2026-00001"))

    if not Usuario.query.filter_by(email="recepcao@clinica.com").first():
        u_rec = Usuario(nome="Atendimento Recepção", email="recepcao@clinica.com", perfil="RECEPCIONISTA")
        u_rec.set_senha("rec123")
        db.session.add(u_rec)
        db.session.flush()
        db.session.add(Recepcionista(usuario_id=u_rec.id))

    db.session.commit()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(recepcao_bp)
    app.register_blueprint(psicologo_bp)

    with app.app_context():
        db.create_all()
        seed_dados_iniciais()

    # Agendador em segundo plano (roda em Windows e Linux) para verificar alertas de 5 dias corridos
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: verificar_alertas_5_dias(app), trigger="interval", minutes=30)
    scheduler.start()
    verificar_alertas_5_dias(app)

    return app
