from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class Loan(models.Model):
    _name = 'loan'
    _description = 'Prestamo'

    code_loan = fields.Char(string='Codigo de prestamo')
    code_contact = fields.Char(string='Código de contacto')
    alta = fields.Date(string='Alta')
    type_coin = fields.Selection([('bs', 'Bs'), ('sus', 'Sus')], string='Tipo de moneda')
    total_debt = fields.Float(string='Deuda total')
    total_debt_dollars = fields.Float(string='Deuda total en dolares')
    debt_balance = fields.Float(string='Saldo deuda')
    observaciones = fields.Text(string='Observaciones')


