import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, Usuario, ConfiguracaoClinica, Consulta, LogAuditoria, Notificacao

public_bp = Blueprint("public", __name__)

def registrar_log(acao, detalhes=""):
    uid = current_user.id if current_user.is_authenticated else None
    log = LogAuditoria(usuario_id=uid, acao=acao, detalhes=detalhes, ip_origem=request.remote_addr)
    db.session.add(log)
    db.session.commit()

@public_bp.route("/")
def index():
    config = ConfiguracaoClinica.query.first()
    return render_template("public/index.html", config=config)

@public_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirecionar_por_perfil(current_user.perfil)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.check_senha(senha):
            if not usuario.ativo:
                flash("Usuário bloqueado. Contate o Administrador.", "danger")
                return redirect(url_for("public.login"))
            login_user(usuario)
            registrar_log("LOGIN", f"Usuário {usuario.email} ({usuario.perfil}) acessou o sistema.")
            return redirecionar_por_perfil(usuario.perfil)
        else:
            flash("E-mail ou senha inválidos.", "danger")

    return render_template("auth/login.html")

@public_bp.route("/recuperar-senha", methods=["GET", "POST"])
def recuperar_senha():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        nova_senha = request.form.get("nova_senha", "")
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and len(nova_senha) >= 6:
            usuario.set_senha(nova_senha)
            usuario.token_recuperacao = str(uuid.uuid4())
            db.session.commit()
            registrar_log("RECUPERACAO_SENHA", f"Senha redefinida para {email}")
            flash("Senha redefinida com sucesso! Faça login.", "success")
            return redirect(url_for("public.login"))
        flash("E-mail não encontrado ou senha muito curta (mínimo 6 caracteres).", "warning")
    return render_template("auth/recuperar_senha.html")

@public_bp.route("/logout")
@login_required
def logout():
    registrar_log("LOGOUT", f"Usuário {current_user.email} saiu do sistema.")
    logout_user()
    flash("Sessão encerrada com segurança.", "info")
    return redirect(url_for("public.index"))

@public_bp.route("/confirmar-presenca/<token>")
def confirmar_presenca_paciente(token):
    consulta = Consulta.query.filter_by(token_confirmacao=token).first_or_404()
    if consulta.status == "PENDENTE":
        consulta.status = "CONFIRMADA"
        notif = Notificacao(
            usuario_id=consulta.psicologo.usuario_id,
            titulo="Presença Confirmada pelo Paciente",
            mensagem=f"O(a) paciente {consulta.paciente.nome_completo} confirmou presença para {consulta.data_hora.strftime('%d/%m/%Y às %H:%M')}."
        )
        db.session.add(notif)
        db.session.commit()
    return render_template("public/confirmacao_sucesso.html", consulta=consulta)

def redirecionar_por_perfil(perfil):
    if perfil == "ADMINISTRADOR":
        return redirect(url_for("admin.dashboard"))
    elif perfil == "RECEPCIONISTA":
        return redirect(url_for("recepcao.dashboard"))
    elif perfil == "PSICOLOGO":
        return redirect(url_for("psicologo.dashboard"))
    return redirect(url_for("public.index"))
