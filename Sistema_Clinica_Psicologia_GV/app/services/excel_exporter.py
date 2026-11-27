import io
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def gerar_excel_administrativo(pacientes, consultas, pagamentos):
    wb = Workbook()
    
    # Estilos
    header_fill = PatternFill(start_color="0F3460", end_color="0F3460", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    zebra_fill = PatternFill(start_color="F0F4F8", end_color="F0F4F8", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB")
    )

    # ABA 1: Resumo & Financeiro
    ws_fin = wb.active
    ws_fin.title = "Financeiro e Consultas"
    headers_fin = ["ID Consulta", "Data/Hora", "Paciente", "CPF", "Psicólogo", "Status Consulta", "Convênio", "Valor (R$)", "Desconto (R$)", "Valor Final (R$)", "Status Pagamento", "Forma Pagamento"]
    ws_fin.append(headers_fin)
    
    for col_idx in range(1, len(headers_fin) + 1):
        cell = ws_fin.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    for idx, c in enumerate(consultas, start=2):
        pgto = c.pagamento
        valor_final = pgto.valor_final if pgto else (c.valor - c.desconto)
        row_data = [
            c.id,
            c.data_hora.strftime("%d/%m/%Y %H:%M"),
            c.paciente.nome_completo,
            c.paciente.cpf,
            c.psicologo.usuario.nome,
            c.status,
            c.convenio,
            c.valor,
            c.desconto,
            valor_final,
            pgto.status if pgto else "PENDENTE",
            pgto.forma_pagamento if pgto else "-"
        ]
        ws_fin.append(row_data)
        for col_idx in range(1, len(row_data) + 1):
            cell = ws_fin.cell(row=idx, column=col_idx)
            cell.border = thin_border
            if idx % 2 == 0:
                cell.fill = zebra_fill
            if col_idx in (8, 9, 10):
                cell.number_format = 'R$ #,##0.00'

    # Linha de Totais
    last_row = len(consultas) + 2
    ws_fin.cell(row=last_row, column=7, value="TOTAL GERAL:").font = Font(bold=True)
    if len(consultas) > 0:
        ws_fin.cell(row=last_row, column=10, value=f"=SUM(J2:J{last_row-1})").font = Font(bold=True)
        ws_fin.cell(row=last_row, column=10).number_format = 'R$ #,##0.00'

    # ABA 2: Pacientes Cadastrados
    ws_pac = wb.create_sheet(title="Pacientes")
    headers_pac = ["ID", "Nome Completo", "CPF", "Nascimento", "Telefone", "E-mail", "Psicólogo Responsável", "Status", "Data Cadastro"]
    ws_pac.append(headers_pac)
    for col_idx in range(1, len(headers_pac) + 1):
        cell = ws_pac.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = thin_border

    for idx, p in enumerate(pacientes, start=2):
        row_data = [
            p.id,
            p.nome_completo,
            p.cpf,
            p.data_nascimento.strftime("%d/%m/%Y") if p.data_nascimento else "",
            p.telefone,
            p.email or "",
            p.psicologo_responsavel.usuario.nome if p.psicologo_responsavel else "Não vinculado",
            p.status,
            p.data_cadastro.strftime("%d/%m/%Y")
        ]
        ws_pac.append(row_data)
        for col_idx in range(1, len(row_data) + 1):
            cell = ws_pac.cell(row=idx, column=col_idx)
            cell.border = thin_border
            if idx % 2 == 0:
                cell.fill = zebra_fill

    # Ajuste automático de largura das colunas
    for sheet in wb.worksheets:
        sheet.freeze_panes = "A2"
        for col in sheet.columns:
            max_len = max((len(str(cell.value or "")) for cell in col), default=12)
            sheet.column_dimensions[col[0].column_letter].width = min(max_len + 5, 42)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
