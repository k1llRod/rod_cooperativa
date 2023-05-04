from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    monthly_interest = fields.Float(string='Interes mensual %')
    contingency_fund = fields.Float(string='Fondo de contingencia %')


    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.monthly_interest', self.monthly_interest)
        self.env['ir.config_parameter'].sudo().set_param('rod_cooperativa.contingency_fund', self.contingency_fund)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            monthly_interest=float(params.get_param('rod_cooperativa.monthly_interest', default=False))
        )

        return res

    #crear get y set