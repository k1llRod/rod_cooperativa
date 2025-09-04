# models/loan_refinance_confirm_wizard.py
from odoo import models, fields, _

class LoanRefinanceConfirmWizard(models.TransientModel):
    _name = 'loan.refinance.confirm.wizard'
    _description = 'Confirmación de refinanciamiento con pagos programados'

    message = fields.Text(readonly=True)
    original_wizard_id = fields.Many2one('form.refinance', required=True)

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_proceed(self):
        self.ensure_one()
        return self.original_wizard_id._do_refinance()
