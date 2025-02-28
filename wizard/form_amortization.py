from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FormAmortization(models.TransientModel):
    _name='form.amortization'
    _description='Form Amortization'

    name=fields.Char(string='Codigo de amortización', default='Nuevo')
    capital_initial=fields.Float(string='Monto de prestamo inicial')
    capital_rest=fields.Float(string='Saldo capital $')
    quantity_month_initial=fields.Integer(string='Cantidad de meses inicial')
    interest_days_rest=fields.Float(string='Días de Interés Restantes')
    total_capital_rest=fields.Float(string='Saldo capital Bs')
    amount_amortization=fields.Float(string='Monto a Amortizar', required=True)
    month_amortization=fields.Integer(string='Meses a Amortizar', required=True)
    date_amortization=fields.Date(string='Fecha de Amortización', required=True)
    data_loan_id=fields.Many2one('loan.application', string='Datos del prestamo')
    fixed_fee=fields.Float(string='Cuota fija ($)', compute='_compute_index_loan_fixed_fee')
    index_loan=fields.Float(string='Indice de prestamo ($)', compute='_compute_index_loan_fixed_fee')
    index_loan_bs=fields.Float(string='Indice de prestamo (Bs)')

    def action_confirm(self):
        a = 1