from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class TypeLoan(models.Model):
    _name = 'type.loan'
    _description = 'Tipo de prestamo'

    name = fields.Char(string='Tipo de prestamo')
    code_loan = fields.Char(string='Codigo de prestamo')
    degree = fields.Char(string='Grado')
    months = fields.Integer(string='Meses limite')
    limit_amount = fields.Float(string='Monto limite en bolivianos')
    limit_amount_dollars = fields.Float(string='Monto limite en dolares')
    amount_month = fields.Float(string='Monto por mes')
    amount_month_dollars = fields.Float(string='Monto por mes en dolares')


