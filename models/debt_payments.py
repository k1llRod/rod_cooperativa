from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class DebtPayments(models.Model):
    _name = 'debt.payments'
    _description = 'Pagos de prestamo'

    code_payment = fields.Char(string='Codigo de pago')
    code_loan = fields.Char(string='Codigo de prestamo')
    type_payment = fields.Selection([('efectivo', 'Efectivo'), ('cheque', 'Cheque'), ('transferencia', 'Transferencia')], string='Tipo de pago')
    monto = fields.Float(string='Monto')

