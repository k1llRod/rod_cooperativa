from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class FormFinalizedLoan(models.TransientModel):
    _name = 'form.finalized.loan'
    _description = 'Form Finalized Loan'

    # name = fields.Char(string = 'name')
    loan_application_id = fields.Many2one('loan.application', string='Codigo Prestamo')
    date_finalize = fields.Date(string='Fecha de Finalizacion', required=True, default=fields.Date.context_today)
    amount_loan_dollars_initial = fields.Float(string='Monto de prestamo inicial en dolares')
    amount_loan_initial = fields.Float(string='Monto de prestamo inicial')
    month_quantity_initial = fields.Float(string='Cantidad de meses iniciales')
    date_application = fields.Date(string='Fecha de solicitud')
    date_approval = fields.Date(string='Fecha de aprobacion')
    payment_count = fields.Integer(string='Cantidad de pagos realizados')
    balance_capital = fields.Float(string='Saldo de capital $.')
    balance_capital_bolivianos = fields.Float(string='Saldo de capital Bs.', compute='_compute_calculate_dollar', store=True)
    balance_total_interest_month = fields.Float(string='Saldo total de interes mensual $.')
    balance_total_interest_month_bolivianos = fields.Float(string='Saldo total de interes mensual en Bs.', compute='_compute_calculate_dollar', store=True)


    @api.depends('balance_capital', 'balance_total_interest_month')
    def _compute_calculate_dollar(self):
        for record in self:
            record.balance_capital_bolivianos = record.balance_capital * 6.96
            record.balance_total_interest_month_bolivianos = record.balance_total_interest_month * 6.96

    def action_confirm(self):
        if self.loan_application_id.state != 'progress':
            raise UserError(_('No se puede confirmar un prestamo finalizado que no este en progreso.'))
        finalized_loan = self.env['finalized.loan'].create({
            'loan_application_id': self.loan_application_id.id,
            'date_finalize': self.date_finalize,
            'amount_loan_dollars_initial': self.amount_loan_dollars_initial,
            'amount_loan_initial': self.amount_loan_initial,
            'payment_count': self.payment_count,
            'balance_capital_dollar': self.balance_capital,
            'balance_capital_bolivianos': self.balance_capital_bolivianos,
            'balance_total_interest_month': self.balance_total_interest_month,
            'balance_total_interest_month_bolivianos': self.balance_total_interest_month_bolivianos,
            'state': 'draft'
        })
        if finalized_loan:
            self.loan_application_id.state = 'liquidation_process'
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': _('Finalized Loan'),
        #     'res_model': 'finalized.loan',
        #     'view_mode': 'form',
        #     'res_id': finalized_loan.id,
        #     'target': 'current',
        # }