from odoo import api, fields, models, tools, _

class FinalizedLoan(models.Model):
    _name = 'finalized.loan'
    _description = 'Finalized Loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string = 'Codigo')
    loan_application_id = fields.Many2one('loan.application', string='Codigo Prestamo')
    date_finalize = fields.Date(string='Fecha de Finalizacion', required=True, default=fields.Date.context_today)
    amount_loan_dollars_initial = fields.Float(string='Monto de prestamo inicial en $')
    amount_loan_initial = fields.Float(string='Monto de prestamo inicial Bs.')
    payment_count = fields.Integer(string='Cantidad de pagos realizados')
    balance_capital_dollar = fields.Float(string='Saldo de capital en $.')
    balance_capital_bolivianos = fields.Float(string='Saldo de capital en Bs.')
    balance_total_interest_month = fields.Float(string='Saldo total de interes mensual en $.')
    balance_total_interest_month_bolivianos = fields.Float(string='Saldo total de interes mensual en Bs.')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('done', 'Hecho'),
    ], string='Estado', default='draft', required=True)

    def action_confirm(self):
        # Here you can write the code to finalize the contributions
        a = 1

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('finalized.loan')
        return super(FinalizedLoan, self).create(vals)