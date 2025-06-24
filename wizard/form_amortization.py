from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
    with_guarantor = fields.Selection(
        [('loan_guarantor', 'Prestamo regular con garantes'), ('no_loan_guarantor', 'Prestamo regular sin garantes')],
        string='Tipo de prestamo regular', related='data_loan_id.with_guarantor', store=True)
    monthly_interest_mortgage = fields.Float(string='Interes mensual hipotecario', related='data_loan_id.monthly_interest_mortgage', store=True)
    mortgage_loan = fields.Float(string='Prestamo hipotecario', related='data_loan_id.mortgage_loan', store=True)
    @api.depends('month_amortization','amount_amortization')
    def _compute_recalculate_capital_rest(self):
        for record in self:
            record.recalculate_capital_rest = record.capital_rest - (record.amount_amortization - record.interest_days_rest)
            record.month_rest = record.quantity_month_initial - record.quantity_month_payment

    @api.onchange('amount_amortization', 'month_amortization')
    def _compute_index_loan_fixed_fee(self):
        if self.with_guarantor == 'loan_guarantor' or self.with_guarantor == 'no_loan_guarantor':
            interest = (self.data_loan_id.monthly_interest + self.data_loan_id.contingency_fund) / 100
            index_quantity = (1 - (1 + interest) ** (-self.month_amortization))
            index_loan = interest / index_quantity if index_quantity != 0 else 0
            self.new_fixed_fee = round(self.recalculate_capital_rest * index_loan,2)
            percentage_amount_min_def = round(self.new_fixed_fee,2) * self.data_loan_id.amount_min_def
            # self.new_fixed_fee = round(self.new_fixed_fee,2) + round(percentage_amount_min_def,2)
        else:
            interest = (self.monthly_interest_mortgage + self.mortgage_loan) / 100
            index_quantity = (1 - (1 + interest) ** (-self.month_amortization))
            index_loan = interest / index_quantity if index_quantity != 0 else 0
            self.new_fixed_fee = self.recalculate_capital_rest * index_loan
            percentage_amount_min_def = round(self.new_fixed_fee, 2) * self.data_loan_id.amount_min_def
            self.new_fixed_fee = round(self.new_fixed_fee, 2) + round(percentage_amount_min_def, 2)
            # self.pay_slip_balance = self.fixed_fee_bs * (100 / 40)
            # self.new_fixed_fee = round(self.fixed_fee, 2) + round(self.interest_month_surpluy, 2) + round(
            #     (self.amount_min_def * self.fixed_fee), 2)

            # record.total_capital_rest = record.capital_rest * 6.96

    def action_confirm(self):
        unlink_registers = self.data_loan_id.loan_payment_ids.filtered(lambda x: x.state == 'draft').unlink()
        count_amortization = len(self.data_loan_id.loan_payment_ids.filtered(lambda x: x.state == 'amortization'))
        count_total_registers = len(self.data_loan_id.loan_payment_ids.filtered(lambda x: x.state == 'amortization' or x.state == 'ministry_defense' or x.state == 'transfer'))
        create_loan_payment_amortization = self.env['loan.payment'].create({
            'loan_application_ids': self.data_loan_id.id,
            'name': 'AMORT '+str(count_amortization+1),
            'date': self.date_amortization,
            'date_payment': self.date_amortization,
            'amount_payment': self.amount_amortization,
            'capital_initial': self.capital_rest,
            'capital_index_initial': self.amount_amortization - self.interest_days_rest,
            'interest_month_surpluy': self.interest_days_rest,
            'amount_total': self.amount_amortization,
            'state': 'amortization'
        })
        if create_loan_payment_amortization:
            for i in range(1, self.month_amortization + 1):
                coa_commission = (1.25 / 100) * self.new_fixed_fee
                percentage_amount_min_def = self.new_fixed_fee * self.data_loan_id.amount_min_def
                # capital_init = create_loan_payment_amortization.balance_capital
                # date_payment = datetime.today()
                date_payment = self.date_amortization
                date_pivot = date_payment
                date_payment = date_payment.replace(day=1)
                date_payment = date_payment.replace(
                    month=date_payment.month + 1 if date_pivot.month < 12 else 1)
                date_payment = date_payment.replace(
                    year=date_payment.year + 1 if date_pivot.month == 12 else date_payment.year)

                capital_init = self.data_loan_id.loan_payment_ids[-1].balance_capital
                date_payment = self.data_loan_id.loan_payment_ids[-1].date
                date_payment = date_payment + relativedelta(months=+1)
                date_payment = date_payment.replace(day=1)
                self.env['loan.payment'].create({
                    'name': 'Cuota ' + str(i),
                    'date': date_payment,
                    'capital_initial': capital_init,
                    'mount': self.new_fixed_fee,
                    'loan_application_ids': self.data_loan_id.id,
                    'percentage_amount_min_def': percentage_amount_min_def,
                    'interest_month_surpluy': 0,
                    # 'interest_month_surpluy': self.data_loan_id.interest_month_surpluy,
                    # 'commission_min_def': amount_commission,
                    'coa_commission': coa_commission,
                    'state': 'draft',
                })
            # create_loan_payment = self.env['loan.payment'].create({
            #     'loan_application_ids': self.data_loan_id.id,
            #     'name': 'PAGO '+str(count_amortization+2),
            #     'date': self.date_amortization,
            #     'date_payment': self.date_amortization,
            #     'amount_payment': self.new_fixed_fee,
            #     'capital_initial': self.recalculate_capital_rest,
            #     'capital_index_initial': self.new_fixed_fee - self.interest_days_rest,
            #     'interest_month_surpluy': self.interest_days_rest,
            #     'amount_total': self.new_fixed_fee,
            #     'state': 'draft'
            # })
        a = 1



