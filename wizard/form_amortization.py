from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FormAmortization(models.TransientModel):
    _name='form.amortization'
    _description='Form Amortization'

    name=fields.Char(string='Codigo de amortización', default='Nuevo')
    capital_initial=fields.Float(string='Monto de prestamo inicial')
    capital_rest=fields.Float(string='Saldo capital $')
    quantity_month_initial=fields.Integer(string='Cantidad de meses inicial')
    quantity_month_payment=fields.Integer(string='Cantidad de meses pagados')
    interest_days_rest=fields.Float(string='Días de Interés Restantes')
    interest_days_rest_bs=fields.Float(string='Días de Interés Restantes Bs')
    total_capital_rest=fields.Float(string='Saldo capital Bs')
    amount_amortization=fields.Float(string='Monto a Amortizar ($)', required=True)
    month_amortization=fields.Integer(string='Meses a Amortizar', required=True)
    date_amortization=fields.Date(string='Fecha de Amortización', required=True)
    data_loan_id=fields.Many2one('loan.application', string='Datos del prestamo')
    fixed_fee=fields.Float(string='Cuota fija ($)', compute='_compute_index_loan_fixed_fee')
    index_loan=fields.Float(string='Indice de prestamo ($)', compute='_compute_index_loan_fixed_fee')
    index_loan_bs=fields.Float(string='Indice de prestamo (Bs)')
    total_fixed_fee=fields.Float(string='Cuota fija total ($)')
    recalculate_capital_rest=fields.Float(string='Recalcular saldo capital $', compute='_compute_recalculate_capital_rest')
    month_rest=fields.Integer(string='Meses restantes')
    new_fixed_fee=fields.Float(string='Nueva cuota fija ($)', compute='_compute_index_loan_fixed_fee')
    index_loan = fields.Float(string='Indice de prestamo ($)', compute='_compute_index_loan_fixed_fee')

    @api.depends('month_amortization','amount_amortization')
    def _compute_recalculate_capital_rest(self):
        for record in self:
            record.recalculate_capital_rest = record.capital_rest - record.amount_amortization
            record.month_rest = record.quantity_month_initial - record.quantity_month_payment

    @api.onchange('month_refinance', 'amount_refinance')
    def _compute_index_loan_fixed_fee(self):
        try:
            interest = (self.monthly_interest + self.contingency_fund) / 100
            index_quantity = (1 - (1 + interest) ** (-self.month_refinance))
            self.index_loan = interest / index_quantity if index_quantity != 0 else 0
            self.fixed_fee = self.amount_refinance * self.index_loan
        except:
            self.index_loan = 0
            # record.total_capital_rest = record.capital_rest * 6.96

    def action_confirm(self):
        a = 1