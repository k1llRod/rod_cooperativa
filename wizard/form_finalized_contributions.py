from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta

class FormFinalizedContributions(models.TransientModel):
    _name = 'form.finalized.contributions'
    _description = 'Form Finalized Contributions'

    name = fields.Char(string = 'name')
    partner_payroll_id = fields.Many2one('partner.payroll', string='Codigo Aporte')
    date_finalize = fields.Date(string='Fecha de Finalizacion', required=True)
    disengagement = fields.Float(string='Desvinculacion', required=True, default=10)
    total_mandatory_contributions_certificate = fields.Float(string='Total de aportes obligatorios', required=True)
    total_voluntary_contributions_certificate = fields.Float(string='Total de aportes voluntarios', required=True)
    total_other_contributions = fields.Float(string='Total otros aportes', required=True)
    total_performance_contributions = fields.Float(string='Total rendimiento de aportes', required=True)
    total_balance_capital = fields.Float(string='Total saldo de prestamo', required=True)



    def action_confirm(self):
        # Here you can write the code to finalize the contributions
        a = 1