from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class CalculatorLoan(models.Model):
    _name = 'calculator.loan'
    _description = 'Calculadora de Préstamos'

    name = fields.Char(string='Nombre')
    amount_loan = fields.Float(string='Monto de prestamo (Bolivianos)', compute='_compute_change_dollars_bolivian')
    amount_loan_dollars = fields.Float(string='Monto de prestamo (dolares)')
    months_quantity = fields.Integer(string='Cantidad de meses', tracking=True)
    index_loan = fields.Float(string='Indice de prestamo ($)', compute='_compute_index_loan_fixed_fee')
    index_loan_bs = fields.Float(string='Indice de prestamo (Bs)')
    fixed_fee = fields.Float(string='Cuota fija ($)', compute='_compute_index_loan_fixed_fee')
    fixed_fee_bs = fields.Float(string='Cuota fija (Bs)', compute='_compute_index_loan_fixed_fee_bs')
    date_application = fields.Date(string='Fecha de solicitud', default=fields.Date.today())
    date_approval = fields.Date(string='Fecha de aprobacion')
    surplus_days = fields.Integer(string='Dias excedentes')
    interest_month_surpluy = fields.Float(string='Interes dias excedente')
    total_interest_month_surpluy = fields.Float(string='Total interes mensual excedente',
                                                compute='_compute_total_interest_month_surpluy', store=True)

    @api.depends('interest_month_surpluy', 'months_quantity')
    def _compute_total_interest_month_surpluy(self):
        for rec in self:
            rec.total_interest_month_surpluy = rec.interest_month_surpluy * rec.months_quantity

    @api.onchange('months_quantity', 'with_guarantor')
    def _compute_index_loan_fixed_fee(self):
        try:
            if self.with_guarantor == 'loan_guarantor' or self.with_guarantor == 'no_loan_guarantor':
                interest = (self.monthly_interest + self.contingency_fund) / 100
                index_quantity = (1 - (1 + interest) ** (-self.months_quantity))
                self.index_loan = interest / index_quantity if index_quantity != 0 else 0
                self.fixed_fee = self.amount_loan_dollars * self.index_loan
                self.pay_slip_balance = self.fixed_fee_bs * (100 / 40)
            else:
                interest = (self.monthly_interest_mortgage + self.mortgage_loan) / 100
                index_quantity = (1 - (1 + interest) ** (-self.months_quantity))
                self.index_loan = interest / index_quantity if index_quantity != 0 else 0
                self.fixed_fee = self.amount_loan_dollars * self.index_loan
                self.pay_slip_balance = self.fixed_fee_bs * (100 / 40)
        except:
            self.index_loan = 0