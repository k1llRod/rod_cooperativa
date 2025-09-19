from odoo import models, fields, _

class LoanPaymentXlsx(models.AbstractModel):
    _name = 'report.rod_cooperativa.action_loan_payment_excel'
    _inherit = 'report.report_xlsx.abstract'  # <- OJO: no 'abstract'
    _description = 'Reporte XLSX de loan.payment (selección)'

    def generate_xlsx_report(self, workbook, data, payments):
        # payments = recordset de loan.payment (los active_ids)
        records = self.env['loan.payment'].browse(payments.ids)

        fmt_title = workbook.add_format({'font_size': 11, 'align': 'vcenter', 'bold': True})
        fmt_text = workbook.add_format({'font_size': 10, 'align': 'vcenter'})
        fmt_date = workbook.add_format({'num_format': 'dd/mm/yy', 'font_size': 10, 'align': 'vcenter'})
        fmt_num = workbook.add_format({'num_format': '#,##0.00', 'font_size': 10, 'align': 'vcenter'})

        fmt_yellow = workbook.add_format({
            'bg_color': '#FFFF00',  # amarillo
            'font_size': 10,
            'align': 'vcenter',
            'border': 0
        })

        sheet = workbook.add_worksheet("loan application")
        headers = ['No.', 'CODIGO', 'GRADO', 'AP.PATERNO', 'AP.MATERNO', 'NOMBRES', 'ALTA', 'TIPO DE MONEDA', 'PERIODO',
                   'D/MINDEF Bs']
        headers = ['No.', 'CODIGO', 'GRADO', 'AP.PATERNO', 'AP.MATERNO', 'NOMBRES', 'ALTA','TIPO DE MONEDA', 'TOTAL DEUDA', 'MESES PLAZO', 'OBS.', ]
        for c, h in enumerate(headers):
            sheet.write(0, c, h, fmt_title)

        row = 1
        for rec in records:
            partner = rec.partner_id
            grade = partner.category_partner_id if partner else ''
            sheet.write(row, 0, row, fmt_text)
            code = str(getattr(partner, 'code_contact', '') or '')
            sheet.write(row, 1, "000" + code, fmt_text)
            # sheet.write(row, 1, getattr(partner, '0000'+'code_contact', '') or '', fmt_text)
            sheet.write(row, 2, getattr(grade, 'code_loan', '') or '', fmt_text)
            sheet.write(row, 3, getattr(partner, 'paternal_surname', '') or '', fmt_text)
            sheet.write(row, 4, getattr(partner, 'maternal_surname', '') or '', fmt_text)
            nombres = getattr(partner, 'name_contact', None) or partner.display_name or ''
            sheet.write(row, 5, nombres, fmt_text)
            sheet.write(row, 6, 'ALTA', fmt_text)
            sheet.write(row, 7, 'BS.', fmt_text)
            sheet.write(row, 8, getattr(rec, 'amount_total_bs', '') or '', fmt_text)
            sheet.write(row, 9, '001', fmt_text)
            sheet.write(row, 10, 'PRESTAMO-PAV', fmt_text)
            # sheet.write(row, 6, "ALTA", fmt_text)
            # sheet.write(row, 7, "BS.", fmt_text)
            # sheet.write_number(row, 8, getattr(rec, 'amount_total_bs', 0.0) or 0.0, fmt_num)
            # sheet.write(row, 9, "001", fmt_text)
            # sheet.write(row, 10, "PRESTAMO", fmt_text)
            row += 1
            rec.state = 'scheduled'  # Actualizar el estado a 'scheduled'
            rec.date_scheduled = fields.Date.today()  # Asignar la fecha de programación
            if rec.flag_collect_guarantors == True:
                guarantor_one = rec.guarantor_one
                grade_guarantor_one = guarantor_one.category_partner_id if partner else ''
                sheet.write(row, 0, row, fmt_yellow)
                sheet.write(row, 1, getattr(guarantor_one, 'code_contact', '') or '', fmt_yellow)
                sheet.write(row, 2, getattr(grade_guarantor_one, 'code_loan', '') or '', fmt_yellow)
                sheet.write(row, 3, getattr(guarantor_one, 'paternal_surname', '') or '', fmt_yellow)
                sheet.write(row, 4, getattr(guarantor_one, 'maternal_surname', '') or '', fmt_yellow)
                nombres = getattr(guarantor_one, 'name_contact', None) or partner.display_name or ''
                sheet.write(row, 5, nombres, fmt_yellow)
                sheet.write(row, 6, 'ALTA', fmt_yellow)
                sheet.write(row, 7, 'BS.', fmt_yellow)
                sheet.write(row, 8, getattr(rec, 'amount_desc_guarantor_one', '') or '', fmt_yellow)
                sheet.write(row, 9, '001', fmt_yellow)
                sheet.write(row, 10, 'PRESTAMO-PAV', fmt_yellow)
                # sheet.write(row, 7, getattr(rec, 'amount_desc_guarantor_one', '') or '', fmt_yellow)
                row += 1

                guarantor_two = rec.guarantor_two
                grade_guarantor_two = guarantor_two.category_partner_id if partner else ''
                sheet.write(row, 0, row, fmt_yellow)
                sheet.write(row, 1, getattr(guarantor_two, 'code_contact', '') or '', fmt_yellow)
                sheet.write(row, 2, getattr(grade_guarantor_two, 'code_loan', '') or '', fmt_yellow)
                sheet.write(row, 3, getattr(guarantor_two, 'paternal_surname', '') or '', fmt_yellow)
                sheet.write(row, 4, getattr(guarantor_two, 'maternal_surname', '') or '', fmt_yellow)
                nombres = getattr(guarantor_two, 'name_contact', None) or partner.display_name or ''
                sheet.write(row, 5, nombres, fmt_yellow)
                sheet.write(row, 6, 'ALTA', fmt_yellow)
                sheet.write(row, 7, 'BS.', fmt_yellow)
                sheet.write(row, 8, getattr(rec, 'amount_desc_guarantor_two', '') or '', fmt_yellow)
                sheet.write(row, 9, '001', fmt_yellow)
                sheet.write(row, 10, 'PRESTAMO-PAV', fmt_yellow)
                # sheet.write(row, 7, getattr(rec, 'amount_desc_guarantor_two', '') or '', fmt_yellow)
                row += 1

