from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class TypeLoan(models.Model):
    _name = 'partner.category'
    _description = 'Categoria del socio'

    name = fields.Char(string='Categoria')
    code_loan = fields.Char(string='Codigo de categoria')
    months = fields.Integer(string='Meses limite')
    limit_amount = fields.Float(string='Monto limite en bolivianos', compute='_compute_limit_amount_dollars', store=True)
    limit_amount_dollars = fields.Float(string='Monto limite en dolares')

    @api.depends('limit_amount')
    def _compute_limit_amount_dollars(self):
        for record in self:
            dollar = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
            record.limit_amount_dollars = record.limit_amount * round(dollar.inverse_rate, 2)



