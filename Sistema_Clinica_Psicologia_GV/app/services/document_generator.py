import os
import re
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Marco", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def _sanitizar_nome(texto):
    texto = re.sub(r'[\\/*?:"<>|]', "", texto).strip()
    return texto.replace(" ", "_")

def obter_pasta_paciente_mes(base_dir, nome_paciente, data_consulta=None):
    """
    Cria e retorna a pasta multiplataforma (Windows/Linux) no formato:
    <base_dir>/<Paciente_Mes_Ano>/
    """
    dt = data_consulta or datetime.now()
    mes_nome = MESES_PT.get(dt.month, str(dt.month))
    nome_pasta = f"{_sanitizar_nome(nome_paciente)}_{mes_nome}_{dt.year}"
    pasta_destino = os.path.join(base_dir, nome_pasta)
    os.makedirs(pasta_destino, exist_ok=True)
    return pasta_destino


def gerar_arquivos_clinicos(base_dir, tipo_documento, dados, nome_paciente, data_consulta=None, logo_path=None):
    """
    Gera simultaneamente o arquivo .docx e .pdf exatamente conforme os modelos anexados
    e salva na pasta <Paciente_Mes_Ano> no explorador de arquivos.
    """
    pasta = obter_pasta_paciente_mes(base_dir, nome_paciente, data_consulta)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefixos = {
        "ANAMNESE_INFANTOJUVENIL": "Anamnese_Infantojuvenil",
        "RELATORIO_SEMANAL": "Relatorio_Semanal_Psicodiagnostico",
        "LAUDO_PSICODIAGNOSTICO": "Laudo_Psicologico_Psicodiagnostico"
    }
    nome_base = f"{prefixos.get(tipo_documento, 'Documento')}_{_sanitizar_nome(nome_paciente)}_{timestamp}"
    caminho_docx = os.path.join(pasta, f"{nome_base}.docx")
    caminho_pdf = os.path.join(pasta, f"{nome_base}.pdf")

    linhas_estruturadas = _montar_estrutura_modelo(tipo_documento, dados)
    _gerar_docx(caminho_docx, tipo_documento, linhas_estruturadas, logo_path)
    _gerar_pdf(caminho_pdf, tipo_documento, linhas_estruturadas, logo_path)

    return caminho_pdf, caminho_docx


def _montar_estrutura_modelo(tipo, d):
    if tipo == "ANAMNESE_INFANTOJUVENIL":
        return [
            ("TITULO", "VIVER DE NEUROPSICOLOGIA - ANAMNESE INFANTOJUVENIL"),
            ("CAMPO", f"Responsável participante: {d.get('responsavel_participante', '')}"),
            ("SECAO", "1. DADOS DO PACIENTE"),
            ("CAMPO", f"Nome: {d.get('paciente_nome', '')}"),
            ("CAMPO", f"Data de nascimento: {d.get('data_nascimento', '')}   |   Naturalidade: {d.get('naturalidade', '')}"),
            ("CAMPO", f"Com quem reside: {d.get('com_quem_reside', '')}"),
            ("CAMPO", f"Caso não seja com nenhum dos pais, qual o motivo: {d.get('motivo_nao_pais', '')}"),
            ("SECAO", "2. DADOS DE IDENTIFICAÇÃO DOS PAIS"),
            ("CAMPO", f"Nome do Pai: {d.get('pai_nome', '')}   |   Idade: {d.get('pai_idade', '')}   |   Estado Civil: {d.get('pai_estado_civil', '')}"),
            ("CAMPO", f"Grau de Instrução: {d.get('pai_instrucao', '')}   |   Profissão: {d.get('pai_profissao', '')}"),
            ("CAMPO", f"Telefone: {d.get('pai_telefone', '')}   |   Onde reside / Endereço: {d.get('pai_endereco', '')}"),
            ("CAMPO", f"Histórico de doença mental familiar, vícios e/ou outras doenças (Pai): {d.get('pai_historico_saude', '')}"),
            ("CAMPO", f"Nome da Mãe: {d.get('mae_nome', '')}   |   Idade: {d.get('mae_idade', '')}   |   Estado Civil: {d.get('mae_estado_civil', '')}"),
            ("CAMPO", f"Grau de Instrução: {d.get('mae_instrucao', '')}   |   Profissão: {d.get('mae_profissao', '')}"),
            ("CAMPO", f"Telefone: {d.get('mae_telefone', '')}   |   Endereço: {d.get('mae_endereco', '')}"),
            ("CAMPO", f"Histórico de doença mental familiar, vícios e/ou outras doenças (Mãe): {d.get('mae_historico_saude', '')}"),
            ("SECAO", "3. DADOS DO ENCAMINHAMENTO"),
            ("CAMPO", f"Encaminhamento: {d.get('encaminhamento', '')}   |   Data: {d.get('data_entrevista', '')}"),
            ("CAMPO", f"Queixa principal: {d.get('queixa_principal', '')}"),
            ("CAMPO", f"Possui algum diagnóstico: {d.get('possui_diagnostico', '')}"),
            ("SECAO", "4. CONHECENDO MELHOR A CRIANÇA/ADOLESCENTE"),
            ("SUBSECAO", "• Concepção"),
            ("CAMPO", f"A gravidez foi desejada por ambos os pais? {d.get('gravidez_desejada', '')}   |   Fez pré-natal? {d.get('pre_natal', '')}"),
            ("CAMPO", f"Tipo de nascimento/parto: {d.get('tipo_parto', '')}   |   Local de nascimento: {d.get('local_nascimento', '')}"),
            ("CAMPO", f"Semanas gestacionais: {d.get('semanas_gestacionais', '')}   |   Medicações durante a gestação: {d.get('medicacoes_gestacao', '')}"),
            ("CAMPO", f"Uso de cigarro, álcool e outras drogas durante a gestação? {d.get('drogas_gestacao', '')} | Tipo/Frequência: {d.get('drogas_tipo_freq', '')}"),
            ("CAMPO", f"Sofreu queda, susto ou doenças na gravidez? {d.get('intercorrencias_gravidez', '')}"),
            ("CAMPO", f"Informações sobre período gestacional: {d.get('info_gestacional', '')}"),
            ("SUBSECAO", "• Histórico do desenvolvimento"),
            ("CAMPO", f"Apgar: {d.get('apgar', '')}   |   Amamentação: {d.get('amamentacao', '')}   |   Tempo: {d.get('tempo_amamentacao', '')}"),
            ("CAMPO", f"Controle cabeça: {d.get('controle_cabeca', '')} | Sentou: {d.get('sentou', '')} | Engatinhou: {d.get('engatinhou', '')} | Andou: {d.get('andou', '')}"),
            ("CAMPO", f"Balbuciou: {d.get('balbuciou', '')} | Falou: {d.get('falou', '')} | Amarrar sapatos: {d.get('amarrar_sapatos', '')} | Vestir-se: {d.get('vestir_sozinho', '')}"),
            ("CAMPO", f"Comer sozinho(a): {d.get('comer_sozinho', '')} | Controle urina (diurno/noturno): {d.get('controle_urina', '')} | Controle fezes: {d.get('controle_fezes', '')}"),
            ("CAMPO", f"Uso de chupeta: {d.get('uso_chupeta', '')} | Uso de fraldas: {d.get('uso_fraldas', '')} | Dorme sozinho? {d.get('dorme_sozinho', '')}"),
            ("CAMPO", f"Ranger dos dentes: {d.get('ranger_dentes', '')} | Rói unhas? {d.get('roi_unhas', '')}"),
            ("CAMPO", f"Rotina da criança e mudanças: {d.get('rotina_crianca', '')} | Dificuldade adaptação: {d.get('dificuldade_adaptacao', '')}"),
            ("CAMPO", f"Como é o brincar (sozinho/amigos): {d.get('como_brinca', '')}"),
            ("CAMPO", f"O que deixa nervoso(a) e por quê: {d.get('o_que_deixa_nervoso', '')} | Medos: {d.get('medos', '')}"),
            ("SUBSECAO", "• Histórico Médico"),
            ("CAMPO", f"Estado atual de saúde: {d.get('estado_saude', '')} | Sono, alimentação e digestão: {d.get('sono_alimentacao', '')}"),
            ("CAMPO", f"Febre alta/convulsões: {d.get('febre_convulsoes', '')} | Internações: {d.get('internacoes', '')} | Cirurgias: {d.get('cirurgias', '')}"),
            ("CAMPO", f"Doenças infecto-contagiosas, desmaios ou quedas com batida na cabeça: {d.get('doencas_quedas', '')}"),
            ("CAMPO", f"Já fez terapia? {d.get('fez_terapia', '')} | Faz uso de medicamento? {d.get('medicamento_atual', '')}"),
            ("SUBSECAO", "• Sexualidade e Outras Informações"),
            ("CAMPO", f"Educação sexual / curiosidade / questões: {d.get('sexualidade_info', '')}"),
            ("CAMPO", f"Tempo de tela e conteúdo: {d.get('tempo_tela', '')} | Atividades favoritas: {d.get('atividades_favoritas', '')}"),
            ("CAMPO", f"Problemas com limites (lei): {d.get('problemas_limites', '')} | Quem aplica disciplina: {d.get('quem_disciplina', '')}"),
            ("CAMPO", f"Estratégias bem-sucedidas: {d.get('estrategias_sucesso', '')}"),
            ("CAMPO", f"Habilidades mais desenvolvidas e características positivas: {d.get('habilidades_positivas', '')}"),
            ("SUBSECAO", "• Dificuldades Específicas"),
            ("CAMPO", f"Articulação na fala: {d.get('dif_articulacao', '')} | Encontrar palavras: {d.get('dif_palavras', '')} | Fala infantilizada: {d.get('fala_infantilizada', '')} | Fala errado: {d.get('fala_errado', '')}"),
            ("CAMPO", f"Pensamento lentificado: {d.get('pensamento_lentificado', '')} | Esquece coisas: {d.get('esquece_coisas', '')} | Distrai-se facilmente: {d.get('distrai_facilmente', '')}"),
            ("CAMPO", f"Esquece instruções: {d.get('esquece_instrucoes', '')} | Perde pertences: {d.get('perde_pertences', '')} | Planejar tarefas: {d.get('dif_planejar', '')}"),
            ("CAMPO", f"Não prevê consequências: {d.get('nao_preve_consequencias', '')} | Dinheiro/matemática: {d.get('dif_matematica', '')} | Pouca noção temporal: {d.get('pouca_nocao_temporal', '')}"),
            ("CAMPO", f"Outras dificuldades no dia a dia: {d.get('outras_dificuldades', '')}"),
            ("SUBSECAO", "• Desenvolvimento Escolar"),
            ("CAMPO", f"Local onde estuda: {d.get('escola_local', '')} | Série: {d.get('escola_serie', '')} | Tipo: {d.get('escola_tipo', '')} | Período: {d.get('escola_periodo', '')}"),
            ("CAMPO", f"Início na escola: {d.get('inicio_escola', '')} | Idade leitura/escrita: {d.get('idade_leitura_escrita', '')}"),
            ("CAMPO", f"Queixas escolares e dificuldades em matérias: {d.get('queixas_escolares', '')}"),
            ("CAMPO", f"Relacionamento colegas/professores: {d.get('relacionamento_escolar', '')} | Reprovação escolar: {d.get('reprovacao_escolar', '')}"),
        ]

    elif tipo == "RELATORIO_SEMANAL":
        return [
            ("TITULO", f"CAMPUS {d.get('campus', 'CLINICA GRAZIELE VENANCIO')} - RELATÓRIO SEMANAL PSICODIAGNÓSTICO"),
            ("CAMPO", f"Curso / Área: {d.get('curso', 'Psicologia / Neuropsicologia')}   |   Semestre/Período: {d.get('semestre', '')}"),
            ("CAMPO", "Estágio Supervisionado Específico em Psicodiagnóstico / Atendimento Clínico"),
            ("CAMPO", f"Profissional / Estagiário(s): {d.get('estagiarios', '')}"),
            ("CAMPO", f"Psicólogo(a) / Professor(a) Orientador(a): {d.get('orientador', '')}   |   CRP: {d.get('crp_orientador', '')}"),
            ("SECAO", "IDENTIFICAÇÃO DO ATENDIMENTO"),
            ("CAMPO", f"Usuário(a) / Paciente: {d.get('paciente_nome', '')}   |   Sexo: {d.get('sexo', '')}   |   Idade: {d.get('idade', '')}"),
            ("CAMPO", f"Data do Atendimento: {d.get('data_atendimento', '')}   |   Sala: {d.get('sala', '')}   |   Dia Semana: {d.get('dia_semana', '')}   |   Hora: {d.get('hora', '')}"),
            ("CAMPO", f"Sessão Nº: {d.get('numero_sessao', '1ª SESSÃO')}"),
            ("SECAO", "I – Relato de Avaliação (Etapa conduzida da avaliação)"),
            ("CAMPO", d.get("relato_avaliacao", "")),
            ("SECAO", "II – Observações comportamentais"),
            ("CAMPO", d.get("observacoes_comportamentais", "")),
            ("SECAO", "III – Correção dos instrumentos"),
            ("CAMPO", d.get("correcao_instrumentos", "")),
            ("SECAO", "IV – Fundamentação Teórica"),
            ("CAMPO", d.get("fundamentacao_teorica", "")),
            ("SECAO", "V – Orientações após a supervisão"),
            ("CAMPO", d.get("orientacoes_supervisao", "")),
            ("ASSINATURA", f"Responsável Técnico / Estagiário(a): {d.get('estagiarios', '')}  |  RGM/Reg: {d.get('rgm', '')}"),
            ("ASSINATURA", f"Psicólogo(a) Responsável / Orientador(a): {d.get('orientador', '')}  |  CRP: {d.get('crp_orientador', '')}"),
        ]

    else:  # LAUDO_PSICODIAGNOSTICO
        return [
            ("TITULO", "LAUDO PSICOLÓGICO (Resolução CFP nº 06/2019)"),
            ("SECAO", "1. IDENTIFICAÇÃO"),
            ("CAMPO", "I - Título: Laudo Psicológico."),
            ("CAMPO", f"II - Pessoa atendida: {d.get('paciente_nome', '')}"),
            ("CAMPO", f"III - Solicitante: {d.get('solicitante', '')}"),
            ("CAMPO", f"IV - Finalidade: {d.get('finalidade', '')} (Prontuário nº {d.get('numero_prontuario', '')})"),
            ("CAMPO", f"V - Autores: {d.get('autores', '')} - Psicólogo(a) Responsável: {d.get('psicologo_responsavel', '')} (CRP: {d.get('crp', '')})"),
            ("SECAO", "2. DESCRIÇÃO DA DEMANDA"),
            ("CAMPO", d.get("descricao_demanda", "")),
            ("SECAO", "3. PROCEDIMENTO"),
            ("CAMPO", f"Período e frequência: {d.get('periodo_atendimentos', '')}"),
            ("CAMPO", d.get("procedimento_tecnico", "")),
            ("SECAO", "4. ANÁLISE"),
            ("CAMPO", d.get("analise_clinica", "")),
            ("SECAO", "5. CONCLUSÃO"),
            ("CAMPO", d.get("conclusao_encaminhamentos", "")),
            ("CAMPO", "Este laudo possui caráter sigiloso (Resolução CFP 06/2019). Prazo de validade: 8 (oito) meses."),
            ("SECAO", "REFERÊNCIAS BIBLIOGRÁFICAS (ABNT)"),
            ("CAMPO", d.get("referencias_bibliograficas", "")),
            ("ASSINATURA", f"Local e Data: {d.get('local_data', '')}"),
            ("ASSINATURA", f"Psicólogo(a): {d.get('psicologo_responsavel', '')} - CRP: {d.get('crp', '')}"),
        ]


def _gerar_docx(caminho_docx, tipo_documento, linhas, logo_path=None):
    doc = Document()
    if logo_path and os.path.exists(logo_path):
        try:
            p_logo = doc.add_paragraph()
            p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_logo = p_logo.add_run()
            run_logo.add_picture(logo_path, width=Inches(1.5))
        except Exception:
            pass

    for tipo_linha, texto in linhas:
        p = doc.add_paragraph()
        if tipo_linha == "TITULO":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(texto)
            r.bold = True
            r.font.size = Pt(14)
            r.font.color.rgb = RGBColor(15, 52, 96)
        elif tipo_linha == "SECAO":
            r = p.add_run(texto)
            r.bold = True
            r.font.size = Pt(11)
            r.font.color.rgb = RGBColor(22, 78, 135)
        elif tipo_linha == "SUBSECAO":
            r = p.add_run(texto)
            r.bold = True
            r.font.size = Pt(10.5)
        elif tipo_linha == "ASSINATURA":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_linha = p.add_run("_________________________________________")
            r_linha.font.size = Pt(10)
            p_ass = doc.add_paragraph()
            p_ass.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p_ass.add_run(texto)
            r.font.size = Pt(10)
        else:
            r = p.add_run(texto)
            r.font.size = Pt(10)

    doc.save(caminho_docx)


def _gerar_pdf(caminho_pdf, tipo_documento, linhas, logo_path=None):
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    largura, altura = A4
    margem_esq = 45
    margem_dir = largura - 45
    largura_util = margem_dir - margem_esq
    y = altura - 45

    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, (largura - 90) / 2, y - 55, width=90, height=55, preserveAspectRatio=True, mask='auto')
            y -= 68
        except Exception:
            pass

    for tipo_linha, texto in linhas:
        if y < 65:
            c.showPage()
            y = altura - 50

        if tipo_linha == "TITULO":
            c.setFont("Helvetica-Bold", 13)
            c.setFillColor(colors.HexColor("#0F3460"))
            wrapped = simpleSplit(texto, "Helvetica-Bold", 13, largura_util)
            for w in wrapped:
                c.drawCentredString(largura / 2, y, w)
                y -= 18
            y -= 6
        elif tipo_linha == "SECAO":
            y -= 6
            c.setFont("Helvetica-Bold", 10.5)
            c.setFillColor(colors.HexColor("#164E87"))
            c.drawString(margem_esq, y, texto)
            y -= 15
        elif tipo_linha == "SUBSECAO":
            y -= 3
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.black)
            c.drawString(margem_esq, y, texto)
            y -= 14
        elif tipo_linha == "ASSINATURA":
            y -= 14
            c.setFont("Helvetica", 9.5)
            c.setFillColor(colors.black)
            c.drawCentredString(largura / 2, y, "_________________________________________________")
            y -= 13
            c.drawCentredString(largura / 2, y, texto)
            y -= 16
        else:
            c.setFont("Helvetica", 9.5)
            c.setFillColor(colors.black)
            for paragrafo in texto.split("\n"):
                wrapped = simpleSplit(paragrafo or " ", "Helvetica", 9.5, largura_util)
                for w in wrapped:
                    if y < 60:
                        c.showPage()
                        y = altura - 50
                        c.setFont("Helvetica", 9.5)
                    c.drawString(margem_esq, y, w)
                    y -= 13

    c.save()