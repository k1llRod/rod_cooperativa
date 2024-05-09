from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PaymentPostMortem(models.TransientModel):
    _name = 'payment.post.mortem'

    name = fields.Char(string='Codigo')
    family_ids = fields.Many2many('family', string='Beneficiarios/as')
    partner_id = fields.Many2one('res.partner', string='Socio')
    type_payment = fields.Selection([('post_mortem', 'Post mortem'), ('longevity', 'Longevidad')],
                                    string='Tipo de pago')
    return_amount = fields.Float(string='Monto a devolver')
    return_amount_beneficiary = fields.Float(string='M. devuelto post mortem beneficiario')
    return_logevity_amount = fields.Float(string='M. devuelto longevidad socio')
    payment_date = fields.Date(string='Fecha de pago')



