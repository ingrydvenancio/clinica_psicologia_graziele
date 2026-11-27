from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.Enum("ADMINISTRADOR", "RECEPCIONISTA", "PSICOLOGO", name="perfil_enum"), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    token_recuperacao = db.Column(db.String(100), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.now)

    psicologo = db.relationship("Psicologo", backref="usuario", uselist=False, cascade="all, delete-orphan")
    recepcionista = db.relationship("Recepcionista", backref="usuario", uselist=False, cascade="all, delete-orphan")
    administrador = db.relationship("Administrador", backref="usuario", uselist=False, cascade="all, delete-orphan")
    notificacoes = db.relationship("Notificacao", backref="usuario", lazy=True, cascade="all, delete-orphan")

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_active(self):
        return self.ativo


class Psicologo(db.Model):
    __tablename__ = "psicologos"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), unique=True, nullable=False)
    crp = db.Column(db.String(30), unique=True, nullable=False)
    especialidade = db.Column(db.String(120), default="Neuropsicologia e Psicologia Clínica")
    telefone = db.Column(db.String(25))
    biografia = db.Column(db.Text)

    pacientes = db.relationship("Paciente", backref="psicologo_responsavel", lazy=True)
    consultas = db.relationship("Consulta", backref="psicologo", lazy=True)


class Recepcionista(db.Model):
    __tablename__ = "recepcionistas"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), unique=True, nullable=False)
    turno = db.Column(db.String(50), default="Integral")
    telefone = db.Column(db.String(25))


class Administrador(db.Model):
    __tablename__ = "administradores"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), unique=True, nullable=False)
    cargo = db.Column(db.String(80), default="Diretor(a) Clínico(a)")


class ConfiguracaoClinica(db.Model):
    __tablename__ = "configuracoes_clinica"
    id = db.Column(db.Integer, primary_key=True)
    nome_clinica = db.Column(db.String(150), default="Clínica de Psicologia Graziele Venancio")
    cnpj = db.Column(db.String(25), default="00.000.000/0001-00")
    endereco = db.Column(db.String(255), default="Av. Paulista, 1000 - Sala 42, São Paulo - SP")
    telefone = db.Column(db.String(30), default="(11) 99999-0000")
    email_contato = db.Column(db.String(150), default="contato@grazielevenancio.com.br")
    valor_consulta_padrao = db.Column(db.Float, default=180.00)
    quem_somos_titulo = db.Column(db.String(150), default="Quem Somos Nós")
    quem_somos_texto = db.Column(
        db.Text,
        default="A Clínica de Psicologia Graziele Venancio oferece atendimento humanizado, ético e baseado em evidências científicas em Neuropsicologia, Psicodiagnóstico e Psicoterapia Infantojuvenil e Adulto."
    )
    especialista_nome = db.Column(db.String(150), default="Dra. Graziele Venancio")
    especialista_crp = db.Column(db.String(40), default="CRP 06/123456")
    especialista_formacao = db.Column(
        db.Text,
        default="Psicóloga Clínica e Especialista em Neuropsicologia e Avaliação Psicológica. Atendimento focado no desenvolvimento cognitivo, emocional e comportamental."
    )


class Paciente(db.Model):
    __tablename__ = "pacientes"
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    telefone = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(150))
    endereco = db.Column(db.String(255))
    contato_emergencia = db.Column(db.String(150))
    psicologo_id = db.Column(db.Integer, db.ForeignKey("psicologos.id"), nullable=True)
    observacoes_admin = db.Column(db.Text)
    status = db.Column(db.Enum("ATIVO", "INATIVO", name="status_paciente_enum"), default="ATIVO")
    data_cadastro = db.Column(db.DateTime, default=datetime.now)

    consultas = db.relationship("Consulta", backref="paciente", lazy=True, cascade="all, delete-orphan")
    prontuario = db.relationship("Prontuario", backref="paciente", uselist=False, cascade="all, delete-orphan")
    documentos = db.relationship("DocumentoClinico", backref="paciente", lazy=True, cascade="all, delete-orphan")


class Consulta(db.Model):
    __tablename__ = "consultas"
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    psicologo_id = db.Column(db.Integer, db.ForeignKey("psicologos.id"), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    duracao_minutos = db.Column(db.Integer, default=50)
    sala = db.Column(db.String(40), default="Sala 01")
    status = db.Column(
        db.Enum("PENDENTE", "CONFIRMADA", "EM_ATENDIMENTO", "CONCLUIDA", "CANCELADA", "FALTA", name="status_consulta_enum"),
        default="PENDENTE"
    )
    valor = db.Column(db.Float, default=180.00)
    desconto = db.Column(db.Float, default=0.00)
    convenio = db.Column(db.String(80), default="Particular")
    alerta_5dias_enviado = db.Column(db.Boolean, default=False)
    token_confirmacao = db.Column(db.String(100), unique=True)
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.now)

    pagamento = db.relationship("Pagamento", backref="consulta", uselist=False, cascade="all, delete-orphan")


class Pagamento(db.Model):
    __tablename__ = "pagamentos"
    id = db.Column(db.Integer, primary_key=True)
    consulta_id = db.Column(db.Integer, db.ForeignKey("consultas.id"), unique=True, nullable=False)
    valor_final = db.Column(db.Float, nullable=False)
    forma_pagamento = db.Column(
        db.Enum("PIX", "DINHEIRO", "CARTAO_CREDITO", "CARTAO_DEBITO", "TRANSFERENCIA", "CONVENIO", name="forma_pgto_enum"),
        default="PIX"
    )
    status = db.Column(db.Enum("PENDENTE", "PAGO", "ISENTO", name="status_pgto_enum"), default="PENDENTE")
    data_pagamento = db.Column(db.DateTime, nullable=True)
    recibo_numero = db.Column(db.String(50))


class Prontuario(db.Model):
    __tablename__ = "prontuarios"
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), unique=True, nullable=False)
    psicologo_id = db.Column(db.Integer, db.ForeignKey("psicologos.id"), nullable=False)
    queixa_principal = db.Column(db.Text)
    anamnese_geral = db.Column(db.Text)
    plano_terapeutico = db.Column(db.Text)
    hipotese_diagnostica = db.Column(db.Text)
    atualizado_em = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    evolucoes = db.relationship("Evolucao", backref="prontuario", lazy=True, cascade="all, delete-orphan")


class Evolucao(db.Model):
    __tablename__ = "evolucoes"
    id = db.Column(db.Integer, primary_key=True)
    prontuario_id = db.Column(db.Integer, db.ForeignKey("prontuarios.id"), nullable=False)
    consulta_id = db.Column(db.Integer, db.ForeignKey("consultas.id"), nullable=True)
    psicologo_id = db.Column(db.Integer, db.ForeignKey("psicologos.id"), nullable=False)
    data_registro = db.Column(db.DateTime, default=datetime.now)
    descricao_sessao = db.Column(db.Text, nullable=False)
    observacoes_clinicas = db.Column(db.Text)
    encaminhamentos = db.Column(db.Text)


class DocumentoClinico(db.Model):
    __tablename__ = "documentos_clinicos"
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    psicologo_id = db.Column(db.Integer, db.ForeignKey("psicologos.id"), nullable=False)
    consulta_id = db.Column(db.Integer, db.ForeignKey("consultas.id"), nullable=True)
    tipo_documento = db.Column(
        db.Enum("ANAMNESE_INFANTOJUVENIL", "RELATORIO_SEMANAL", "LAUDO_PSICODIAGNOSTICO", name="tipo_doc_enum"),
        nullable=False
    )
    dados_json = db.Column(db.Text, nullable=False)
    caminho_pdf = db.Column(db.String(500))
    caminho_docx = db.Column(db.String(500))
    criado_em = db.Column(db.DateTime, default=datetime.now)


class Notificacao(db.Model):
    __tablename__ = "notificacoes"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    lida = db.Column(db.Boolean, default=False)
    criada_em = db.Column(db.DateTime, default=datetime.now)


class LogAuditoria(db.Model):
    __tablename__ = "logs_auditoria"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    acao = db.Column(db.String(150), nullable=False)
    detalhes = db.Column(db.Text)
    ip_origem = db.Column(db.String(45))
    data_hora = db.Column(db.DateTime, default=datetime.now)
