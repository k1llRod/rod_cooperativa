from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PaymentPostMortem(models.TransientModel):
    _name = 'payment.post.mortem'

    name = fields.Char(string='Codigo')
    family_ids = fields.Many2many('family', string='Beneficiarios/as', domain="[('partner_id', '=', partner_id)]")
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
    base_amount_dollars = fields.Float(string='Saldo post mortem en dólares', compute='_compute_base_dollars')
    base_longevity_amount = fields.Integer(string='Saldo longevidad')
    base_longevity_amount_dollars = fields.Integer(string='Saldo longevidad', compute='_compute_base_dollars')
    global_amount = fields.Integer(string='Monto global')
    observation = fields.Text(string='Observación')

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
            'family_ids': [(6, 0, self.family_ids.ids)] if self.type_payment != 'longevity' else [],
            'partner_id': self.partner_id.id,
            'type_payment': self.type_payment,
            'return_amount': self.return_amount,
            'return_amount_beneficiary': self.return_amount_beneficiary,
            'return_logevity_amount': self.return_logevity_amount,
            'payment_date': self.payment_date,
            'observation': self.observation,
            'amount_pm_debe': self.return_amount,
            'amount_pm_post_mortem': self.return_amount,
        })
        return {
            'name': 'Detalle del socio',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.depends('base_amount', 'base_longevity_amount')
    def _compute_base_dollars(self):
        for record in self:
            if record.partner_id.currency_id and record.partner_id.currency_id.name == 'USD':
                record.base_amount_dollars = record.base_amount
                record.base_longevity_amount_dollars = record.base_longevity_amount
            else:
                record.base_amount_dollars = round(record.base_amount / 6.96)
                record.base_longevity_amount_dollars = round(record.base_longevity_amount / 6.96)




