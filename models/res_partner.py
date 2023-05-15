from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    name = fields.Char(string='Nombre', store=True)
    code_contact = fields.Char(string='Código de contacto')
    guarantor = fields.Boolean(string='Garante')
    partner = fields.Boolean(string='Socio')
    degree = fields.Selection([('primary', 'Primaria'), ('secondary', 'Secundaria'), ('university', 'Universitario')], string='Grado')
    ballot_balance = fields.Integer(string='Saldo boleta')

    name_contact = fields.Char(string='Nombre')
    paternal_surname = fields.Char(string='Apellido paterno')
    maternal_surname = fields.Char(string='Apellido materno')
    marital_status = fields.Selection([('single', 'Soltero'), ('married', 'Casado'), ('divorced', 'Divorciado'), ('widower', 'Viudo')], string='Estado civil')
    weapon = fields.Selection([('Artilleria', 'Artilleria'),
                               ('Infanteria', 'Infanteria'),
                               ('Caballeria', 'Caballeria'),
                               ('Comunicaciones','Comunicaciones'),
                               ('Logística','Logística'),
                               ('Ingenieria','Ingenieria')], string='Arma', default='Artilleria')
    #categoria de socio
    category_partner_id = fields.Many2one('partner.category', string='Categoría de socio')

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

    # def name_get(self):
    #     result = []
    #     for partner in self:
    #         name = str(partner.vat) + ' - ' + partner.name
    #         result.append((partner.id,name))
    #     return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            partners_ids = []
            args = ['|', ('name', operator, name), ('vat', operator, name)] + args
            partners_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        else:
            partners_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return partners_ids


    # @api.depends('name_contact', 'paternal_surname', 'maternal_surname')
    # def _compute_name(self):
    #     for partner in self:
    #         if partner.name_contact:
    #             partner.name = partner.name_contact
    #         if partner.paternal_surname:
    #             partner.name = partner.paternal_surname + ' ' + partner.name
    #         if partner.maternal_surname:
    #             partner.name = partner.maternal_surname + ' ' + partner.name





