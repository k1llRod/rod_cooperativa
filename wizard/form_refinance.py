from odoo import models, fields, api, _

class FormRefinance(models.TransientModel):
    _name = 'form.refinance'

    name = fields.Char(string='Nombre', required=True)
    capital_rest = fields.Float(string='Capital Restante')
    interest_days_rest = fields.Integer(string='Días de Interés Restantes')
    total_capital_rest = fields.Float(string='Total Capital Restante')
    amount_refinance = fields.Float(string='Monto a Refinanciar')
    month_refinance = fields.Integer(string='Meses a Refinanciar')
    date_refinance = fields.Date(string='Fecha de Refinanciamiento')

    def init_refinance(self):
        a = 1