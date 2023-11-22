from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class TypeLoan(models.Model):
    _name = 'partner.category'
    _description = 'Categoria del socio'

    name = fields.Char(string='Categoria')
    code_loan = fields.Char(string='Codigo de categoria')
    months = fields.Integer(string='Meses limite')
    max_limit_amount_dollars = fields.Float(string='Monto maximo en dolares')
    max_limit_amount = fields.Float(string='Monto maximo en bolivianos', compute='_compute_limit_amount_dollars', store=True)
    ballot_balance = fields.Float(string='Saldo de boleta', store=True)

    @api.depends('max_limit_amount_dollars')
    def _compute_limit_amount_dollars(self):
        for record in self:
            dollar = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
            record.max_limit_amount = record.max_limit_amount_dollars * round(dollar.inverse_rate, 2)
