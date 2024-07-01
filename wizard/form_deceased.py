from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FormDeceased(models.TransientModel):
    _name = 'form.deseaced'

    name = fields.Char(string='Nombre del fallecido')
    description = fields.Text(string='Descripción')
    date_deceased = fields.Date(string='Fecha de fallecimiento', required=True)
    type_unsuscribe = fields.Selection([('deceased', 'Fallecido'), ('unsubscribe', 'Baja')], string='Tipo de baja')
    partner_id = fields.Many2one('res.partner', string='Socio', required=True)

    def action_confirm(self):
        if self.type_unsuscribe == 'deceased':
            self.partner_id.write({'state': 'deceased', 'date_deceased': self.date_deceased, 'glosa': self.description})
        else:
            self.partner_id.write({'state': 'unsubscribe', 'date_unsubscribe': self.date_deceased})
        return {'type': 'ir.actions.act_window_close'}
