from odoo import api, fields, models, tools, _

class Family(models.Model):
    _name = 'family'
    _description = 'Family'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre beneficiario/a', required=True)
    kinship = fields.Selection([('son', 'Hijo/a'), ('wife', 'Esposa'), ('husband', 'Esposo')], string='Parentesco')
    date_of_birth = fields.Date(string='Fecha de nacimiento')
    age = fields.Integer(string='Edad', compute='_compute_age', store=True)
    nro_celular = fields.Char(string='Nro. Celular')
    partner_id = fields.Many2one('res.partner', string='Socio', store=True)
    partner_name = fields.Char(string='Nombre del socio', related='partner_id.name', store=True)
    graduation_year = fields.Integer(string='Prom.', related='partner_id.graduation_year', store=True)
    category_partner_id = fields.Many2one('partner.category', string='Categoria de socio', related='partner_id.category_partner_id', store=True)
    beneficiary = fields.Boolean(string='Beneficiario/a')
    type_discount_post_mortem = fields.Selection([('traspaso_cossmil', 'Traspaso COSSMIL'), ('devolucion_aporte', 'Devolucion de aportes')], string='Tipo de retorno post mortem')
    since = fields.Date(string='Desde')
    until = fields.Date(string='Hasta')
    return_amount = fields.Float(string='M. devuelto post mortem socio')
    return_amount_beneficiary = fields.Float(string='M. devuelto post mortem beneficiario')
    return_logevity_amount = fields.Float(string='M. devuelto longevidad socio')
    payment_date = fields.Date(string='Fecha de pago')
    base_amount = fields.Float(string='Monto de beneficio post mortem')
    base_longevity = fields.Float(string='Longevidad')
    total_amount = fields.Float(string='Saldo total', compute='_compute_total_amount', store=True)
    global_amount = fields.Float(string='Monto global', compute='_calculate_global_amount',store=True)
    def create(self, vals_list):
        res = super(Family, self).create(vals_list)

        return res
    @api.depends('base_amount', 'base_longevity')
    def _calculate_global_amount(self):
        for record in self:
            record.global_amount = record.base_amount + record.base_longevity

    @api.depends('return_amount', 'return_logevity_amount','return_amount_beneficiary')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.global_amount - (record.return_amount + record.return_amount_beneficiary +record.return_logevity_amount)

    @api.depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            if record.date_of_birth:
                record.age = fields.Date.today().year - fields.Date.from_string(record.date_of_birth).year

    def init_widow(self):
        action = self.env['ir.actions.act_window']._for_xml_id('rod_cooperativa.action_family')
        domain = []
        partners = self.env['family'].search([('beneficiary', '=', True)])
        domain.append(('id', 'in', partners and partners.ids or False))
        action['domain'] = domain
        return action


