from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

# from server.odoo.tools.populate import compute


class LoanPayment(models.Model):
    _name = 'loan.payment'
    _description = 'Pagos de prestamos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date asc'

    name = fields.Char(string='Codigo de pago', required=True)
    loan_application_ids = fields.Many2one('loan.application', string='Solicitud de prestamo', required=True)
    partner_id = fields.Many2one('res.partner', string='Socio', related='loan_application_ids.partner_id', store=True)

    type_loan = fields.Selection([('regular', 'Regular'), ('emergency', 'Emergencia')], string='Tipo de prestamo',
                                 related='loan_application_ids.type_loan')
    with_guarantor = fields.Selection(
        [('loan_guarantor', 'Prestamo regular con garantes'), ('no_loan_guarantor', 'Prestamo regular sin garantes')],
        string='Tipo de prestamo regular', related='loan_application_ids.with_guarantor', store=True)
    code_contact = fields.Char(string='Codigo de contacto', related='loan_application_ids.code_contact', store=True)
    ci_partner = fields.Char(string='Carnet de identidad', related='loan_application_ids.ci_partner', store=True)
    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('guest', 'Invitado'),
                                                 ('passive_reserve_a','Pasivo categoria "A"'),
                                                 ('passive_reserve_b','Pasivo categoria "B"'),
                                                 ('leave','Baja')], string='Tipo de asociado', related='loan_application_ids.partner_id.partner_status_especific', store=True)
    type_payment = fields.Selection([('1', 'Abono'), ('2', 'Transferencia')], string='Tipo de pago')

    guarantor_one = fields.Many2one('res.partner', string='Garante 1', related='loan_application_ids.guarantor_one', store=True, tracking=True)
    guarantor_two = fields.Many2one('res.partner', string='Garante 2', related='loan_application_ids.guarantor_two', store=True, tracking=True)
    code_garantor_one = fields.Char(string='Codigo de garante 1', related='guarantor_one.code_contact', store=True)
    code_garantor_two = fields.Char(string='Codigo de garante 2', related='guarantor_two.code_contact', store=True)
    flag_collect_guarantors = fields.Boolean(string='Cobrar a garantes', related='loan_application_ids.flag_collect_guarantors', store=True)
    amount_desc_guarantor_one = fields.Float(string='Monto descontado garante 1', compute='_compute_guarantor_fields', store=True, digits=(16, 2))
    amount_desc_guarantor_two = fields.Float(string='Monto descontado garante 2', compute='_compute_guarantor_fields', store=True, digits=(16, 2))

    date = fields.Date(string='Fecha pivote', required=True)
    date_payment = fields.Date(string='Fecha de pago')
    period = fields.Char(string='Periodo', compute='_compute_period', store=True)

    # Moneda base (Bs) = la de la compañía
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one('res.currency', string='Moneda (Bs)', related='company_id.currency_id', store=True,
                                  readonly=True)
    # Moneda USD fija
    currency_id_dollar = fields.Many2one('res.currency', string='Moneda (USD)',
                                         default=lambda self: self.env.ref('base.USD'), readonly=True)

    capital_initial = fields.Monetary(string='Capital inicial',currency_field='currency_id_dollar')
    capital_index_initial = fields.Monetary(string='Capital',currency_field='currency_id_dollar')
    mount = fields.Monetary(string='Cuota fija',currency_field='currency_id_dollar')
    interest = fields.Monetary(string='Interes', compute='_compute_interest', store=True,currency_field='currency_id_dollar')
    interest_base = fields.Monetary(string='0.7%', compute='_compute_interest', store=True,currency_field='currency_id_dollar')
    interest_mortgage = fields.Monetary(string='Interes H.', compute='_compute_interest', store=True,currency_field='currency_id_dollar')
    interest_base_mortgage = fields.Monetary(string='0.207%', compute='_compute_interest', digits=(16, 2), store=True,currency_field='currency_id_dollar')
    res_social = fields.Monetary(string='F.C. 0.04%', compute='_compute_interest', digits=(16, 2), store=True,currency_field='currency_id_dollar')
    res_mortgage = fields.Monetary(string='P.H. 0.04%', compute='_compute_interest', digits=(16, 2), store=True,currency_field='currency_id_dollar')
    balance_capital = fields.Monetary(string='Saldo capital', compute='_compute_interest', digits=(16, 2),currency_field='currency_id_dollar', store=True)
    percentage_amount_min_def = fields.Monetary(string='%MINDEF', digits=(16, 2), store=True,currency_field='currency_id_dollar')
    commission_min_def = fields.Monetary(string='0.25% MINDEF', digits=(16, 2), store=True,currency_field='currency_id_dollar')
    coa_commission = fields.Monetary(string='%COA',currency_field='currency_id_dollar')
    coa_commission_bs = fields.Monetary(string='%COA Bs',currency_field='currency_id')
    interest_month_surpluy = fields.Monetary(string='D/E', digits=(16, 2), store=True,currency_field='currency_id_dollar')
    amount_total = fields.Monetary(string='D/MINDEF $', digits=(16, 2),currency_field='currency_id_dollar')
    amount_total_bs = fields.Monetary(string='D/MINDEF Bs', digits=(16, 2), store=True,currency_field='currency_id')
    amount_returned_coa = fields.Monetary(string='Monto devuelto COA', digits=(16, 2), store=True,currency_field='currency_id')
    amount_payment = fields.Monetary(string='Monto a pagar', digits=(16, 2), store=True,currency_field='currency_id')
    state = fields.Selection(
        [('draft', 'Borrador'),
         ('scheduled', 'Programado'),
         ('transfer', 'Transferencia bancaria'),
         ('ministry_defense', 'Ministerio de defensa'),
         ('ministry_defense_warrantor', 'Ministerio de defensa garantes'),
         ('not_discounted','No descontado'),
         ('debt_settlement_mindef', 'Liquidacion de deuda MINDEF'),
         ('debt_settlement_deposit', 'Liquidacion de deuda por deposito'),
         ('amortization','Amortizacion'),
         ('payment_mora','Descuento con mora'),
         ('scheduled_mora','Programado con mora')], string='Estado',
        default='draft', tracking=True)

    flag_state = fields.Selection([
        ('init', 'Inicio'),
        ('verificate', 'Verificación'),
        ('progress', 'En Proceso'),
        ('done', 'Concluido'),
        ('refinanced', 'Refinanciado'),
        ('expansion', 'Ampliación'),
        ('cancel', 'Cancelado')
    ], string='Flag state', related='loan_application_ids.state')

    capital_index_initial_bolivianos = fields.Monetary(string='Capital BS', compute='_compute_bolivianos', store=True,
                                                    digits=(16, 2),currency_field='currency_id')
    interest_base_bolivianos = fields.Monetary(string='0.7% BS', compute='_compute_bolivianos', store=True, digits=(16, 2),currency_field='currency_id')
    res_social_bolivianos = fields.Monetary(string='F.C. BS', compute='_compute_bolivianos', store=True, digits=(16, 2),currency_field='currency_id')
    percentage_amount_min_def_bolivianos = fields.Monetary(string='%MINDEF BS', compute='_compute_bolivianos', store=True,
                                                        digits=(16, 2),currency_field='currency_id')
    interest_month_surpluy_bolivianos = fields.Monetary(string='D/E BS', compute='_compute_bolivianos', store=True,
                                                     digits=(16, 2),currency_field='currency_id')
    amount_total_bolivianos = fields.Monetary(string='D/MINDEF Bs', compute='_compute_bolivianos', digits=(16, 2),
                                           store=True,currency_field='currency_id')

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
    amount_income = fields.Monetary(string='Monto ingreso')
    amount_capital_index = fields.Monetary(string='Monto Capital', digits=(16, 2), store=True,currency_field='currency_id_dollar')
    amount_interest = fields.Monetary(string='Monto interes', digits=(16, 2), store=True,currency_field='currency_id_dollar')
    amount_res_social = fields.Monetary(string='Monto contingencia', digits=(16, 2), store=True,currency_field='currency_id_dollar')
    amount_percentage_mindef = fields.Monetary(string='Monto porcentaje MINDEF', digits=(16, 2), store=True,currency_field='currency_id_dollar')
    amount_overage_days = fields.Monetary(string='Monto Dias D/E', digits=(16, 2), store=True,currency_field='currency_id_dollar')
    amount_overage = fields.Monetary(string='Monto excedente', digits=(16, 2), store=True,currency_field='currency_id_dollar')

    amount_interest_bs = fields.Monetary(string='Monto interes Bs', compute='_onchange_values_amount', digits=(16, 2), store=True,currency_field='currency_id')
    amount_capital_index_bs = fields.Monetary(string='Monto Capital Bs', compute='_onchange_values_amount', digits=(16, 2), store=True,currency_field='currency_id')
    amount_res_social_bs = fields.Monetary(string='Monto contingencia Bs', compute='_onchange_values_amount', digits=(16, 2), store=True,currency_field='currency_id')
    amount_percentage_mindef_bs = fields.Monetary(string='Monto porcentaje MINDEF Bs', compute='_onchange_values_amount', digits=(16, 4), store=True,currency_field='currency_id')
    amount_overage_days_bs = fields.Monetary(string='Monto Dias D/E Bs', compute='_onchange_values_amount', digits=(16, 2), store=True,currency_field='currency_id')
    amount_overage_bs = fields.Monetary(string='Monto excedente Bs', compute='_onchange_values_amount', digits=(16, 2), store=True,currency_field='currency_id')

    amount_sum = fields.Monetary(string='Total', compute='_sum_total', digits=(16, 2), store=True,currency_field='currency_id')
    amount_sum_bs = fields.Monetary(string='Total Bs', compute='_onchange_values_amount', digits=(16, 2), store=True,currency_field='currency_id')

    date_scheduled = fields.Date(string='Fecha programada', help="Fecha programada para el pago del préstamo")
    special_case = fields.Boolean(string='Caso especial', related='loan_application_ids.special_case', store=True)

    date_initial_mora = fields.Date(string='Fecha inicial de mora')
    date_end_mora = fields.Date(string='Fecha fin de mora')
    days_mora = fields.Integer(string='Días de mora')
    amount_mora = fields.Monetary(string='Monto de mora', digits=(16, 2), compute='_calculate_mora', store=True,currency_field='currency_id_dollar')
    amount_mora_bs = fields.Monetary(string='Monto de mora Bs', compute='_onchange_amount_mora', digits=(16, 2), store=True,currency_field='currency_id')
    amount_total_original = fields.Monetary(string='Desc Original', digits=(16, 2), store=True,currency_field='currency_id_dollar')
    mora_applied = fields.Boolean(string='Mora aplicada', store=True, default=False)

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
            if rec.balance_capital < 0:
                rec.balance_capital = 0
            if rec.balance_capital > 0 and rec.balance_capital < 1:
                rec.balance_capital = 0

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
            if record.state == 'draft' or record.state == 'scheduled':
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
            journal_id = rec.loan_application_ids.journal_income_id.id if rec.loan_application_ids.journal_income_id else rec.journal_id.id
            if rec.state == 'transfer' or rec.state == 'amortization':
                data = (
                    0, 0, {'account_id': rec.account_income_id.id if rec.account_income_id else rec.loan_application_ids.account_capital_index_id.id,
                           'debit': rec.amount_payment,
                           'credit': 0,
                           'partner_id': rec.loan_application_ids.partner_id.id,
                           'amount_currency': 0
                           })
                if not (rec.amount_payment == 0):
                    move_line.append(data)
                    # amount = rec.amount_payment + amount
                data = (0, 0, {
                    'account_id': rec.account_capital_index_id.id if rec.account_capital_index_id else rec.loan_application_ids.account_capital_index_id.id,
                    'debit': 0, 'credit': rec.amount_capital_index_bs,
                    'partner_id': rec.loan_application_ids.partner_id.id,
                    'amount_currency': 0
                })
                if not (rec.capital_index_initial_bolivianos == 0):
                    move_line.append(data)
                    amount = rec.amount_capital_index_bs + amount
                data = (0, 0, {
                    'account_id': rec.account_interest_base.id if rec.account_interest_base else rec.loan_application_ids.account_interest_base.id,
                    'debit': 0, 'credit': rec.amount_interest_bs,
                    'partner_id': rec.loan_application_ids.partner_id.id,
                    'amount_currency': 0
                })

                if not (rec.interest_base_bolivianos == 0):
                    move_line.append(data)
                    amount = rec.amount_interest_bs + amount
                data = (0, 0, {
                    'account_id': rec.account_res_social.id if rec.account_res_social else rec.loan_application_ids.account_interest_surplus.id,
                    'debit': 0, 'credit': rec.amount_res_social_bs,
                    'partner_id': rec.loan_application_ids.partner_id.id,
                    'amount_currency': 0
                })
                if not (rec.res_social_bolivianos == 0):
                    move_line.append(data)
                    amount = rec.amount_res_social_bs + amount
                data = (0, 0, {
                    'account_id': rec.account_percentage_mindef.id if rec.account_percentage_mindef else rec.loan_application_ids.account_percentage_mindef.id,
                    'debit': 0, 'credit': rec.amount_percentage_mindef_bs,
                    'partner_id': rec.loan_application_ids.partner_id.id,
                    'amount_currency': 0
                })
                if not (rec.percentage_amount_min_def_bolivianos == 0):
                    move_line.append(data)
                    amount = rec.amount_percentage_mindef_bs + amount
                data = (0, 0, {'account_id': rec.account_overage_days.id if rec.account_overage_days else rec.loan_application_ids.account_surpluy_days.id,
                               'debit': 0, 'credit': rec.amount_overage_days_bs,
                               'partner_id': rec.loan_application_ids.partner_id.id,
                               'amount_currency': 0
                               })
                if not (rec.interest_month_surpluy_bolivianos == 0):
                    move_line.append(data)
                    amount = rec.amount_overage_days_bs + amount
                data = (0, 0, {'account_id': rec.account_overage_amount.id if rec.account_overage_amount else rec.loan_application_ids.account_surpluy_days.id,
                               'debit': 0, 'credit': rec.amount_overage,
                               'partner_id': rec.loan_application_ids.partner_id.id,
                               'amount_currency': 0
                               })
                if not (rec.amount_overage == 0):
                    amount = rec.amount_overage + amount
                    move_line.append(data)
            if rec.amount_payment >= amount:
                validate = round(rec.amount_payment - amount, 2) if round(rec.amount_payment - amount, 2) > 0 else 0
                data = (0, 0, {'account_id': rec.account_overage_amount.id if rec.account_overage_amount else rec.loan_application_ids.account_surpluy_days.id,
                               'debit': 0, 'credit': validate,
                               'partner_id': rec.loan_application_ids.partner_id.id,
                               'amount_currency': 0
                               })


                if not (validate == 0):
                    move_line.append(data)
            move_vals = {
                "date": rec.date_payment,
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
            # record.amount_sum_bs = record.amount_sum * record.currency_id_dollar.inverse_rate
    @api.depends('amount_capital_index','amount_interest','amount_res_social','amount_percentage_mindef','amount_overage_days','amount_overage')
    def _sum_total(self):
        for record in self:
            record.amount_sum = record.amount_capital_index + record.amount_interest + record.amount_res_social + record.amount_percentage_mindef + record.amount_overage_days
            record.amount_sum_bs = record.amount_capital_index_bs + record.amount_interest_bs + record.amount_res_social_bs + record.amount_percentage_mindef_bs + record.amount_overage_days_bs
            if record.amount_income > record.amount_sum_bs:
                record.amount_overage = record.amount_income - record.amount_sum_bs

    @api.depends('flag_collect_guarantors', 'guarantor_one', 'guarantor_two')
    def _compute_guarantor_fields(self):
        for rec in self:
            if rec.flag_collect_guarantors:
                rec.amount_desc_guarantor_one = rec.amount_total_bs * 0.5 if rec.guarantor_one else 0
                rec.amount_desc_guarantor_two = rec.amount_total_bs * 0.5 if rec.guarantor_two else 0
            else:
                rec.amount_desc_guarantor_one = 0
                rec.amount_desc_guarantor_two = 0

    def create_report_excel(self):
        action = self.env["ir.actions.actions"]._for_xml_id("rod_cooperativa.action_loan_payment_excel")
        action['context'] = {
            'active_model': 'loan.payment',
            'active_ids': self.ids,
        }
        return action

    def confirm_ministry_defense_warrantor(self):
        for record in self:
            if record.state == 'draft' or record.state == 'scheduled':
                record.write({'state': 'ministry_defense_warrantor'})


    def not_discounted_loan(self):
        for rec in self:
            if rec.state == 'draft' or rec.state == 'scheduled':
                rec.state = 'not_discounted'
                rec.message_post(body="El prestamo ha sido marcado como NO DESCONTADO correctamente.")
                # Aquí podrías agregar lógica adicional si es necesario, como enviar notificaciones o actualizar otros registros.
            else:
                raise ValidationError('No se puede marcar como no descontado este pago.')

    def _get_mora_params(self):
        mora_interest = float(
            self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.mora_interest', default=0))
        grace_days = int(
            self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.days_grace', default=0))
        return grace_days,mora_interest

    def _compute_mora_core(self, as_of=None):
        self.ensure_one()
        if self.state == 'payment_mora' or self.state == 'scheduled_mora':
            as_of = self.date_end_mora or fields.Date.context_today(self.env) if as_of is None else as_of
            grace_days, mora_interest = self._get_mora_params()
            if mora_interest == 0:
                validation = 'El interés de mora no ha sido configurado. Por favor, configurelo en los parámetros del sistema.'
                raise ValidationError(validation)
            days_mora = (as_of - self.date_initial_mora).days
            overdue_capital = round(self.capital_index_initial * days_mora * (mora_interest/100),2)
        # Si la cuota ya está completamente pagada, no hay mora
            return days_mora, overdue_capital
        else:
            return 0, 0

    @api.depends('state', 'date_initial_mora', 'date_end_mora', 'capital_index_initial')
    def _calculate_mora(self):
        for rec in self:
            days, overdue_capital = rec._compute_mora_core()
            rec.amount_mora = overdue_capital
            rec.days_mora = days
            # rec.amount_total = round(rec.mount, 2) + round(rec.percentage_amount_min_def, 2) + round(
            #                     rec.interest_month_surpluy,
            #                     2) if rec.mount > 0 else rec.capital_index_initial + rec.interest_month_surpluy
            # if rec.state == 'payment_mora':
            #     rec.amount_total =  rec.amount_total + overdue_capital

    def action_pay_mora(self):
        for record in self:
            if record.state == 'not_discounted':
                record.write({'state': 'payment_mora'})

    @api.depends('amount_mora')
    def _onchange_amount_mora(self):
        for rec in self:
            rec.amount_mora_bs = rec.amount_mora * rec.currency_id_dollar.inverse_rate

    def _compute_base_total_now(self):
        self.ensure_one()
        if (self.amount_total or 0.0) > 0.0:
            return round(self.amount_total, 2)
        return (self.capital_index_initial or 0.0) + (self.interest_month_surpluy or 0.0)

    def _apply_mora_to_amount_total(self):
        self.ensure_one()
        days, overdue_capital = self._compute_mora_core()
        self.write({
            'amount_mora': overdue_capital,
            'days_mora': days,
        })
        base_total = self.amount_total_original or self._compute_base_total_now()
        new_total = base_total + (overdue_capital or 0.0)
        self.write({
            'amount_total_original': base_total,
            'amount_total': new_total,
            'amount_total_bs': new_total * self.currency_id_dollar.inverse_rate,
            'mora_applied': True,
        })

    def _unapply_mora_if_any(self):
        self.ensure_one()
        if self.mora_applied:
            base_total = self.amount_total_original or self._compute_base_total_now()
            self.write({
                'amount_mora': 0.0,
                'days_mora': 0,
                'amount_total': base_total,
                'amount_total_bs': base_total * self.currency_id_dollar.inverse_rate,
                'amount_total_original': 0.0,
                'mora_applied': False,
            })

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        # Fija el original a la creación si no viene
        if not rec.amount_total_original:
            rec.amount_total_original = rec._compute_base_total_now()
        return rec

    def write(self, vals):
        # Estados previos para detectar transición
        prev = {r.id: (r.state, r.mora_applied) for r in self}
        res = super().write(vals)

        if 'state' in vals:
            for rec in self:
                old_state, old_mora_applied = prev.get(rec.id, (None, False))
                # Si entra a payment_mora y aún no aplicamos
                if old_state != 'payment_mora' and rec.state in ['payment_mora','scheduled_mora']   and not rec.mora_applied:
                    rec._apply_mora_to_amount_total()
                    rec._onchange_amount_mora()
                # (Opcional) Si sale de payment_mora, revertir
                elif old_state == 'payment_mora' and rec.state != 'payment_mora' and rec.mora_applied:
                    rec._unapply_mora_if_any()
        return res

    def scheduled_mora(self):
        for record in self:
            if record.state == 'draft':
                # Validación: ambos campos deben tener valor
                if not record.date_initial_mora or not record.date_end_mora:
                    raise ValidationError(
                        "Debes completar las fechas de inicio y fin de mora antes de programar la mora."
                    )
                record.write({'state': 'scheduled_mora'})


    def update_amount_total_original(self):
        for rec in self:
            rec.amount_total_original = rec.amount_total



