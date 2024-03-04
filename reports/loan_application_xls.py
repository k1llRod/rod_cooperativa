import base64
import io
from odoo import models, fields, api, _

class PartnerXlsx(models.AbstractModel):
    _name = 'report.rod_cooperativa.report_loan_application_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        loan_payment = self.env['loan.payment'].search([('period', '=', data['period'])])
        format1 = workbook.add_format({'font_size': 11, 'align': 'vcenter', 'bold': True})
        format2 = workbook.add_format({'font_size': 10, 'align': 'vcenter'})
        format3 = workbook.add_format({'num_format': 'dd/mm/yy', 'font_size': 10, 'align': 'vcenter'})
        sheet = workbook.add_worksheet("loan application")
        nro = 1
        sheet.write(0, 0, 'No.', format1)
        sheet.write(0, 1, 'CODIGO', format1)
        sheet.write(0, 2, 'GRADO', format1)
        sheet.write(0, 3, 'AP.PATERNO', format1)
        sheet.write(0, 4, 'AP.MATERNO', format1)
        sheet.write(0, 5, 'NOMBRES', format1)
        sheet.write(0, 6, 'ALTA', format1)
        sheet.write(0, 7, 'TIPO DE MONEDA', format1)
        sheet.write(0, 8, 'TOTAL DEUDA', format1)
        sheet.write(0, 9, 'MESES PLAZO', format1)
        sheet.write(0, 10, 'OBS', format1)
        for rec in loan_payment:
            sheet.write(nro, 0, nro, format2)
            sheet.write(nro, 1, rec.loan_application_ids.partner_id.code_contact, format2)
            sheet.write(nro, 2, rec.loan_application_ids.category_partner, format2)
            sheet.write(nro, 3, rec.loan_application_ids.partner_id.paternal_surname, format2)
            sheet.write(nro, 4, rec.loan_application_ids.partner_id.maternal_surname, format2)
            sheet.write(nro, 5, rec.loan_application_ids.partner_id.name_contact, format2)
            sheet.write(nro, 6, "ALTA", format2)
            sheet.write(nro, 7, "BS.", format2)
            sheet.write(nro, 8, rec.amount_total_bs, format2)
            sheet.write(nro, 9, "001", format2)
            sheet.write(nro, 10, "PRESTAMO", format2)
            nro += 1

        # for obj in partners:
        #     report_name = obj.name
        #     # One sheet by partner
        #     sheet = workbook.add_worksheet(report_name[:31])
        #     bold = workbook.add_format({'bold': True})
        #     sheet.write(0, 0, obj.name, bold)