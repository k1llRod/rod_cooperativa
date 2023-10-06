from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FormRefinance(models.TransientModel):
    _name = 'form.refinance'

    name = fields.Char(string='Codigo de refinancimiento', default='Nuevo')
    capital_initial = fields.Float(string='Monto de prestamo inicial')
    capital_rest = fields.Float(string='Capital Restante')
    quantity_month_initial = fields.Integer(string='Cantidad de meses inicial')
    interest_days_rest = fields.Float(string='Días de Interés Restantes')
    total_capital_rest = fields.Float(string='Total Capital Restante')
    amount_refinance = fields.Float(string='Monto a Refinanciar', required=True)
    month_refinance = fields.Integer(string='Meses a Refinanciar', required=True)
    date_refinance = fields.Date(string='Fecha de Refinanciamiento', required=True)
    data_loan_id = fields.Many2one('loan.application', string='Datos del prestamo')
    amount_delivered = fields.Float(string='Monto a entregar' ,compute='_compute_amount_delivered', store=True)

    fixed_fee = fields.Float(string='Cuota fija ($)', compute='_compute_index_loan_fixed_fee')
    index_loan = fields.Float(string='Indice de prestamo ($)', compute='_compute_index_loan_fixed_fee')
    index_loan_bs = fields.Float(string='Indice de prestamo (Bs)')
    contingency_fund = fields.Float(string='Fondo de contingencia %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.contingency_fund')))
    monthly_interest = fields.Float(string='Indice de prestamo por mes %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest')))
    amount_min_def = fields.Float(string='Min. Defensa %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_min_def')), digits=(6, 3))
    commission_min_def = fields.Float(string='Comision Min. Defensa %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_commission_min_def')),
                                      digits=(6, 3))
    @api.onchange('month_refinance','amount_refinance')
    def _compute_index_loan_fixed_fee(self):
        try:
            interest = (self.monthly_interest + self.contingency_fund) / 100
            index_quantity = (1 - (1 + interest) ** (-self.month_refinance))
            self.index_loan = interest / index_quantity if index_quantity != 0 else 0
            self.fixed_fee = self.amount_refinance * self.index_loan
        except:
            self.index_loan = 0
    def init_refinance(self):
        create_loan = self.env['loan.application'].create({
            'name': self.name,
            'type_loan': 'regular',
            'partner_id': self.data_loan_id.partner_id.id,
            'months_quantity': self.month_refinance,
            'amount_loan_dollars': self.amount_refinance,
            'date_application': self.date_refinance,
            'refinance_loan_id': self.data_loan_id.id,
            'amount_devolution': self.amount_delivered,
            'total_interest_month_surpluy': self.interest_days_rest,
            'state': 'init',
        })
        if create_loan:
            self.data_loan_id.state = 'refinanced'
            return {
                'type': 'ir.actions.act_window',
                'name': 'Prestamo',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'loan.application',
                'res_id': create_loan.id,
                'target': 'current',
            }
        else:
            raise ValidationError(_('Error en el proceso de refinanciamiento'))

    @api.depends('amount_refinance')
    def _compute_amount_delivered(self):
        for rec in self:
            rec.amount_delivered = rec.amount_refinance - rec.capital_rest