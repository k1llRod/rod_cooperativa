from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    name = fields.Char(string='Nombre', store=True)
    code_contact = fields.Char(string='Código de socio / Boleta de pago')
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
    ci_cossmil = fields.Char(string='C.I. COSSMIL Nro.')
    ci_military = fields.Char(string='C.I. MILITAR Nro.')
    graduation_year = fields.Integer(string='Año de graduación')
    specialty = fields.Char(string='Especialidad')
    allergies = fields.Char(string='Alergias')
    type_blood = fields.Char(string='Tipo de sangre')
    partner_status = fields.Selection([('activate', 'Servicio activo'),
                                       ('active_reserve', 'Reserva activa'),
                                       ('passive_reserve_a', 'Reserva pasivo "A"'),
                                       ('passive_reserve_b', 'Reserva pasivo "B"')],
                                      string='Sitiación de socio')
    state = fields.Selection([('draft', 'Borrador'), ('verificate', 'Verificación'), ('activate', 'Socio activo'),
                              ('rejected', 'Rechazado')],
                             string='Estado', default='draft')
    year_service = fields.Integer(string='Años de servicio', compute='_compute_year_service', store=True)

    @api.depends('graduation_year')
    def _compute_year_service(self):
        for partner in self:
            if partner.graduation_year:
                partner.year_service = datetime.now().year - partner.graduation_year
            else:
                partner.year_service = 0
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


    #Funcion para contar cuantos garantias dio el contacto
    guarantor_count = fields.Integer(compute='_compute_guarantor_count', string='Garantías asignadas')

    @api.depends('guarantor')
    def _compute_guarantor_count(self):
        loan = self.env['loan.application'].search([]).filtered(lambda x:x.guarantor.id == self.id)
        self.guarantor_count = len(loan)

    def action_view_guarantor(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("rod_cooperativa.action_loan_application")
        action['domain'] = [
            ('guarantor.id', '=', self.id),
        ]
        return action

    def action_view_partner_invoices(self):
        return True

    #Campo por default Pais
    country_id = fields.Many2one('res.country', string='País', default=29)

    @api.onchange('state_id')
    def _onchange_state_id(self):
        for partner in self:
            if partner.state_id:
                partner.zip = partner.state_id.code

    #Parentesco
    # def _compute_my_field(self):
    #     for record in self:
    #         record.family_id = [(0, 0, {'partner_id': record.id})]
    family_id = fields.One2many('family', 'partner_id', string='Familiares')





