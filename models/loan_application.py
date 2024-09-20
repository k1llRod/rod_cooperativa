import calendar
from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from collections import OrderedDict


class LoanApplication(models.Model):
    _name = 'loan.application'
    _description = 'Solicitud de prestamo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _columns = {
        'partner_id': fields.Many2one('res.partner', string='Socio solicitante', required=True)
    },

    name = fields.Char(string='Código de solicitud', tracking=True)
    state = fields.Selection([
        ('init', 'Inicio'),
        ('verificate', 'Verificación'),
        ('approval', 'Aprobar'),
        ('progress', 'En Proceso'),
        ('liquidation_process', 'Proceso de liquidación'),
        ('done', 'Concluido'),
        ('refinanced', 'Refinanciado'),
        ('expansion', 'Ampliación'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='init', tracking=True)
    type_loan = fields.Selection([('regular', 'Regular'), ('emergency', 'Emergencia')], string='Tipo de prestamo')
    partner_id = fields.Many2one('res.partner', string='Socio solicitante', tracking=True)
    code_contact = fields.Char(string='Codigo de socio', related='partner_id.code_contact', store=True)
    category_partner = fields.Char(string='Grado', related='partner_id.category_partner_id.name', store=True)
    ci_partner = fields.Char(string='Carnet de identidad', related='partner_id.vat', store=True)
    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('letter_a', 'Letra "A" de disponibilidad'),
                                                 ('passive_reserve_a', 'Reserva pasivo "A"'),
                                                 ('passive_reserve_b', 'Reserva pasivo "B"'),
                                                 ('leave', 'Baja')], string='Tipo de asociado',
                                                related='partner_id.partner_status_especific', store=True)
    letter_of_request = fields.Boolean(string='Carta de solicitud', tracking=True)
    contact_request = fields.Boolean(string='Solicitud de prestamo', tracking=True)
    last_copy_paid_slip = fields.Boolean(string='Ultima copia de boleta de pago', tracking=True)
    ci_photocopy = fields.Boolean(string='Fotocopia de CI', tracking=True)
    photocopy_military_ci = fields.Boolean(string='Fotocopia de Carnet militar', tracking=True)
    # photocopy_payment_slip = fields.Boolean(string='Fotocopia de boleta de pago', tracking=True)
    # category_loan = fields.Many2one('type.loan', string='Categoria', tracking=True)
    guarantor_one = fields.Many2one('res.partner', string='Garante 1', tracking=True)
    guarantor_two = fields.Many2one('res.partner', string='Garante 2', tracking=True)
    code_garantor_one = fields.Char(string='Codigo de garante 1', related='guarantor_one.code_contact', store=True)
    code_garantor_two = fields.Char(string='Codigo de garante 2', related='guarantor_two.code_contact', store=True)
    code_loan = fields.Char(string='Codigo de prestamo')
    amount_loan = fields.Float(string='Monto de prestamo (Bolivianos)', compute='_compute_change_dollars_bolivian')
    amount_loan_dollars = fields.Float(string='Monto de prestamo (dolares)')
    months_quantity = fields.Integer(string='Cantidad de meses', tracking=True)
    # valores calculados para prestamos
    amount_loan_max = fields.Float(string='Monto maximo de prestamo (Bolivianos)', compute='_compute_set_amount')
    amount_loan_max_dollars = fields.Float(string='Monto maximo de prestamo (dolares)', )
    # monthly_interest = fields.Float(string='Interes mensual %', compute='_compute_interest_monthly')
    # contingency_fund = fields.Float(string='Fondo de contingencia %', compute='_compute_interest_monthly')
    index_loan = fields.Float(string='Indice de prestamo ($)', compute='_compute_index_loan_fixed_fee')
    index_loan_bs = fields.Float(string='Indice de prestamo (Bs)')
    fixed_fee = fields.Float(string='Cuota fija ($)', compute='_compute_index_loan_fixed_fee')
    fixed_fee_bs = fields.Float(string='Cuota fija (Bs)', compute='_compute_index_loan_fixed_fee_bs')
    date_application = fields.Date(string='Fecha de solicitud', default=fields.Date.today())
    date_approval = fields.Date(string='Fecha de aprobacion')
    with_guarantor = fields.Selection(string='Tipo de prestamo regular',
                                      selection=[('loan_guarantor', 'Prestamo regular con garantes'),
                                                 ('no_loan_guarantor', 'Prestamo regular sin garantes'),
                                                 ('mortgage', 'Prestamo hipotecario')])
    signature_recognition = fields.Boolean(string='Reconocimiento de firmas')
    contract = fields.Boolean(string='Contrato')
    surplus_days = fields.Integer(string='Dias excedentes')
    interest_month_surpluy = fields.Float(string='Interes dias excedente')
    total_interest_month_surpluy = fields.Float(string='Total interes mensual excedente',
                                                compute='_compute_total_interest_month_surpluy', store=True)
    reason_loan = fields.Text(string='Motivo del prestamo')
    number_account = fields.Char(string='Numero de cuenta')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Moneda', related='company_id.currency_id')
    currency_id_dollar = fields.Many2one('res.currency', string='Moneda en Dólares',
                                         default=lambda self: self.env.ref('base.USD'))
    turn_name = fields.Char(string='Girar a', tracking=True)
    account_deposit = fields.Char(string='Cuenta de deposito', tracking=True)
    special_case = fields.Boolean(string='Caso especial', default=False)
    refinance_loan_id = fields.Many2one('loan.application', string='Prestamo anterior')
    amount_devolution = fields.Float(string='Monto a entregar', digits=(6, 2), store=True)
    amount_devolution_bs = fields.Float(string="Monto a entregar Bs.", digits=(6, 2), store=True)
    balance_capital = fields.Float(string='Saldo capital', compute='_compute_balance_capital', store=True)
    balance_total_interest_month = fields.Float(string='Saldo total interes mensual',
                                                compute='_compute_balance_capital', digits=(6, 2), store=True)
    balance_total_interest_month_auxiliar = fields.Float(string='Saldo total interes mensual auxiliar')
    balance_capital_auxiliar = fields.Float(string='Saldo capital auxiliar')
    # amount_min_def = fields.Float(string='Min. Defensa %', currency_field='company_currency_id',compute='_compute_min_def')
    pending_payment = fields.Integer(string='Pendiente de pago', compute='_compute_pending_payment')
    alert_pending_payment = fields.Boolean(string='Alerta de pago', compute='_compute_pending_payment')
    pay_slip_balance = fields.Float(string='Saldo boleta de pago')
    missing_payments = fields.Integer(string='Pagos pendientes', compute='_compute_missing_payments')
    total_payments_confirm = fields.Integer(string='Total pagos confirmados', compute='_compute_missing_payments')

    loan_historical_coaa = fields.Float(string='Prestamos historico COAA')
    journal_id = fields.Many2one('account.journal', string='Diario Egreso')

    account_loan_id = fields.Many2one('account.account', string='Cuenta de prestamo')
    account_egreso_id = fields.Many2one('account.account', string='Cuenta de egreso')
    accounting_entry_id = fields.Many2one('account.move', string='Asiento contable egreso')

    account_monto_refinanciamiento = fields.Many2one('account.account', string="Cuenta Saldo anterior")
    account_monto_meses_interes = fields.Many2one('account.account', string="Cuenta Saldo dias excedentes")

    journal_income_id = fields.Many2one('account.journal', string='Diario Ingreso')
    account_income = fields.Many2one('account.account', string='Cuenta de ingreso')
    account_capital_index_id = fields.Many2one('account.account', string='Cuenta de capital')
    account_interest_base = fields.Many2one('account.account', string='Interes 0.7%')
    account_interest_surplus = fields.Many2one('account.account', string='Fondo por Contingencia')
    account_percentage_mindef = fields.Many2one('account.account', string='Porcentaje Min. Defensa')
    account_surpluy_days = fields.Many2one('account.account', string='Interes dias excedentes')

    finalized_loan_id = fields.One2many('finalized.loan', 'loan_application_id', string='Prestamos finalizados')
    @api.depends('loan_payment_ids')
    def _compute_pending_payment(self):
        for rec in self:
            if rec.state == 'progress':
                rec.pending_payment = len(rec.loan_payment_ids.filtered(lambda x: x.state == 'draft'))
                if rec.pending_payment > 0:
                    rec.alert_pending_payment = True
                else:
                    rec.alert_pending_payment = False
            if len(rec.loan_payment_ids) > 0:
                rec.pending_payment = len(rec.loan_payment_ids.filtered(lambda x: x.state == 'draft'))
                if rec.pending_payment > 0:
                    rec.alert_pending_payment = True
                else:
                    rec.alert_pending_payment = False
            else:
                rec.pending_payment = 0
                rec.alert_pending_payment = False

    @api.onchange('date_approval')
    def _compute_surplus_days(self):
        for record in self:
            if record.date_approval:
                if record.with_guarantor == 'loan_guarantor' or record.with_guarantor == 'no_loan_guarantor':
                    last_day = calendar.monthrange(record.date_approval.year, record.date_approval.month)[1]
                    point_day = last_day - record.date_approval.day
                    record.surplus_days = point_day
                    calculte_interest = record.amount_loan_dollars * (
                            (record.monthly_interest + record.contingency_fund) / 100)
                    record.interest_month_surpluy = (calculte_interest / last_day) * (
                            point_day / record.months_quantity)
                else:
                    last_day = calendar.monthrange(record.date_approval.year, record.date_approval.month)[1]
                    point_day = last_day - record.date_approval.day
                    record.surplus_days = point_day
                    calculte_interest = record.amount_loan_dollars * (
                            (record.monthly_interest_mortgage + record.mortgage_loan) / 100)
                    record.interest_month_surpluy = (calculte_interest / last_day) * (
                            point_day / record.months_quantity)
            else:
                record.surplus_days = 0
                record.interest_month_surpluy = 0

    def _compute_min_def(self):
        self.amount_min_def = self.fixed_fee * round(
            float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_min_def')), 4)

    @api.onchange('amount_loan_dollars')
    def _onchange_amount_loan_dollars(self):
        self.fixed_fee = self.amount_loan_dollars * self.index_loan
        self.pay_slip_balance = self.fixed_fee_bs * (100 / 40)

    def _compute_set_dollar(self):
        dollar = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        return round(dollar.inverse_rate, 2)

    def _default_interest_monthly(self):
        return float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest'))

    def _default_contingency_fund(self):
        return float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.contingency_fund'))

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

    def button_value_dolar(self):
        dollar = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        self.value_dolar = round(dollar.inverse_rate, 2)

    # Valores por default y constantes
    value_dolar = fields.Float(default=_compute_set_dollar)
    contingency_fund = fields.Float(string='Fondo de contingencia %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.contingency_fund')))
    monthly_interest = fields.Float(string='Indice de prestamo por mes %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest')))
    amount_min_def = fields.Float(string='Min. Defensa %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_min_def')), digits=(6, 3))
    commission_min_def = fields.Float(string='Comision Min. Defensa %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_commission_min_def')),
                                      digits=(6, 3))
    mortgage_loan = fields.Float(string='Prestamo hipotecario %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.mortgage_loan')))
    monthly_interest_mortgage = fields.Float(string='Indice de prestamo hipotecario por mes %',
                                             default=lambda self: float(
                                                 self.env['ir.config_parameter'].sudo().get_param(
                                                     'rod_cooperativa.monthly_interest_mortgage')), digits=(6, 3))
    # Relacion a los pagos
    loan_payment_ids = fields.One2many('loan.payment', 'loan_application_ids', string='Pagos')

    value_partner_total_contribution = fields.Float(string='Total aportes', compute='compute_total_contribution')

    interest_day_rest = fields.Float(string='Interes dias restantes', digits=(6, 2))
    interest_day_rest_bs = fields.Float(string='Interes dias restantes Bs.', digits=(6, 2))

    def compute_total_contribution(self):
        value = self.env['partner.payroll'].search([('partner_id', '=', self.partner_id.id)])
        self.value_partner_total_contribution = round(value.contribution_total, 2)

    # Conversion dolares a boliviamos
    @api.depends('amount_loan_dollars')
    def _compute_change_dollars_bolivian(self):
        for rec in self:
            rec.amount_loan = rec.amount_loan_dollars * rec.value_dolar

    def approve_loan(self):
        for rec in self:
            if rec.letter_of_request == False: raise ValidationError('Falta carta de solicitud')
            if rec.contact_request == False: raise ValidationError('Falta solicitud de prestamo')
            if rec.last_copy_paid_slip == False: raise ValidationError('Falta ultima copia de boleta de pago')
            # if rec.ci_fothocopy == False: raise ValidationError('Falta fotocopia de CI')
            # if rec.photocopy_military_ci == False: raise ValidationError('Falta fotocopia de carnet militar')
            # rec.date_approval = fields.Date.today()
            if rec.date_approval < rec.date_application: raise ValidationError(
                'La FECHA DE APROBACION no puede ser anterior a la FECHA DE SOLICITUD')
            for i in range(1, rec.months_quantity + 1):
                commission_min_def = float(
                    self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.commission_min_def'))
                # amount_commission = (commission_min_def / 100) * rec.amount_total_bs
                coa_commission = (1.25 / 100) * rec.fixed_fee
                percentage_amount_min_def = rec.fixed_fee * rec.amount_min_def
                if len(rec.loan_payment_ids) == 0:
                    capital_init = rec.amount_loan_dollars
                    # date_payment = datetime.today()
                    date_payment = rec.date_approval
                    if rec.special_case == True:
                        if date_payment.day >= 1 and date_payment.day <= 15:
                            date_payment = rec.date_approval
                        else:
                            raise ValidationError('La solicitud de prestamo esta fuera de rango')
                    else:
                        date_pivot = date_payment
                        date_payment = date_payment.replace(day=1)
                        date_payment = date_payment.replace(
                            month=date_payment.month + 1 if date_pivot.month < 12 else 1)
                        date_payment = date_payment.replace(
                            year=date_payment.year + 1 if date_pivot.month == 12 else date_payment.year)
                else:
                    capital_init = rec.loan_payment_ids[i - 2].balance_capital
                    date_payment = rec.loan_payment_ids[i - 2].date
                    date_payment = date_payment + relativedelta(months=+1)
                    date_payment = date_payment.replace(day=1)

                self.env['loan.payment'].create({
                    'name': 'Cuota ' + str(i),
                    'date': date_payment,
                    'capital_initial': capital_init,
                    'mount': rec.fixed_fee,
                    'loan_application_ids': rec.id,
                    'percentage_amount_min_def': percentage_amount_min_def,
                    'interest_month_surpluy': rec.interest_month_surpluy,
                    # 'commission_min_def': amount_commission,
                    'coa_commission': coa_commission,
                    'state': 'draft',
                })
            self.progress()

    def create_activity(self, activity_type, summary, user_id, note, deadline):
        if activity_type:
            self.env['mail.activity'].create({
                'activity_type_id': activity_type,  # Tipo de actividad (llamada, correo, etc.)
                'res_id': self.id,  # ID del registro al que está asociada la actividad
                'res_model_id': self.env['ir.model']._get(self._name).id,  # Modelo relacionado
                'user_id': user_id,  # ID del usuario asignado a la actividad
                'summary': summary,  # Resumen de la actividad
                'note': note,  # Nota o descripción detallada de la actividad
                'date_deadline': deadline,  # Fecha límite para completar la actividad
            })

    def verification_pass(self):
        for rec in self:
            if rec.with_guarantor == False:
                raise ValidationError('Falta asignar tipo de prestamo regular')
            if not rec.months_quantity > 0:
                raise ValidationError('La cantidad de meses no puede ser menor o igual a 0')
            if not rec.amount_loan_dollars > 0:
                raise ValidationError('El monto del prestamo no puede ser menor o igual a 0')
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record_url = f"{base_url}/web#id={self.id}&model={self._name}&view_type=form"

            message = f"Se le asigno el siguiente prestamo para revision: " \
                      f"<a href='{record_url}'>{rec.name}</a>"
            group = self.env.ref('rod_cooperativa.group_rod_cooperativa_administrator')
            # group = self.env.ref('rod_cooperativa.group_rod_cooperativa_administrator')
            users = group.users
            self.message_subscribe(partner_ids=users.mapped('partner_id').ids)
            # if group:
            #     users = group.users
            #     partner_ids = [user.partner_id.id for user in users]
            #     if partner_ids:
            #         rec.message_post(body=message,
            #                          partner_ids=partner_ids)
            activity_type  = self.env['mail.activity.type'].search([('name', '=', 'Prestamo')], limit=1)
            activity_type_xml = self.env.ref('mail.mail_activity_data_todo')
            for record in users:
                rec.create_activity(
                    activity_type_xml.id,  # Tipo de actividad
                    'Revision de proceso',  # Resumen
                    record.id,  # ID del usuario asignado (puede ser cualquier usuario)
                    'Revisar el siguiente documento para continuar con el proceso.',  # Nota
                    fields.Date.today()  # Fecha límite en 3 días
                )
            rec.state = 'verificate'

    def progress(self):
        self.state = 'progress'
        # self.date_approval = fields.Date.today()

    def return_application(self):
        self.state = 'init'

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('loan.application')
        vals['name'] = name
        if vals.get('guarantor', False):
            for rec in vals.get('guarantor')[0][0]:
                name_guarantor = self.env['res.partner'].browse(rec).name
                self.message_post(body="Se agrego al garante " + name_guarantor)
        res = super(LoanApplication, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('guarantor', False):
            message = '<ul>'
            for rec in vals.get('guarantor')[0][2]:
                name_guarantor = self.env['res.partner'].browse(rec).name
                message += f"<li>{name_guarantor}</li>"
            message += '</ul>'
            self.message_post(body="Garantes asignados: " + message)
        res = super(LoanApplication, self).write(vals)
        return res

    @api.onchange('type_loan')
    def _onchage_type_loan(self):
        if self.type_loan == 'emergency':
            # self.guarantor = False
            self.months_quantity = 0
            self.with_guarantor = ''
            self.guarantor_one = False
            self.guarantor_two = False

    # Asignar datos del socio, cantidad de meses
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            rec.months_quantity = rec.partner_id.category_partner_id.months
            rec.amount_loan_dollars = rec.partner_id.category_partner_id.limit_amount_dollars

    @api.depends('fixed_fee')
    def _compute_index_loan_fixed_fee_bs(self):
        for rec in self:
            rec.fixed_fee_bs = rec.fixed_fee * rec.value_dolar

    def return_draft(self):
        self.state = 'init'

    @api.onchange('with_guarantor')
    def _onchange_with_guarantor(self):
        if self.with_guarantor == 'no_loan_guarantor':
            self.signature_recognition = False
            self.guarantor_one = False
            self.guarantor_two = False

    def refinance(self):
        id = self.id
        auxiliar = self.balance_total_interest_month
        auxiliar_balance = self.balance_capital
        if self.balance_total_interest_month_auxiliar > 0:
            auxiliar = self.balance_total_interest_month_auxiliar
        if self.balance_capital_auxiliar > 0:
            auxiliar_balance = self.balance_capital_auxiliar
        return {
            'name': 'Formulario de refinanciamiento',
            'type': 'ir.actions.act_window',
            'res_model': 'form.refinance',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_capital_initial': self.amount_loan_dollars,
                'default_data_loan_id': id,
                'default_capital_rest': auxiliar_balance,
                'default_interest_days_rest': auxiliar,
                'default_quantity_month_initial': self.months_quantity,
            },
        }

    @api.depends('loan_payment_ids.state')
    def _compute_balance_capital(self):
        for rec in self:
            if len(rec.loan_payment_ids.filtered(lambda x: x.state == 'transfer' or x.state == 'ministry_defense' or
                                                           x.state == 'debt_settlement_deposit' or x.state == 'debt_settlement_mindef')) > 0:
                rec.balance_capital = \
                    rec.loan_payment_ids.filtered(lambda x: x.state == 'transfer' or x.state == 'ministry_defense' or
                                                            x.state == 'debt_settlement_deposit' or x.state == 'debt_settlement_mindef')[
                        -1].balance_capital
                rec.balance_total_interest_month = rec.total_interest_month_surpluy - sum(
                    rec.loan_payment_ids.filtered(
                        lambda
                            x: x.state == 'transfer' or x.state == 'ministry_defense' or x.state == 'debt_settlement_deposit' or x.state == 'debt_settlement_mindef').mapped(
                        'interest_month_surpluy'))
            else:
                rec.balance_capital = rec.amount_loan_dollars
                rec.balance_total_interest_month = rec.total_interest_month_surpluy

    @api.depends('interest_month_surpluy', 'months_quantity')
    def _compute_total_interest_month_surpluy(self):
        for rec in self:
            rec.total_interest_month_surpluy = rec.interest_month_surpluy * rec.months_quantity

    @api.onchange('guarantor_one', 'guarantor_two')
    def _onchange_guarantor_one(self):
        if self.guarantor_one and self.guarantor_two:
            if self.guarantor_one == self.guarantor_two:
                raise ValidationError('No puede seleccionar el mismo garante')
        if self.guarantor_one == self.partner_id:
            raise ValidationError('No puede seleccionar el mismo socio como garante')
        if self.guarantor_one.guarantor_count == 3:
            raise ValidationError('El garante,' + self.guarantor_one.name + ', ya tiene 3 prestamos')

    @api.onchange('guarantor_two')
    def _onchange_guarantor_two(self):
        if self.guarantor_one and self.guarantor_two:
            if self.guarantor_one == self.guarantor_two:
                raise ValidationError('No puede seleccionar el mismo garante')
        if self.guarantor_two == self.partner_id:
            raise ValidationError('No puede seleccionar el mismo socio como garante')
        if self.guarantor_two.guarantor_count == 3:
            raise ValidationError('El garante,' + self.guarantor_two.name + ', ya tiene 3 prestamos')

    def reset_payroll(self):
        for rec in self:
            rec.loan_payment_ids.unlink()
            rec.state = 'init'

    def return_approval(self):
        for rec in self:
            rec.state = 'approval'

    def return_progress(self):
        for rec in self:
            rec.state = 'progress'

    def import_loan(self):
        return {
            'name': 'Conciliar pagos de prestamos',
            'type': 'ir.actions.act_window',
            'res_model': 'reconcile.loan',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }

    def massive_approve_loan(self):
        for r in self:
            r._compute_index_loan_fixed_fee()
            r.approve_loan()

    def massive_verification_pass(self):
        self.state = 'verificate'

    @api.depends('loan_payment_ids')
    def _compute_missing_payments(self):
        for rec in self:
            rec.missing_payments = len(rec.loan_payment_ids.filtered(lambda x: x.state == 'draft'))
            # date_init = rec.loan_payment_ids.filtered(lambda x:x.name == 'Cuota 1').date
            date_end = datetime.now().date()
            count_payment_confirm = len(
                rec.loan_payment_ids.filtered(lambda x: x.state == 'transfer' or x.state == 'ministry_defense'))
            count_payment = len(rec.loan_payment_ids.filtered(lambda x: x.date <= date_end))
            # rec.missing_payments = (date_end.year - date_init.year) * 12 + date_end.month - date_init.month
            rec.missing_payments = count_payment - count_payment_confirm
            rec.total_payments_confirm = count_payment
            # rec.amount_devolution_bs = rec.amount_devolution * rec.value_dolar
            # rec.interest_day_rest_bs = rec.interest_day_rest * rec.value_dolar

    @api.onchange('interest_day_rest')
    def _onchange_interest_day_rest(self):
        self.interest_day_rest_bs = self.interest_day_rest * self.value_dolar

    @api.onchange('amount_devolution')
    def _onchange_amount_devolution(self):
        self.amount_devolution_bs = self.amount_devolution * self.value_dolar
    def action_wizard_report_xlsx(self):
        return {
            'name': 'Generar reportes Excel',
            'type': 'ir.actions.act_window',
            'res_model': 'report.form.xlsx',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }

    def approval_state(self):
        for rec in self:
            group = rec.env.ref('rod_cooperativa.group_rod_cooperativa_operator')
            # group = self.env.ref('rod_cooperativa.group_rod_cooperativa_administrator')
            users = group.users
            activity_type_xml = rec.env.ref('mail.mail_activity_data_todo')
            for record in users:
                rec.create_activity(
                    activity_type_xml.id,  # Tipo de actividad
                    'Revision de proceso para aprobacion',  # Resumen
                    record.id,  # ID del usuario asignado (puede ser cualquier usuario)
                    'Revisar el siguiente documento para continuar con el proceso.',  # Nota
                    fields.Date.today()  # Fecha límite en 3 días
                )
            rec.state = 'approval'

    def approve_egreso(self):
        val = []
        for record in self:
            data = (0, 0, {'account_id': record.account_loan_id.id,
                           'debit': record.amount_loan, 'credit': 0,
                           'partner_id': record.partner_id.id,
                           'amount_currency': 0
                           })
            val.append(data)
            if record.loan_historical_coaa > 0:
                amount = record.amount_loan - record.loan_historical_coaa
                # data = (0, 0, {'account_id': record.account_loan_id.id,
                #                          'debit': record.amount_loan, 'credit': 0, 'partner_id': record.partner_id.id,
                #                          'amount_currency': 0
                #                          })
                # val.append(data)
                data = (0, 0, {'account_id': record.account_loan_id.id,
                               'debit': 0, 'credit': record.loan_historical_coaa, 'partner_id': record.partner_id.id,
                               'name': 'COAA',
                               'amount_currency': 0
                               })
                val.append(data)
                data = (0, 0, {'account_id': record.account_loan_id.id,
                               'debit': 0, 'credit': amount, 'partner_id': record.partner_id.id,
                               'name': 'BENEFICIARIO',
                               'amount_currency': 0
                               })
                val.append(data)
            else:
                if record.refinance_loan_id:
                    amount_amortizacion = record.amount_loan - record.amount_devolution_bs - record.interest_day_rest_bs
                    amount_loan = record.amount_loan - (amount_amortizacion + record.interest_day_rest_bs)

                    data = (0, 0, {'account_id': record.account_egreso_id.id,
                                   'debit': 0, 'credit': amount_loan,
                                   # 'partner_id': record.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    data = (0, 0, {'account_id': record.account_monto_refinanciamiento.id,
                                   'debit': 0, 'credit': amount_amortizacion,
                                   # 'partner_id': record.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    data = (0, 0, {'account_id': record.account_monto_meses_interes.id,
                                   'debit': 0, 'credit': record.interest_day_rest_bs,
                                   # 'partner_id': record.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                else:
                    data = (0, 0, {'account_id': record.account_egreso_id.id,
                                   'debit': 0, 'credit': record.amount_loan,
                                   # 'partner_id': record.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
            if record.with_guarantor == 'loan_guarantor':
                glosa = "P/CONTAB. PREST. AMORT." + " " + record.partner_id.category_partner_id.code_loan + " " + record.partner_id.name + " COD: " + record.partner_id.code_contact + " PREST $US " + str(record.amount_loan_dollars) + " INT " + str(round(record.monthly_interest,2))+"% " + "F.CONTIGENCIA: " + str(round(record.contingency_fund,2)) + "% PLAZO: " + str(record.months_quantity) + " MESES EXCED " + str(record.surplus_days) + " DIAS "+ "CUOTA FIJA $US: "+ str(round(record.loan_payment_ids[0].amount_total,2)) +" GARANTES " + record.guarantor_one.category_partner_id.code_loan + " " +record.guarantor_one.name + " "+ record.guarantor_two.category_partner_id.code_loan + " " + record.guarantor_two.name
            else:
                glosa = "P/CONTAB. PREST. AMORT." + " " + record.partner_id.category_partner_id.code_loan + " " + record.partner_id.name + " COD: " + record.partner_id.code_contact + " PREST $US " + str(
                    record.amount_loan_dollars) + " INT " + str(
                    round(record.monthly_interest, 2)) + "% " + "F.CONTIGENCIA: " + str(
                    round(record.contingency_fund, 2)) + "% PLAZO: " + str(
                    record.months_quantity) + " MESES EXCED " + str(
                    record.surplus_days) + " DIAS " + "CUOTA FIJA $US: " + str(round(record.loan_payment_ids[0].amount_total,2))
            move_vals = {
                "date": record.date_approval,
                "journal_id": record.journal_id.id,
                "ref": "PRESTAMOS ASIGNADO AL ASOCIADO" + " " + record.partner_id.name + " EN LA FECHA " + str(
                    record.date_approval),
                # "company_id": payment.company_id.id,
                # "name": "name test",
                "glosa": glosa,
                "state": "draft",
                "line_ids": val,
            }
            account_move_id = record.env['account.move'].create(move_vals)
            record.accounting_entry_id = account_move_id.id
            account_move_id.loan_application_id = record.id
        return {
            'name': 'Pagos de planilla',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': account_move_id.id,
            'views': [(False, 'form')],
        }

    def update_loan(self):
        for record in self:
            for r in record.loan_payment_ids:
                r.commission_min_def = r.mount * 0.0025
                r.coa_commission_bs = r.coa_commission * 6.96

    def finalized_loan(self):
        if self.state != 'progress':
            raise ValidationError('No se puede liquidar este prestamo.')
        context = {
            'default_loan_application_id': self.id,
            'default_amount_loan_dollars_initial': self.amount_loan_dollars,
            'default_amount_loan_initial': self.amount_loan,
            'default_month_quantity_initial': self.months_quantity,
            'default_payment_count': self.total_payments_confirm,
            'default_date_application': self.date_application,
            'default_date_approval': self.date_approval,
            'default_balance_capital': self.balance_capital if self.balance_capital != 0 else self.balance_capital_auxiliar,
            'default_balance_total_interest_month': self.balance_total_interest_month if self.balance_total_interest_month != 0 else self.balance_total_interest_month_auxiliar,

        }
        return {
            'name': 'Pago de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'form.finalized.loan',
            'view_mode': 'form',
            'view_type': 'form',
            'context': context,
            'target': 'new',
        }