-- Script SQL / MySQL Completo - Clínica de Psicologia Graziele Venancio
CREATE DATABASE IF NOT EXISTS clinica_psicologia_gv CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE clinica_psicologia_gv;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    perfil ENUM('ADMINISTRADOR', 'RECEPCIONISTA', 'PSICOLOGO') NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    token_recuperacao VARCHAR(100) NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS psicologos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE,
    crp VARCHAR(30) NOT NULL UNIQUE,
    especialidade VARCHAR(120) DEFAULT 'Neuropsicologia e Psicologia Clínica',
    telefone VARCHAR(25),
    biografia TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recepcionistas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE,
    turno VARCHAR(50) DEFAULT 'Integral',
    telefone VARCHAR(25),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS administradores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE,
    cargo VARCHAR(80) DEFAULT 'Diretor(a) Administrativo(a)',
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS configuracoes_clinica (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_clinica VARCHAR(150) NOT NULL DEFAULT 'Clínica de Psicologia Graziele Venancio',
    cnpj VARCHAR(25) DEFAULT '00.000.000/0001-00',
    endereco VARCHAR(255) DEFAULT 'Av. Paulista, 1000 - Sala 42 - São Paulo/SP',
    telefone VARCHAR(30) DEFAULT '(11) 99999-0000',
    email_contato VARCHAR(150) DEFAULT 'contato@grazielevenancio.com.br',
    valor_consulta_padrao DECIMAL(10,2) DEFAULT 180.00,
    quem_somos_titulo VARCHAR(150) DEFAULT 'Quem Somos Nós',
    quem_somos_texto TEXT,
    especialista_nome VARCHAR(150) DEFAULT 'Dra. Graziele Venancio',
    especialista_crp VARCHAR(40) DEFAULT 'CRP 06/000000',
    especialista_formacao TEXT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS pacientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_completo VARCHAR(150) NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    data_nascimento DATE NOT NULL,
    telefone VARCHAR(25) NOT NULL,
    email VARCHAR(150),
    endereco VARCHAR(255),
    contato_emergencia VARCHAR(150),
    psicologo_id INT,
    observacoes_admin TEXT,
    status ENUM('ATIVO', 'INATIVO') DEFAULT 'ATIVO',
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (psicologo_id) REFERENCES psicologos(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS consultas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NOT NULL,
    psicologo_id INT NOT NULL,
    data_hora DATETIME NOT NULL,
    duracao_minutos INT DEFAULT 50,
    sala VARCHAR(40) DEFAULT 'Sala 01',
    status ENUM('PENDENTE', 'CONFIRMADA', 'EM_ATENDIMENTO', 'CONCLUIDA', 'CANCELADA', 'FALTA') DEFAULT 'PENDENTE',
    valor DECIMAL(10,2) NOT NULL DEFAULT 180.00,
    desconto DECIMAL(10,2) DEFAULT 0.00,
    convenio VARCHAR(80) DEFAULT 'Particular',
    alerta_5dias_enviado BOOLEAN DEFAULT FALSE,
    token_confirmacao VARCHAR(100) UNIQUE,
    observacoes TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
    FOREIGN KEY (psicologo_id) REFERENCES psicologos(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS pagamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    consulta_id INT NOT NULL UNIQUE,
    valor_final DECIMAL(10,2) NOT NULL,
    forma_pagamento ENUM('PIX', 'DINHEIRO', 'CARTAO_CREDITO', 'CARTAO_DEBITO', 'TRANSFERENCIA', 'CONVENIO') DEFAULT 'PIX',
    status ENUM('PENDENTE', 'PAGO', 'ISENTO') DEFAULT 'PENDENTE',
    data_pagamento DATETIME NULL,
    recibo_numero VARCHAR(50),
    FOREIGN KEY (consulta_id) REFERENCES consultas(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS prontuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NOT NULL UNIQUE,
    psicologo_id INT NOT NULL,
    queixa_principal TEXT,
    anamnese_geral TEXT,
    plano_terapeutico TEXT,
    hipotese_diagnostica TEXT,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
    FOREIGN KEY (psicologo_id) REFERENCES psicologos(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS evolucoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prontuario_id INT NOT NULL,
    consulta_id INT NULL,
    psicologo_id INT NOT NULL,
    data_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    descricao_sessao TEXT NOT NULL,
    observacoes_clinicas TEXT,
    encaminhamentos TEXT,
    FOREIGN KEY (prontuario_id) REFERENCES prontuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (consulta_id) REFERENCES consultas(id) ON DELETE SET NULL,
    FOREIGN KEY (psicologo_id) REFERENCES psicologos(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS documentos_clinicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NOT NULL,
    psicologo_id INT NOT NULL,
    consulta_id INT NULL,
    tipo_documento ENUM('ANAMNESE_INFANTOJUVENIL', 'RELATORIO_SEMANAL', 'LAUDO_PSICODIAGNOSTICO') NOT NULL,
    dados_json LONGTEXT NOT NULL,
    caminho_pdf VARCHAR(500),
    caminho_docx VARCHAR(500),
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
    FOREIGN KEY (psicologo_id) REFERENCES psicologos(id) ON DELETE CASCADE,
    FOREIGN KEY (consulta_id) REFERENCES consultas(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notificacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    mensagem TEXT NOT NULL,
    lida BOOLEAN DEFAULT FALSE,
    criada_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS logs_auditoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL,
    acao VARCHAR(150) NOT NULL,
    detalhes TEXT,
    ip_origem VARCHAR(45),
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;
