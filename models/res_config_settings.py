from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    monthly_interest = fields.Float(string='Interes mensual %', digits=(6, 3))
    contingency_fund = fields.Float(string='Fondo de contingencia %', digits=(6, 3))
    percentage_min_def = fields.Float(string='Porcentaje Min. Defensa %', digits=(6, 3))
    insurance_relief = fields.Float(string='Seguro de desgravamen %', digits=(6, 3))
    commission_min_def = fields.Float(string='Comisión Min. Defensa %', digits=(6, 3))
    mortgage_loan = fields.Float(string='Prestamo hipotecario', digits=(6, 3))
    monthly_interest_mortgage = fields.Float(string='Interes mensual hipotecario %', digits=(6, 3))

    account_loan_id = fields.Many2one('account.account', string='Cuenta contable de prestamos')
    account_egreso_id = fields.Many2one('account.account', string='Cuenta contable de egreso de intereses')
    account_monto_refinanciamiento = fields.Many2one('account.account', string='Cuenta contable de monto refinanciamiento')
    account_monto_meses_interes = fields.Many2one('account.account', string='Cuenta contable de monto meses de interes')


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            monthly_interest=float(
                self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest')),
            contingency_fund=float(
                self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.contingency_fund')),
            percentage_min_def=float(
                self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_min_def')),
            insurance_relief=float(
                self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.insurance_relief')),
            commission_min_def=float(
                self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.commission_min_def')),
            mortgage_loan=float(
                self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.mortgage_loan')),
            monthly_interest_mortgage=float(
                self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest_mortgage')),
            account_loan_id=int(
                self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.account_loan_id', default=False) or False),
            account_egreso_id=int(
                self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.account_egreso_id', default=False) or False),
            account_monto_refinanciamiento=int(
                self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.account_monto_refinanciamiento', default=False) or False),
            account_monto_meses_interes=int(
                self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.account_monto_meses_interes', default=False) or False),

        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.monthly_interest', self.monthly_interest)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.contingency_fund', str(self.contingency_fund))
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.percentage_min_def',
                                                         str(self.percentage_min_def))
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.insurance_relief',
                                                         str(self.insurance_relief))
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.commission_min_def', str(self.commission_min_def))
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.mortgage_loan',
                                                         str(self.mortgage_loan))
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.monthly_interest_mortgage',
                                                         str(self.monthly_interest_mortgage))
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.account_loan_id',
                                                            str(self.account_loan_id.id if self.account_loan_id else ''))
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.account_egreso_id',
                                                            str(self.account_egreso_id.id if self.account_egreso_id else ''))
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.account_monto_refinanciamiento',
                                                            str(self.account_monto_refinanciamiento.id if self.account_monto_refinanciamiento else ''))
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.account_monto_meses_interes',
                                                            str(self.account_monto_meses_interes.id if self.account_monto_meses_interes else ''))

    #crear get y set