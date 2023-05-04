from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class LoanApplication(models.Model):
    _name = 'loan.application'
    _description = 'Solicitud de prestamo'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Código de solicitud', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Socio solicitante', required=True, tracking=True)
    letter_of_request = fields.Boolean(string='Carta de solicitud')
    contact_request = fields.Boolean(string='Solicitud de prestamo')
    last_copy_paid_slip = fields.Boolean(string='Ultima copia de boleta de pago')
    ci_fothocopy = fields.Boolean(string='Fotocopia de CI')
    photocopy_military_ci = fields.Boolean(string='Fotocopia de Carnet militar')
    type_of_loan = fields.Selection([('personal', 'Personal'), ('mortgage', 'Hipotecario')], string='Tipo de préstamo')
    guarantor = fields.Many2one('res.partner', string='Garante')
    code_loan = fields.Char(string='Codigo de prestamo')

    state = fields.Selection([
        ('init', 'Inicio'),
        ('verificate', 'Verificación'),
        ('progress', 'En Proceso'),
        ('done', 'Concluido'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='init')


