from odoo import models, fields, api, _

class FormRefinance(models.TransientModel):
    _name = 'form.refinance'

    name = fields.Char(string='Codigo de refinancimiento', default='Nuevo')
    capital_initial = fields.Float(string='Monto de prestamo inicial')
    capital_rest = fields.Float(string='Capital Restante')
    quantity_month_initial = fields.Integer(string='Cantidad de meses inicial')
    interest_days_rest = fields.Float(string='Días de Interés Restantes')
    total_capital_rest = fields.Float(string='Total Capital Restante')
    amount_refinance = fields.Float(string='Monto a Refinanciar')
    month_refinance = fields.Integer(string='Meses a Refinanciar')
    date_refinance = fields.Date(string='Fecha de Refinanciamiento')
    data_loan_id = fields.Many2one('loan.application', string='Datos del prestamo')
    amount_delivered = fields.Float(string='Monto a entregar' ,compute='_compute_amount_delivered', store=True)

    fixed_fee = fields.Float(string='Cuota fija ($)', compute='')
    index_loan = fields.Float(string='Indice de prestamo ($)', compute='_compute_index_loan_fixed_fee')
    index_loan_bs = fields.Float(string='Indice de prestamo (Bs)')
    @api.onchange('month_refinance')
    def _compute_index_loan_fixed_fee(self):
        try:
            interest = (self.monthly_interest + self.contingency_fund) / 100
            index_quantity = (1 - (1 + interest) ** (-self.month_refinance))
            self.index_loan = interest / index_quantity if index_quantity != 0 else 0
            self.fixed_fee = self.amount_loan_dollars * self.index_loan
        except:
            self.index_loan = 0
    def init_refinance(self):
        a = 1
    @api.depends('amount_refinance')
    def _compute_amount_delivered(self):
        for rec in self:
            rec.amount_delivered = rec.amount_refinance - rec.capital_rest