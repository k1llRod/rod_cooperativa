from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

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
    net_salary = fields.Float(string='Salario neto')
    type_loan = fields.Selection([('regular','Regular'), ('emergency','Emergencia')], string='Tipo de prestamo')
    partner_id = fields.Many2one('res.partner', string='Socio solicitante', required=True, tracking=True)
    letter_of_request = fields.Boolean(string='Carta de solicitud')
    contact_request = fields.Boolean(string='Solicitud de prestamo')
    last_copy_paid_slip = fields.Boolean(string='Ultima copia de boleta de pago')
    ci_fothocopy = fields.Boolean(string='Fotocopia de CI')
    photocopy_military_ci = fields.Boolean(string='Fotocopia de Carnet militar')
    # category_loan = fields.Many2one('type.loan', string='Categoria', tracking=True)
    guarantor = fields.Many2one('res.partner', string='Garante')
    code_loan = fields.Char(string='Codigo de prestamo')
    amount_loan = fields.Float(string='Monto de prestamo (Bolivianos)')
    amount_loan_dollars = fields.Float(string='Monto de prestamo (dolares)')
    months_quantity = fields.Integer(string='Cantidad de meses')
    #valores calculados para prestamos
    amount_loan_max = fields.Float(string='Monto maximo de prestamo (Bolivianos)',  compute='_compute_set_amount')
    amount_loan_max_dollars = fields.Float(string='Monto maximo de prestamo (dolares)', )
    # monthly_interest = fields.Float(string='Interes mensual %', compute='_compute_interest_monthly')
    # contingency_fund = fields.Float(string='Fondo de contingencia %', compute='_compute_interest_monthly')
    index_loan = fields.Float(string='Indice de prestamo')
    fixed_fee = fields.Float(string='Cuota fija')
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
    contingency_fund = fields.Float(string='Fondo de contingencia %', default= lambda self: float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest')))
    monthly_interest = fields.Float(string='Indice de prestamo', default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.contingency_fund')))
    amount_min_def = fields.Float(string='Min. Defensa %', default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_min_def')))



