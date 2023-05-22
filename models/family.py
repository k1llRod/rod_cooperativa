from odoo import api, fields, models, tools, _

class Family(models.Model):
    _name = 'family'
    _description = 'Family'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', required=True)
    kinship = fields.Selection([('son', 'Hijo/a'), ('wife', 'Esposa'), ('husband', 'Esposo')], string='Parentesco')
    date_of_birth = fields.Date(string='Fecha de nacimiento')
    nro_celular = fields.Char(string='Nro. Celular')
    partner_id = fields.Many2one('res.partner', string='Socio', store=True)

    def create(self, vals_list):
        res = super(Family, self).create(vals_list)

        return res



