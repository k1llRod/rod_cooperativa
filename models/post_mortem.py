from odoo import api, fields, models, tools, _

class PostMortem(models.Model):
    _name = 'post.mortem'
    _description = 'Post Mortem'

    name = fields.Char(string='Codigo')
    family_ids = fields.Many2many('family', string='Beneficiarios/as')
    partner_id = fields.Many2one('res.partner', string='Socio')
    type_discount_post_mortem = fields.Selection([('traspaso_cossmil', 'Traspaso COSSMIL'), ('devolucion_aporte', 'Devolucion de aportes')], string='Tipo de retorno post mortem')
    type_payment = fields.Selection([('post_mortem', 'Post mortem'),
                                     ('longevity', 'Longevidad'),
                                     ('annual_discount', 'Por descuento anual')],
                                    string='Tipo de pago')
    since = fields.Date(string='Desde')
    until = fields.Date(string='Hasta')
    return_amount = fields.Float(string='Monto devuelto')
    return_amount_beneficiary = fields.Float(string='M. devuelto post mortem beneficiario')
    return_logevity_amount = fields.Float(string='M. devuelto longevidad socio')
    payment_date = fields.Date(string='Fecha de pago')

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('post.mortem')
        vals['name'] = name
        res = super(PostMortem, self).create(vals)
        return res
