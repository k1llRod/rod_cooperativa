from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    monthly_interest = fields.Float(string='Interes mensual %', digits=(6, 3))
    contingency_fund = fields.Float(string='Fondo de contingencia %', digits=(6, 3))
    percentage_min_def = fields.Float(string='Porcentaje Min. Defensa %', digits=(6, 3))
    insurance_relief = fields.Float(string='Seguro de desgravamen %', digits=(6, 3))

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
                self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.insurance_relief'))

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

    #crear get y set