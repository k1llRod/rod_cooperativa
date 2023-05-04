from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    name = fields.Char(string='Nombre', store=True)
    code_contact = fields.Char(string='Código de contacto')
    guarantor = fields.Boolean(string='Garante')
    degree = fields.Selection([('primary', 'Primaria'), ('secondary', 'Secundaria'), ('university', 'Universitario')], string='Grado')
    ballot_balance = fields.Integer(string='Saldo boleta')

    name_contact = fields.Char(string='Nombre')
    paternal_surname = fields.Char(string='Apellido paterno')
    maternal_surname = fields.Char(string='Apellido materno')

    @api.onchange('name_contact', 'paternal_surname', 'maternal_surname')
    def _onchange_name(self):
        for partner in self:
            if partner.name_contact:
                partner.name = partner.name_contact
            if partner.maternal_surname:
                partner.name = partner.maternal_surname + ' ' + partner.name
            if partner.paternal_surname:
                partner.name = partner.paternal_surname + ' ' + partner.name
            if not partner.name_contact and not partner.paternal_surname and not partner.maternal_surname:
                partner.name = ''


    # @api.depends('name_contact', 'paternal_surname', 'maternal_surname')
    # def _compute_name(self):
    #     for partner in self:
    #         if partner.name_contact:
    #             partner.name = partner.name_contact
    #         if partner.paternal_surname:
    #             partner.name = partner.paternal_surname + ' ' + partner.name
    #         if partner.maternal_surname:
    #             partner.name = partner.maternal_surname + ' ' + partner.name





