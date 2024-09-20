from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class FinalizedLoan(models.Model):
    _name = 'finalized.loan'
    _description = 'Finalized Loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string = 'Codigo')
    loan_application_id = fields.Many2one('loan.application', string='Codigo Prestamo')
    date_finalize = fields.Date(string='Fecha de Finalizacion', required=True, default=fields.Date.context_today, track_visibility='onchange')
    amount_loan_dollars_initial = fields.Float(string='Monto de prestamo inicial en $')
    amount_loan_initial = fields.Float(string='Monto de prestamo inicial Bs.')
    payment_count = fields.Integer(string='Cantidad de pagos realizados')
    balance_capital_dollar = fields.Float(string='Saldo de capital en $.')
    balance_capital_bolivianos = fields.Float(string='Saldo de capital en Bs.')
    balance_total_interest_month = fields.Float(string='Saldo total de interes mensual en $.')
    balance_total_interest_month_bolivianos = fields.Float(string='Saldo total de interes mensual en Bs.')

    journal_id = fields.Many2one('account.journal', string='Diario')
    accounting_finalized_loan_id = fields.Many2one('account.move', string='Asiento contable')
    accounting_finalized_loan_state = fields.Selection([
        ('draft', 'Borrador'),
        ('posted', 'Publicado'),
    ], string='Estado', default='draft', related='accounting_finalized_loan_id.state', store=True, track_visibility='onchange')
    account_loan_id = fields.Many2one('account.account', string='Cuenta de prestamo', track_visibility='onchange')
    amount_account_loan = fields.Float(string='Monto de cuenta de prestamo', track_visibility='onchange')

    account_regular_loan_amortization = fields.Many2one('account.account', string='Cuenta de amortizacion de prestamo regular', track_visibility='onchange')
    amount_regular_loan_amortization = fields.Float(string='Monto de amortizacion de prestamo regular', track_visibility='onchange')
    account_other_income = fields.Many2one('account.account', string='Cuenta de otros ingresos')
    amount_other_income = fields.Float(string='Monto de otros ingresos', track_visibility='onchange')

    total_payment = fields.Float(string='Total de pagos', compute='_compute_total_payment', store=True)
    total_payment_bolivianos = fields.Float(string='Total de pagos en Bs.', compute='_compute_total_payment', store=True)

    @api.depends('balance_capital_dollar', 'balance_total_interest_month')
    def _compute_total_payment(self):
        for record in self:
            record.total_payment = record.balance_capital_dollar + record.balance_total_interest_month
            record.total_payment_bolivianos = record.balance_capital_bolivianos + record.balance_total_interest_month_bolivianos

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('done', 'Hecho'),
    ], string='Estado', default='draft', required=True, track_visibility='onchange')

    def action_draft(self):
        self.state = 'draft'
    def action_confirm(self):
        for record in self:
            move_line = []
            if record.loan_application_id.state == 'process':
                journal_id = record.journal_id.id
                data = (
                    0, 0, {'account_id': record.account_loan_id.id,
                           'debit': record.amount_account_loan,
                           'credit': 0,
                           'partner_id': record.loan_application_id.partner_id.id,
                           'amount_currency': 0
                           })
                if not (record.amount_account_loan == 0): move_line.append(data)
                data = (0, 0, {
                    'account_id': record.account_regular_loan_amortization.id,
                    'debit': 0, 'credit': record.amount_regular_loan_amortization,
                    'partner_id': record.loan_application_id.partner_id.id,
                    'amount_currency': 0
                })
                if not (record.amount_regular_loan_amortization == 0): move_line.append(data)
                data = (0, 0, {
                    'account_id': record.account_other_income.id,
                    'debit': 0, 'credit': record.amount_other_income,
                    'partner_id': record.loan_application_id.partner_id.id,
                    'amount_currency': 0
                })
                if not (record.amount_other_income == 0): move_line.append(data)
                move_vals = {
                    "date": record.date_finalize,
                    "journal_id": journal_id,
                    "ref": "LIQUIDACION DE PRESTAMO" + " " + record.loan_application_id.partner_id.name,
                    # "company_id": payment.company_id.id,
                    # "name": "name test",
                    "state": "draft",
                    "line_ids": move_line,
                }
                account_move_id = record.env['account.move'].create(move_vals)
                record.accounting_finalized_loan_id = account_move_id.id
                account_move_id.finalized_loan_id = record.id
                if account_move_id:
                    delete_records = record.loan_application_id.loan_payment_ids.filtered(
                        lambda x: x.state == 'draft').unlink()
                    if delete_records:
                        record.loan_application_id.state = 'done'
                    else:
                        raise ValidationError('Error al eliminar los registros de pagos')


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('finalized.loan')
        return super(FinalizedLoan, self).create(vals)

    def open_finalized_loan(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Finalized Loan'),
            'res_model': 'finalized.loan',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }
    @api.onchange('account_loan_id')
    def _onchange_account_loan_id(self):
        self.amount_account_loan = self.total_payment_bolivianos
        self.amount_regular_loan_amortization = self.balance_capital_bolivianos
        self.amount_other_income = self.balance_total_interest_month_bolivianos


