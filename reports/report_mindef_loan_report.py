from odoo import models


class MindefLoanReportXlsx(models.AbstractModel):
    _name = 'report.rod_cooperativa.report_mindef_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet('Planilla Préstamos')

        # --- ESTILOS ---
        title_style = workbook.add_format(
            {'bold': True, 'font_size': 14, 'align': 'center', 'bg_color': '#4F81BD', 'font_color': 'white'})
        header_style = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D9E1F2', 'align': 'center'})
        sub_title_style = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1})
        data_style = workbook.add_format({'border': 1})
        money_style = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        center_style = workbook.add_format({'border': 1, 'align': 'center'})

        # --- ENCABEZADO ---
        sheet.merge_range('A1:I1', 'RESUMEN COMPARATIVO DE PRÉSTAMOS MINDEF', title_style)
        sheet.write('A2', 'Periodo:', sub_title_style)
        sheet.write('B2', data.get('period'), data_style)
        sheet.write('A3', 'Fecha Reporte:', sub_title_style)
        sheet.write('B3', data.get('date_report'), data_style)

        row = 5
        sections = [
            ('BORRADOR', data.get('ids_draft'), '#D9E1F2'),
            ('NO CONCILIADOS', data.get('ids_no_reconciled'), '#FCE4D6'),
            ('CONCILIADOS', data.get('ids_reconciled'), '#E2EFDA'),
            ('OBSERVADOS', data.get('ids_observed'), '#FFF2CC'),
        ]

        for title, ids, color in sections:
            if not ids: continue

            section_style = workbook.add_format({'bold': True, 'bg_color': color, 'border': 1})
            sheet.merge_range(row, 0, row, 8, f"ESTADO: {title} - Cantidad: {len(ids)}", section_style)
            row += 1

            # Encabezados extendidos para comparación
            headers = ['N°', 'C.I.', 'Grado', 'Nombre Completo', 'Monto MINDEF', 'Monto Sistema', 'Diferencia',
                       'Cod. Contacto', 'Estado']
            for col, text in enumerate(headers):
                sheet.write(row, col, text, header_style)
            row += 1

            records_raw = self.env['nominal.relationship.mindef.loan'].browse(ids)
            records = sorted(records_raw, key=lambda x: x.name_complete or '')

            counter = 1
            for rec in records:
                # Búsqueda dinámica del monto en el sistema (loan.payment)
                monto_sistema = 0.0
                pago_cuota = self.env['loan.payment'].search([
                    ('partner_id.code_contact', '=', rec.eit_item),
                    ('period', '=', rec.period_process),
                    ('state', 'in', ['ministry_defense', 'reconciled'])
                ], limit=1)

                if pago_cuota:
                    monto_sistema = pago_cuota.amount_total_bs

                sheet.write(row, 0, counter, center_style)
                sheet.write(row, 1, rec.ci or '', data_style)
                sheet.write(row, 2, rec.degree or '', data_style)
                sheet.write(row, 3, rec.name_complete or '', data_style)

                # Montos
                sheet.write(row, 4, rec.amount_bs or 0.0, money_style)
                sheet.write(row, 5, monto_sistema, money_style)
                sheet.write(row, 6, (rec.amount_bs or 0.0) - monto_sistema, money_style)

                sheet.write(row, 7, rec.eit_item or '', data_style)
                sheet.write(row, 8, rec.state or '', data_style)

                row += 1
                counter += 1
            row += 2

            # Ajuste de anchos
        sheet.set_column('A:A', 5)
        sheet.set_column('B:C', 12)
        sheet.set_column('D:D', 35)
        sheet.set_column('E:G', 14)
        sheet.set_column('H:I', 12)