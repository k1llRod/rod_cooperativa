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
        ('cancel', 'Cancelado')
    ], string='Estado', default='init')
    type_loan = fields.Selection([('regular','Regular'), ('emergency','Emergencia')], string='Tipo de prestamo')
    partner_id = fields.Many2one('res.partner', string='Socio solicitante', tracking=True)
    category_partner = fields.Char(string='Categoria de socio', related='partner_id.category_partner_id.name', store=True)
    ci_partner = fields.Char(string='Carnet de identidad', related='partner_id.vat', store=True)
    letter_of_request = fields.Boolean(string='Carta de solicitud', tracking=True)
    contact_request = fields.Boolean(string='Solicitud de prestamo', tracking=True)
    last_copy_paid_slip = fields.Boolean(string='Ultima copia de boleta de pago', tracking=True)
    # ci_photocopy = fields.Boolean(string='Fotocopia de CI', tracking=True)
    # photocopy_military_ci = fields.Boolean(string='Fotocopia de Carnet militar',  tracking=True)
    # category_loan = fields.Many2one('type.loan', string='Categoria', tracking=True)
    guarantor = fields.Many2one('res.partner', string='Garante')
    code_loan = fields.Char(string='Codigo de prestamo')
    amount_loan = fields.Float(string='Monto de prestamo (Bolivianos)', compute='_compute_change_dollars_bolivian')
    amount_loan_dollars = fields.Float(string='Monto de prestamo (dolares)')
    months_quantity = fields.Integer(string='Cantidad de meses')
    #valores calculados para prestamos
    amount_loan_max = fields.Float(string='Monto maximo de prestamo (Bolivianos)',  compute='_compute_set_amount')
    amount_loan_max_dollars = fields.Float(string='Monto maximo de prestamo (dolares)', )
    # monthly_interest = fields.Float(string='Interes mensual %', compute='_compute_interest_monthly')
    # contingency_fund = fields.Float(string='Fondo de contingencia %', compute='_compute_interest_monthly')
    index_loan = fields.Float(string='Indice de prestamo', compute='_compute_index_loan_fixed_fee')
    fixed_fee = fields.Float(string='Cuota fija', compute='_compute_index_loan_fixed_fee')
    date_application = fields.Date(string='Fecha de solicitud', default=fields.Date.today())
    date_approval = fields.Date(string='Fecha de aprobacion')
    # amount_min_def = fields.Float(string='Min. Defensa %', currency_field='company_currency_id',compute='_compute_min_def')
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
            self.index_loan = interest/index_quantity
            self.fixed_fee = self.amount_loan_dollars * self.index_loan
        except:
            self.index_loan = 0
    def button_value_dolar(self):
        dollar = self.env['res.currency'].search([('name','=','USD')], limit=1)
        self.value_dolar = round(dollar.inverse_rate,2)

    #Valores por default y constantes
    value_dolar = fields.Float(default=_compute_set_dollar)
    contingency_fund = fields.Float(string='Fondo de contingencia %', default= lambda self: float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.contingency_fund')))
    monthly_interest = fields.Float(string='Indice de prestamo por mes', default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest')))
    amount_min_def = fields.Float(string='Min. Defensa %', default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_min_def')), digits=(6, 3))

    #Relacion a los pagos
    loan_payment_ids = fields.One2many('loan.payment', 'loan_application_ids', string='Pagos')

    #Conversion dolares a boliviamos
    @api.depends('amount_loan_dollars')
    def _compute_change_dollars_bolivian(self):
        for rec in self:
            rec.amount_loan = rec.amount_loan_dollars * rec.value_dolar

    def approve_loan(self):
        self.progress()
        for rec in self:
            if rec.letter_of_request == False: raise ValidationError('Falta carta de solicitud')
            if rec.contact_request == False: raise ValidationError('Falta solicitud de prestamo')
            if rec.last_copy_paid_slip == False: raise ValidationError('Falta ultima copia de boleta de pago')
            if rec.ci_fothocopy == False: raise ValidationError('Falta fotocopia de CI')
            if rec.photocopy_military_ci == False: raise ValidationError('Falta fotocopia de carnet militar')

            for i in range(1, rec.months_quantity+1):
                percentage_amount_min_def = rec.fixed_fee * rec.amount_min_def
                if len(rec.loan_payment_ids) == 0:
                    capital_init = rec.amount_loan_dollars
                    date_payment = datetime.today()
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
                    'state': 'earring',
                })
    def verification_pass(self):
        self.state = 'verificate'
    def progress(self):
        self.state = 'progress'
        self.date_approval = fields.Date.today()

    def return_application(self):
        self.state = 'init'

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('loan.application')
        vals['name'] = name
        res = super(LoanApplication, self).create(vals)
        return res

    @api.onchange('type_loan')
    def _onchage_type_loan(self):
        if self.type_loan == 'emergency':
            self.guarantor = False
            self.months_quantity = 0

    #Asignar datos del socio, cantidad de meses
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            rec.months_quantity = rec.partner_id.category_partner_id.months
            rec.amount_loan_dollars = rec.partner_id.category_partner_id.limit_amount_dollars

