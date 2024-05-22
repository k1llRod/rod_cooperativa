from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PaymentPostMortem(models.TransientModel):
    _name = 'payment.post.mortem'

    name = fields.Char(string='Codigo')
    family_ids = fields.Many2many('family', string='Beneficiarios/as')
    partner_id = fields.Many2one('res.partner', string='Socio')
    type_payment = fields.Selection([('post_mortem', 'Post mortem'),
                                     ('longevity', 'Longevidad'),
                                     ('annual_discount','Por descuento anual')],
                                    string='Tipo de pago')
    return_amount = fields.Float(string='Monto a devolver')
    return_amount_beneficiary = fields.Float(string='M. devuelto post mortem beneficiario')
    return_logevity_amount = fields.Float(string='M. devuelto longevidad socio')
    payment_date = fields.Date(string='Fecha de pago')
    base_amount = fields.Integer(string='Saldo Post mortem')
    base_longevity_amount = fields.Integer(string='Saldo longevidad')
    global_amount = fields.Integer(string='Monto global')

    def register_payment(self):
        self.ensure_one()
        if self.type_payment == 'post_mortem':
            if self.return_amount > self.partner_id.balance_post_mortem:
                raise ValidationError(_('El monto a devolver no puede ser mayor al saldo post mortem'))
        if self.type_payment == 'longevity':
            if self.return_amount > self.partner_id.balance_longevity:
                raise ValidationError(_('El monto a devolver no puede ser mayor al saldo longevidad'))

        create = self.env['post.mortem'].create({
            'name': self.name,
            'family_ids': [(6, 0, self.family_ids.ids)],
            'partner_id': self.partner_id.id,
            'type_payment': self.type_payment,
            'payment_date': self.payment_date,
            'return_amount': self.return_amount,
            'return_amount_beneficiary': self.return_amount_beneficiary,
            'return_logevity_amount': self.return_logevity_amount,
            'payment_date': self.payment_date,
        })
        return {
            'name': 'Detalle del socio',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }



