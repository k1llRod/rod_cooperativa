from odoo import models, fields, api
from datetime import datetime


class MindefLoanReportWizard(models.TransientModel):
    _name = 'mindef.loan.report.wizard'
    _description = 'Asistente para Reporte Mensual de Préstamos'

    month = fields.Selection([
        ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'),
        ('04', 'Abril'), ('05', 'Mayo'), ('06', 'Junio'),
        ('07', 'Julio'), ('08', 'Agosto'), ('09', 'Septiembre'),
        ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
    ], string='Mes', required=True, default=lambda self: str(datetime.today().month).zfill(2))

    year = fields.Char(string='Año', default=lambda self: str(fields.Date.today().year), required=True)

    # Campos de pre-visualización (Contadores)
    draft_quantity = fields.Integer(string='En borrador', readonly=True)
    no_reconciled_quantity = fields.Integer(string='No conciliado', readonly=True)
    reconciled_quantity = fields.Integer(string='Conciliado', readonly=True)
    observed_quantity = fields.Integer(string='Observado', readonly=True)

    @api.onchange('month', 'year')
    def _onchange_month_year(self):
        if self.month and self.year:
            period = f"{self.month}/{self.year}"
            # Filtramos en el modelo de PRÉSTAMOS (loan)
            loans = self.env['nominal.relationship.mindef.loan'].search([
                ('period_process', '=', period)
            ])
            self.draft_quantity = len(loans.filtered(lambda x: x.state == 'draft'))
            self.no_reconciled_quantity = len(loans.filtered(lambda x: x.state == 'no_reconciled'))
            self.reconciled_quantity = len(loans.filtered(lambda x: x.state == 'reconciled'))
            self.observed_quantity = len(loans.filtered(lambda x: x.state == 'observed'))
        else:
            self.draft_quantity = 0
            self.no_reconciled_quantity = 0
            self.reconciled_quantity = 0
            self.observed_quantity = 0

    def action_generate_report(self):
        self.ensure_one()
        period = f"{self.month}/{self.year}"

        # Buscamos los préstamos del periodo
        loans = self.env['nominal.relationship.mindef.loan'].search([
            ('period_process', '=', period)
        ])

        summary_data = {
            'period': period,
            'date_report': fields.Datetime.now().strftime('%d/%m/%Y %H:%M'),
            'stats': {
                'draft': self.draft_quantity,
                'no_reconciled': self.no_reconciled_quantity,
                'reconciled': self.reconciled_quantity,
                'observed': self.observed_quantity,
                'total': len(loans),
            },
            # IDs para el motor de reporte (Excel/PDF)
            'ids_draft': loans.filtered(lambda x: x.state == 'draft').ids,
            'ids_no_reconciled': loans.filtered(lambda x: x.state == 'no_reconciled').ids,
            'ids_reconciled': loans.filtered(lambda x: x.state == 'reconciled').ids,
            'ids_observed': loans.filtered(lambda x: x.state == 'observed').ids,
        }

        # Cambia 'rod_cooperativa_prestamos' por el nombre técnico de tu módulo
        return self.env.ref('rod_cooperativa.action_report_mindef_loan_xlsx').report_action(self,
                                                                                                      data=summary_data)