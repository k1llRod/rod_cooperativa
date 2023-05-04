from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class TypeLoan(models.Model):
    _name = 'type.loan'
    _description = 'Tipo de prestamo'

    code_loan = fields.Char(string='Codigo de prestamo')
    degree = fields.Char(string='Grado')
    limit_amount = fields.Float(string='Monto limite')
    months = fields.Integer(string='Meses limite')

