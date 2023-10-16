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
        ('progress', 'En Proceso'),
        ('done', 'Concluido'),
        ('refinanced', 'Refinanciado'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='init', tracking=True)
    type_loan = fields.Selection([('regular','Regular'), ('emergency','Emergencia')], string='Tipo de prestamo')
    partner_id = fields.Many2one('res.partner', string='Socio solicitante', tracking=True)
    code_contact = fields.Char(string='Codigo de socio', related='partner_id.code_contact', store=True)
    category_partner = fields.Char(string='Grado', related='partner_id.category_partner_id.name', store=True)
    ci_partner = fields.Char(string='Carnet de identidad', related='partner_id.vat', store=True)
    letter_of_request = fields.Boolean(string='Carta de solicitud', tracking=True)
    contact_request = fields.Boolean(string='Solicitud de prestamo', tracking=True)
    last_copy_paid_slip = fields.Boolean(string='Ultima copia de boleta de pago', tracking=True)
    ci_photocopy = fields.Boolean(string='Fotocopia de CI', tracking=True)
    photocopy_military_ci = fields.Boolean(string='Fotocopia de Carnet militar',  tracking=True)
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
    #valores calculados para prestamos
    amount_loan_max = fields.Float(string='Monto maximo de prestamo (Bolivianos)',  compute='_compute_set_amount')
    amount_loan_max_dollars = fields.Float(string='Monto maximo de prestamo (dolares)', )
    # monthly_interest = fields.Float(string='Interes mensual %', compute='_compute_interest_monthly')
    # contingency_fund = fields.Float(string='Fondo de contingencia %', compute='_compute_interest_monthly')
    index_loan = fields.Float(string='Indice de prestamo ($)', compute='_compute_index_loan_fixed_fee')
    index_loan_bs = fields.Float(string='Indice de prestamo (Bs)')
    fixed_fee = fields.Float(string='Cuota fija ($)', compute='_compute_index_loan_fixed_fee')
    fixed_fee_bs = fields.Float(string='Cuota fija (Bs)', compute='_compute_index_loan_fixed_fee_bs')
    date_application = fields.Date(string='Fecha de solicitud', default=fields.Date.today())
    date_approval = fields.Date(string='Fecha de aprobacion')
    with_guarantor = fields.Selection(string='Tipo de prestamo regular', selection=[('loan_guarantor', 'Prestamo regular con garantes'), ('no_loan_guarantor', 'Prestamo regular sin garantes')])
    signature_recognition = fields.Boolean(string='Reconocimiento de firmas')
    contract = fields.Boolean(string='Contrato')
    surplus_days = fields.Integer(string='Dias excedentes', compute='_compute_surplus_days')
    interest_month_surpluy = fields.Float(string='Interes mensual excedente', compute='_compute_surplus_days', store=True)
    total_interest_month_surpluy = fields.Float(string='Total interes mensual excedente', compute='_compute_total_interest_month_surpluy', store=True)
    reason_loan = fields.Text(string='Motivo del prestamo')
    number_account = fields.Char(string='Numero de cuenta')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Moneda', related='company_id.currency_id')
    currency_id_dollar = fields.Many2one('res.currency', string='Moneda en Dólares', default=lambda self: self.env.ref('base.USD'))
    turn_name = fields.Char(string='Girar a', tracking=True)
    account_deposit = fields.Char(string='Cuenta de deposito', tracking=True)
    special_case = fields.Boolean(string='Caso especial', default=False)
    refinance_loan_id = fields.Many2one('loan.application', string='Prestamo anterior')
    amount_devolution = fields.Float(string='Monto de entregar')
    balance_capital = fields.Float(string='Saldo capital', compute='_compute_balance_capital', store=True)
    balance_total_interest_month = fields.Float(string='Saldo total interes mensual', compute='_compute_balance_capital', store=True)
    # amount_min_def = fields.Float(string='Min. Defensa %', currency_field='company_currency_id',compute='_compute_min_def')
    @api.depends('date_approval')
    def _compute_surplus_days(self):
        for record in self:
            if record.date_approval:
                last_day = calendar.monthrange(record.date_approval.year, record.date_approval.month)[1]
                point_day = last_day - record.date_approval.day
                record.surplus_days = point_day
                calculte_interest = record.amount_loan_dollars * (record.monthly_interest / 100)
                record.interest_month_surpluy = (calculte_interest / last_day) * point_day / record.months_quantity
            else:
                record.surplus_days = 0
                record.interest_month_surpluy = 0
    def _compute_min_def(self):
        self.amount_min_def = self.fixed_fee * round(float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_min_def')),4)

    @api.onchange('amount_loan_dollars')
    def _onchange_amount_loan_dollars(self):
        self.fixed_fee = self.amount_loan_dollars * self.index_loan

    def _compute_set_dollar(self):
        dollar = self.env['res.currency'].search([('name','=','USD')], limit=1)
        return round(dollar.inverse_rate,2)
    def _default_interest_monthly(self):
        return float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest'))

    def _default_contingency_fund(self):
        return float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.contingency_fund'))
    @api.onchange('months_quantity')
    def _compute_index_loan_fixed_fee(self):
        try:
            interest = (self.monthly_interest + self.contingency_fund)/100
            index_quantity = (1-(1+interest)**(-self.months_quantity))
            self.index_loan = interest/index_quantity if index_quantity != 0 else 0
            self.fixed_fee = self.amount_loan_dollars * self.index_loan
        except:
            self.index_loan = 0
    def button_value_dolar(self):
        dollar = self.env['res.currency'].search([('name','=','USD')], limit=1)
        self.value_dolar = round(dollar.inverse_rate,2)

    #Valores por default y constantes
    value_dolar = fields.Float(default=_compute_set_dollar)
    contingency_fund = fields.Float(string='Fondo de contingencia %', default= lambda self: float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.contingency_fund')))
    monthly_interest = fields.Float(string='Indice de prestamo por mes %', default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest')))
    amount_min_def = fields.Float(string='Min. Defensa %', default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_min_def')), digits=(6, 3))
    commission_min_def = fields.Float(string='Comision Min. Defensa %', default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_commission_min_def')), digits=(6, 3))
    #Relacion a los pagos
    loan_payment_ids = fields.One2many('loan.payment', 'loan_application_ids', string='Pagos')

    value_partner_total_contribution = fields.Float(string='Total aportes', compute='compute_total_contribution')

    def compute_total_contribution(self):
        value = self.env['partner.payroll'].search([('partner_id','=',self.partner_id.id)])
        self.value_partner_total_contribution = round(value.contribution_total,2)


    #Conversion dolares a boliviamos
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
            rec.date_approval = fields.Date.today()
            for i in range(1, rec.months_quantity+1):
                commission_min_def = float(
                    self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.commission_min_def'))
                amount_commission = (commission_min_def / 100) * rec.fixed_fee
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
                        date_payment = date_payment.replace(day=1)
                        date_payment = date_payment.replace(month=date_payment.month + 1)
                else:
                    capital_init = rec.loan_payment_ids[i-2].balance_capital
                    date_payment = rec.loan_payment_ids[i-2].date
                    date_payment = date_payment + relativedelta(months=+1)
                    date_payment = date_payment.replace(day=1)

                self.env['loan.payment'].create({
                    'name': 'Cuota '+str(i),
                    'date': date_payment,
                    'capital_initial': capital_init,
                    'mount': rec.fixed_fee,
                    'loan_application_ids': rec.id,
                    'percentage_amount_min_def': percentage_amount_min_def,
                    'commission_min_def': amount_commission,
                    'state': 'draft',
                })
            self.progress()
    def verification_pass(self):
        self.state = 'verificate'
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
                self.message_post(body="Se agrego al garante "+name_guarantor)
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

    #Asignar datos del socio, cantidad de meses
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
                'default_capital_rest': self.balance_capital,
                'default_interest_days_rest': self.balance_total_interest_month,
                'default_quantity_month_initial': self.months_quantity,
            },
        }
    @api.depends('loan_payment_ids.state')
    def _compute_balance_capital(self):
        for rec in self:
            if len(rec.loan_payment_ids.filtered(lambda x:x.state == 'transfer')) > 0:
                rec.balance_capital = rec.loan_payment_ids.filtered(lambda x:x.state == 'transfer')[-1].balance_capital
                rec.balance_total_interest_month = rec.total_interest_month_surpluy - sum(rec.loan_payment_ids.filtered(lambda x:x.state == 'transfer').mapped('interest_month_surpluy'))
            else:
                rec.balance_capital = rec.amount_loan_dollars
                rec.balance_total_interest_month = rec.total_interest_month_surpluy

    @api.depends('interest_month_surpluy','months_quantity')
    def _compute_total_interest_month_surpluy(self):
        for rec in self:
            rec.total_interest_month_surpluy = rec.interest_month_surpluy * rec.months_quantity

    @api.onchange('guarantor_one','guarantor_two' )
    def _onchange_guarantor_one(self):
        if self.guarantor_one and self.guarantor_two:
            if self.guarantor_one == self.guarantor_two:
                raise ValidationError('No puede seleccionar el mismo garante')
        if self.guarantor_one == self.partner_id:
            raise ValidationError('No puede seleccionar el mismo socio como garante')
        if self.guarantor_one.guarantor_count == 3:
            raise ValidationError('El garante ya tiene 3 prestamos')
        if self.guarantor_two.guarantor_count == 3:
            raise ValidationError('El garante ya tiene 3 prestamos')

