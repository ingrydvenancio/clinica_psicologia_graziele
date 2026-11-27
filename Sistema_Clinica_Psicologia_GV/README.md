# Sistema de Gestão — Clínica de Psicologia Graziele Venancio

Sistema web completo (MVC + MPA) desenvolvido em **Python + Flask**, **MySQL / SQLAlchemy**, **HTML5, CSS3, Bootstrap 5 e JavaScript (FullCalendar)**, compatível com **Windows e Linux**.

## Funcionalidades Principais
1. **Homepage Institucional**: Exibe a logomarca **Graziele Venancio Psicóloga**, foto da especialista na seção **"Quem Somos Nós"** e dados obrigatórios editáveis pelo Administrador.
2. **Controle de Acesso (3 Perfis)**: Administrador, Recepcionista e Psicólogo com hash de senha (`Werkzeug`) e logs de auditoria.
3. **Calendário & Alerta Automático de 5 Dias Corridos**: Quando faltam 5 dias corridos para a consulta, o sistema envia automaticamente um e-mail com link de confirmação de presença ao paciente e gera uma notificação no calendário do Doutor Especialista.
4. **Área do Especialista & Modelos Clínicos Exatos**:
   - **Anamnese Infantojuvenil (Viver de Neuropsicologia)**
   - **Relatório Semanal Psicodiagnóstico**
   - **Laudo Psicológico (Resolução CFP 06/2019)**
   - Ao salvar, baixa automaticamente em **PDF** ou **.DOCX** e organiza no Explorador de Arquivos dentro da pasta `documentos_gerados/<Nome_Paciente>_<Mes>_<Ano>/`.
5. **Painel Administrativo**: Exportação gerencial completa em **Excel (.xlsx)** com abas formatadas e fórmulas.

## Como Executar (Windows e Linux)
```bash
# 1. Criar e ativar ambiente virtual
python -m venv venv
# Windows: venv\Scripts\activate
# Linux:   source venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar o banco MySQL
mysql -u root -p < database.sql
cp .env.example .env  # Edite DB_USER, DB_PASSWORD e MAIL_USERNAME

# 4. Iniciar o sistema
python run.py
```
*(Dica: Para testar imediatamente sem servidor MySQL instalado, defina `USE_SQLITE_FALLBACK=1` no `.env`.)*
