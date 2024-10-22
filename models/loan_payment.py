from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class LoanPayment(models.Model):
    _name = 'loan.payment'
    _description = 'Pagos de prestamos'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Codigo de pago', required=True)
    loan_application_ids = fields.Many2one('loan.application', string='Solicitud de prestamo', required=True)
    partner_id = fields.Many2one('res.partner', string='Socio', related='loan_application_ids.partner_id', store=True)

    type_loan = fields.Selection([('regular', 'Regular'), ('emergency', 'Emergencia')], string='Tipo de prestamo',
                                 related='loan_application_ids.type_loan')
    with_guarantor = fields.Selection(
        [('loan_guarantor', 'Prestamo regular con garantes'), ('no_loan_guarantor', 'Prestamo regular sin garantes')],
        string='Tipo de prestamo regular', related='loan_application_ids.with_guarantor')
    code_contact = fields.Char(string='Codigo de contacto', related='loan_application_ids.code_contact')
    ci_partner = fields.Char(string='Carnet de identidad', related='loan_application_ids.ci_partner')
    # partner_status_especific = fields.Selection([('active_service', 'Servicio activo'), ('guest', 'Invitado'),
    #                                              ('passive_reserve_a','Pasivo categoria "A"'),('passive_reserve_b','Pasivo categoria "B"')
    #                                              ('leave','Baja')], string='Estatus del socio', related='loan_application_ids.partner_status_especific')
    type_payment = fields.Selection([('1', 'Abono'), ('2', 'Transferencia')], string='Tipo de pago')
    date = fields.Date(string='Fecha de pago', required=True)
    date_payment = fields.Date(string='Fecha de pago')
    period = fields.Char(string='Periodo', compute='_compute_period', store=True)
    capital_initial = fields.Float(string='Capital inicial')
    capital_index_initial = fields.Float(string='Capital')
    mount = fields.Float(string='Cuota fija')
    interest = fields.Float(string='Interes', compute='_compute_interest', store=True)
    interest_base = fields.Float(string='0.7%', compute='_compute_interest', store=True)
    interest_mortgage = fields.Float(string='Interes H.', compute='_compute_interest', store=True)
    interest_base_mortgage = fields.Float(string='0.207%', compute='_compute_interest', digits=(16, 2), store=True)
    res_social = fields.Float(string='F.C. 0.04%', compute='_compute_interest', digits=(16, 2), store=True)
    res_mortgage = fields.Float(string='P.H. 0.04%', compute='_compute_interest', digits=(16, 2), store=True)
    balance_capital = fields.Float(string='Saldo capital', compute='_compute_interest', digits=(16, 2), store=True)
    percentage_amount_min_def = fields.Float(string='%MINDEF', digits=(16, 2), store=True)
    commission_min_def = fields.Float(string='0.25% MINDEF', digits=(16, 2), store=True)
    coa_commission = fields.Float(string='%COA')
    coa_commission_bs = fields.Float(string='%COA Bs')
    interest_month_surpluy = fields.Float(string='D/E', digits=(16, 2), store=True)
    amount_total = fields.Float(string='D/MINDEF $', digits=(16, 2))
    amount_total_bs = fields.Float(string='D/MINDEF Bs', compute='_change_amount_total_bs', digits=(16, 2), store=True)
    amount_returned_coa = fields.Float(string='Monto devuelto COA', digits=(16, 2), store=True)
    amount_payment = fields.Float(string='Monto a pagar', digits=(16, 2), store=True)
    state = fields.Selection(
        [('draft', 'Borrador'), ('transfer', 'Transferencia bancaria'),
         ('ministry_defense', 'Ministerio de defensa'), ('debt_settlement_mindef', 'Liquidacion de deuda MINDEF'),
         ('debt_settlement_deposit', 'Liquidacion de deuda por deposito')], string='Estado',
        default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Moneda', related='loan_application_ids.currency_id')
    currency_id_dollar = fields.Many2one('res.currency', string='Moneda en Dólares',
                                         default=lambda self: self.env.ref('base.USD'))
    flag_state = fields.Selection([
        ('init', 'Inicio'),
        ('verificate', 'Verificación'),
        ('progress', 'En Proceso'),
        ('done', 'Concluido'),
        ('refinanced', 'Refinanciado'),
        ('expansion', 'Ampliación'),
        ('cancel', 'Cancelado')
    ], string='Flag state', related='loan_application_ids.state')

    capital_index_initial_bolivianos = fields.Float(string='Capital BS', compute='_compute_bolivianos', store=True,
                                                    digits=(16, 2))
    interest_base_bolivianos = fields.Float(string='0.7% BS', compute='_compute_bolivianos', store=True, digits=(16, 2))
    res_social_bolivianos = fields.Float(string='F.C. BS', compute='_compute_bolivianos', store=True, digits=(16, 2))
    percentage_amount_min_def_bolivianos = fields.Float(string='%MINDEF BS', compute='_compute_bolivianos', store=True,
                                                        digits=(16, 2))
    interest_month_surpluy_bolivianos = fields.Float(string='D/E BS', compute='_compute_bolivianos', store=True,
                                                     digits=(16, 2))
    amount_total_bolivianos = fields.Float(string='D/MINDEF Bs', compute='_compute_bolivianos', digits=(16, 2),
                                           store=True)

    account_move_id = fields.Many2one('account.move', string='Asiento contable')
    state_account = fields.Selection([('draft', 'Borrador'), ('posted', 'Contabilizado'), ('cancel', 'Cancelado')],
                                     default='draft', related='account_move_id.state', store=True)

    account_income_id = fields.Many2one('account.account', string='Cuenta de ingreso')
    account_capital_index_id = fields.Many2one('account.account', string='Cuenta de capital')
    account_interest_base = fields.Many2one('account.account', string='Interes 0.7%')
    account_res_social = fields.Many2one('account.account', string='Fondo por Contingencia 0.04%')
    account_percentage_mindef = fields.Many2one('account.account', string='Porcentaje Min. Defensa')
    account_overage_days = fields.Many2one('account.account', string='Dias excedentes')
    account_overage_amount = fields.Many2one('account.account', string='Cuenta Monto excedente')

    journal_id = fields.Many2one('account.journal', string='Diario')
    amount_income = fields.Float(string='Monto ingreso')
    amount_capital_index = fields.Float(string='Monto Capital', digits=(16, 2), store=True)
    amount_interest = fields.Float(string='Monto interes', digits=(16, 2), store=True)
    amount_res_social = fields.Float(string='Monto contingencia', digits=(16, 2), store=True)
    amount_percentage_mindef = fields.Float(string='Monto porcentaje MINDEF', digits=(16, 2), store=True)
    amount_overage_days = fields.Float(string='Monto Dias D/E', digits=(16, 2), store=True)
    amount_overage = fields.Float(string='Monto excedente', digits=(16, 2), store=True)

    amount_interest_bs = fields.Float(string='Monto interes Bs', compute='_onchange_values_amount', digits=(16, 2), store=True)
    amount_capital_index_bs = fields.Float(string='Monto Capital Bs', compute='_onchange_values_amount', digits=(16, 2), store=True)
    amount_res_social_bs = fields.Float(string='Monto contingencia Bs', compute='_onchange_values_amount', digits=(16, 2), store=True)
    amount_percentage_mindef_bs = fields.Float(string='Monto porcentaje MINDEF Bs', compute='_onchange_values_amount', digits=(16, 4), store=True)
    amount_overage_days_bs = fields.Float(string='Monto Dias D/E Bs', compute='_onchange_values_amount', digits=(16, 2), store=True)
    amount_overage_bs = fields.Float(string='Monto excedente Bs', compute='_onchange_values_amount', digits=(16, 2), store=True)

    amount_sum = fields.Float(string='Total', compute='_sum_total', digits=(16, 2), store=True)
    amount_sum_bs = fields.Float(string='Total Bs', compute='_onchange_values_amount', digits=(16, 2), store=True)

    @api.depends('capital_index_initial', 'interest', 'res_social', 'percentage_amount_min_def',
                 'interest_month_surpluy')
    def _compute_bolivianos(self):
        for rec in self:
            rec.capital_index_initial_bolivianos = rec.capital_index_initial * round(
                rec.currency_id_dollar.inverse_rate, 2)
            rec.interest_base_bolivianos = rec.interest_base * round(rec.currency_id_dollar.inverse_rate, 2)
            rec.res_social_bolivianos = rec.res_social * rec.currency_id_dollar.inverse_rate
            rec.percentage_amount_min_def_bolivianos = rec.percentage_amount_min_def * round(
                rec.currency_id_dollar.inverse_rate, 2)
            rec.interest_month_surpluy_bolivianos = rec.interest_month_surpluy * round(
                rec.currency_id_dollar.inverse_rate, 2)
            rec.amount_total_bolivianos = (rec.capital_index_initial_bolivianos + rec.interest_base_bolivianos +
                                           rec.res_social_bolivianos + rec.percentage_amount_min_def_bolivianos + rec.interest_month_surpluy_bolivianos)

    @api.onchange('amount_total')
    def _change_amount_total_bs(self):
        for rec in self:
            rec.amount_total_bs = rec.amount_total * rec.currency_id_dollar.inverse_rate

    @api.depends('date')
    def _compute_period(self):
        for rec in self:
            rec.period = rec.date.strftime('%m/%Y') if rec.date else ''

    # @api.depends('mount')
    # def _compute_interest(self):
    #     for rec in self:
    #         rec.interest = rec.mount * 0.1

    @api.depends('capital_initial', 'balance_capital', 'interest', 'res_social')
    def _compute_interest(self):
        percentage_interest = float(
            self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest'))
        contingency_found = float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.contingency_fund'))

        interest = (percentage_interest + contingency_found) / 100

        mortgage_loan = float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.mortgage_loan'))
        percentage_interest_mortgage = float(
            self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest_mortgage'))

        interest_mortgage = (percentage_interest_mortgage + mortgage_loan) / 100

        for rec in self:
            if rec.loan_application_ids.with_guarantor == 'loan_guarantor' or rec.loan_application_ids.with_guarantor == 'no_loan_guarantor':
                rec.interest = rec.capital_initial * interest if rec.mount > 0 else 0
                rec.interest_base = rec.capital_initial * round((percentage_interest / 100), 3) if rec.mount > 0 else 0
                if rec.mount > 0:
                    rec.capital_index_initial = round(rec.mount - rec.interest, 2)
            if rec.loan_application_ids.with_guarantor == 'mortgage':
                rec.interest_mortgage = rec.capital_initial * interest_mortgage
                rec.interest_base_mortgage = rec.capital_initial * (percentage_interest_mortgage / 100)
                if rec.mount > 0:
                    rec.capital_index_initial = round(rec.mount - rec.interest_mortgage, 2)
            rec.balance_capital = rec.capital_initial - rec.capital_index_initial
            if rec.loan_application_ids.with_guarantor == 'loan_guarantor' or rec.loan_application_ids.with_guarantor == 'no_loan_guarantor':
                rec.res_social = rec.capital_initial * round((contingency_found / 100), 4) if rec.mount > 0 else 0
            if rec.loan_application_ids.with_guarantor == 'mortgage':
                rec.res_mortgage = rec.capital_initial * round((mortgage_loan / 100), 4)
            rec.amount_total = round(rec.mount, 2) + round(rec.percentage_amount_min_def, 2) + round(
                rec.interest_month_surpluy, 2) if rec.mount > 0 else rec.capital_index_initial + rec.interest_month_surpluy
            if rec.capital_index_initial >= rec.capital_initial:
                rec.amount_payment = round((rec.capital_index_initial + rec.interest_month_surpluy) * rec.loan_application_ids.value_dolar,2)
            rec._change_amount_total_bs()
            # rec.commission_min_def = round((commission_min_def / 100) * rec.amount_total_bs,2)
            # commision_auxiliar = rec.commission_min_def
            # rec.amount_returned_coa = round(rec.amount_total_bs,2) - commision_auxiliar

    def open_loan_payment(self, context=None):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Model Title',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current',
        }

    def confirm_payment(self):
        for record in self:
            if record.state == 'draft':
                record.write({'state': 'transfer'})

    def confirm_ministry_defense(self):
        for record in self:
            if record.state == 'draft':
                record.write({'state': 'ministry_defense'})

    def draft_massive(self):
        for record in self:
            record.write({'state': 'draft'})

    def debt_settlement_min_def(self):
        for record in self:
            if record.state == 'draft':
                record.write({'state': 'debt_settlement_mindef'})

    def debt_settlement_deposit(self):
        for record in self:
            if record.state == 'draft':
                record.write({'state': 'debt_settlement_deposit'})

    @api.onchange('amount_payment')
    def _onchange_amount_payment(self):
        for record in self:
            if record.amount_payment < record.amount_total_bs:
                raise ValidationError('El pago no puede ser menor al establecido en el plan de pagos.')
            else:
                record.amount_returned_coa = 0

    def create_account_move(self):
        for rec in self:
            amount = 0
            move_line_vals = []
            move_line = []
            journal_id = rec.journal_id.id
            if rec.state == 'transfer':
                data = (
                    0, 0, {'account_id': rec.account_income_id.id,
                           'debit': rec.amount_payment,
                           'credit': 0,
                           'partner_id': rec.loan_application_ids.partner_id.id,
                           'amount_currency': 0
                           })
                if not (rec.amount_payment == 0):
                    move_line.append(data)
                    # amount = rec.amount_payment + amount
                data = (0, 0, {
                    'account_id': rec.account_capital_index_id.id,
                    'debit': 0, 'credit': rec.amount_capital_index_bs,
                    'partner_id': rec.loan_application_ids.partner_id.id,
                    'amount_currency': 0
                })
                if not (rec.capital_index_initial_bolivianos == 0):
                    move_line.append(data)
                    amount = rec.amount_capital_index_bs + amount
                data = (0, 0, {
                    'account_id': rec.account_interest_base.id,
                    'debit': 0, 'credit': rec.amount_interest_bs,
                    'partner_id': rec.loan_application_ids.partner_id.id,
                    'amount_currency': 0
                })

                if not (rec.interest_base_bolivianos == 0):
                    move_line.append(data)
                    amount = rec.amount_interest_bs + amount
                data = (0, 0, {
                    'account_id': rec.account_res_social.id,
                    'debit': 0, 'credit': rec.amount_res_social_bs,
                    'partner_id': rec.loan_application_ids.partner_id.id,
                    'amount_currency': 0
                })
                if not (rec.res_social_bolivianos == 0):
                    move_line.append(data)
                    amount = rec.amount_res_social_bs + amount
                data = (0, 0, {
                    'account_id': rec.account_percentage_mindef.id,
                    'debit': 0, 'credit': rec.amount_percentage_mindef_bs,
                    'partner_id': rec.loan_application_ids.partner_id.id,
                    'amount_currency': 0
                })
                if not (rec.percentage_amount_min_def_bolivianos == 0):
                    move_line.append(data)
                    amount = rec.amount_percentage_mindef_bs + amount
                data = (0, 0, {'account_id': rec.account_overage_days.id,
                               'debit': 0, 'credit': rec.amount_overage_days_bs,
                               'partner_id': rec.loan_application_ids.partner_id.id,
                               'amount_currency': 0
                               })
                if not (rec.interest_month_surpluy_bolivianos == 0):
                    move_line.append(data)
                    amount = rec.amount_overage_days_bs + amount
                data = (0, 0, {'account_id': rec.account_overage_amount.id,
                               'debit': 0, 'credit': rec.amount_overage,
                               'partner_id': rec.loan_application_ids.partner_id.id,
                               'amount_currency': 0
                               })
                if not (rec.amount_overage == 0):
                    move_line.append(data)
                    amount = rec.amount_overage + amount
            if not(rec.amount_payment == amount):
                validate = round(rec.amount_payment - amount, 2)
                data = (0, 0, {'account_id': rec.account_overage_amount.id,
                               'debit': 0, 'credit': validate,
                               'partner_id': rec.loan_application_ids.partner_id.id,
                               'amount_currency': 0
                               })
                move_line.append(data)
            move_vals = {
                "date": rec.date,
                "journal_id": journal_id,
                "ref": "PAGO PREST" + " " + rec.loan_application_ids.partner_id.name + " " + rec.period,
                # "company_id": payment.company_id.id,
                # "name": "name test",
                "state": "draft",
                "line_ids": move_line,
            }
            account_move_id = rec.env['account.move'].create(move_vals)
            rec.account_move_id = account_move_id.id
            account_move_id.loan_payment_id = rec.id

    @api.onchange('account_income_id')
    def _onchange_account_income_id(self):
        for record in self:
            record.amount_income = record.amount_payment
            record.amount_capital_index = record.capital_index_initial
            record.amount_interest = record.interest_base
            record.amount_res_social = record.res_social
            record.amount_percentage_mindef = record.percentage_amount_min_def
            record.amount_overage_days = record.interest_month_surpluy
            # record.amount_sum = record.amount_capital_index + record.amount_interest + record.amount_res_social + record.amount_percentage_mindef + record.amount_overage_days

    @api.depends('amount_income','amount_capital_index','amount_interest','amount_res_social','amount_percentage_mindef','amount_overage_days','amount_overage')
    def _onchange_values_amount(self):
        for record in self:
            record.amount_interest_bs = record.amount_interest * record.currency_id_dollar.inverse_rate
            record.amount_capital_index_bs = record.amount_capital_index * record.currency_id_dollar.inverse_rate
            record.amount_res_social_bs = record.amount_res_social * record.currency_id_dollar.inverse_rate
            record.amount_percentage_mindef_bs = record.amount_percentage_mindef * record.currency_id_dollar.inverse_rate
            record.amount_overage_days_bs = record.amount_overage_days * record.currency_id_dollar.inverse_rate
            record.amount_sum_bs = record.amount_sum * record.currency_id_dollar.inverse_rate
    @api.depends('amount_capital_index','amount_interest','amount_res_social','amount_percentage_mindef','amount_overage_days','amount_overage')
    def _sum_total(self):
        for record in self:
            record.amount_sum = record.amount_capital_index + record.amount_interest + record.amount_res_social + record.amount_percentage_mindef + record.amount_overage_days
            if record.amount_income > record.amount_sum:
                record.amount_overage = record.amount_income - record.amount_sum_bs
