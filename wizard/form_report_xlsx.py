from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FormReportXlsx(models.TransientModel):
    _name ='report.form.xlsx'
    _inherit = 'report.report_xlsx.abstract'


    name = fields.Char(string='Nombre del reporte')
    date_start = fields.Date(string='Fecha')
    # date_end = fields.Date(string='Fecha de fin')
    period = fields.Char(string='Periodo de proceso', compute='_compute_period', store=True)

    @api.depends('date_start')
    def _compute_period(self):
        for rec in self:
            if rec.date_start:
                rec.period = rec.date_start.strftime('%m/%Y')

    def print_report(self):
        data = {
            'date_start': self.date_start,
            'period': self.period,
            'form_data': self.read()[0],
        }
        return self.env.ref('rod_cooperativa.action_report_loan_application_xls').report_action(self, data=data)

    def print_report_xlsx(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'name': self.name,
                'date_start': self.date_start,
                'date_end': self.date_end
            },
        }
        return self.env.ref('rod_cooperativa.report_form_xlsx').report_action(self, data=data)