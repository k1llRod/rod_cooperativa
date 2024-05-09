from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FormDeceased(models.TransientModel):
    _name = 'form.deseaced'

    name = fields.Char(string='Nombre del fallecido')
    description = fields.Text(string='Descripción')
    date_deceased = fields.Date(string='Fecha de fallecimiento', required=True)
    type_unsuscribe = fields.Selection([('deceased', 'Fallecido'), ('unsubscribe', 'Baja')], string='Tipo de baja')
    partner_id = fields.Many2one('res.partner', string='Socio', required=True)
