from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    name = fields.Char(string='Nombre', store=True)
    code_contact = fields.Char(string='Código de asociado / Boleta de pago', require=True)
    guarantor = fields.Boolean(string='Garante')
    partner = fields.Boolean(string='Asociado', default=True)
    degree = fields.Selection([('primary', 'Primaria'), ('secondary', 'Secundaria'), ('university', 'Universitario')],
                              string='Grado')
    ballot_balance = fields.Integer(string='Saldo boleta')

    name_contact = fields.Char(string='Nombres', require=True)
    paternal_surname = fields.Char(string='Apellido paterno', require=True)
    maternal_surname = fields.Char(string='Apellido materno', require=True)
    marital_status = fields.Selection(
        [('single', 'Soltero'), ('married', 'Casado'), ('divorced', 'Divorciado'), ('widower', 'Viudo')],
        string='Estado civil', default='single', require=True)
    weapon = fields.Selection([('Artilleria', 'Artilleria'),
                               ('Infanteria', 'Infanteria'),
                               ('Caballeria', 'Caballeria'),
                               ('Comunicaciones', 'Comunicaciones'),
                               ('Logística', 'Logística'),
                               ('Ingenieria', 'Ingenieria')], string='Arma', default='Artilleria')
    # categoria de socio
    category_partner_id = fields.Many2one('partner.category', string='Grado')
    ci_cossmil = fields.Char(string='C. COSSMIL Nro.')
    ci_military = fields.Char(string='C. MILITAR Nro.')
    graduation_year = fields.Integer(string='Año de egreso')
    specialty = fields.Selection([('DAEN', 'DAEN'),
                                  ('DAENMG', 'DAENMG'),
                                  ('DEM', 'DEM'),
                                  ('DIM', 'DIM'),
                                  ('OEME', 'OEME'),
                                  ('PROF', 'PROF')], string='Especialidad')
    allergies = fields.Char(string='Alergias')
    type_blood = fields.Char(string='Grupo sanguineo')
    partner_status = fields.Selection([('active', 'Activo'),
                                       ('active_reserve', 'Reserva activa'),
                                       ('passive', 'Servicio pasivo'),
                                       ('leave', 'Baja')], string="Situacion general",
                                      compute='_onchange_partner_status', store=True)

    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('guest','Invitado'),
                                                 ('passive_reserve_a', 'Pasivo categoria "A"'),
                                                 ('passive_reserve_b', 'Pasivo categoria "B"'),
                                                 ('leave', 'Baja')], string='Tipo de asociado', store=True)

    year_service = fields.Integer(string='Años de servicio', compute='_compute_year_service', store=True)

    ci_photocopy = fields.Boolean(string='Fotocopia de C.I.')
    photocopy_military_ci = fields.Boolean(string='Fotocopia de carnet militar')
    affliation = fields.Boolean(string='Formulario de afiliación')
    photocopy_cossmil_ci = fields.Boolean(string='Fotocopia de carnet COSSMIL')
    # linkrage_request = fields.Boolean(string='Solicitud de vinculación')
    date_birthday = fields.Date(string='Fecha de nacimiento')
    years_completed = fields.Integer(string='Edad', compute='_compute_years_completed', store=True)
    # campo base res.partner
    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'), ('company', 'Company')],
                                    compute='_compute_company_type', inverse='_write_company_type', default='person')
    force_organization = fields.Selection([('ejercito', 'Ejercito'),
                                           ('armada_boliviana', 'Armada Boliviana'),
                                           ('aerea', 'Fuerza Aerea'),
                                           ('comando_jefe', 'Comando en jefe'),
                                           ('ministerio_defensa', 'Ministerio de defensa')], string='Fuerza / org', default='ejercito')


    @api.depends('graduation_year')
    def _compute_year_service(self):
        for partner in self:
            if partner.graduation_year:
                partner.year_service = datetime.now().year - partner.graduation_year
            else:
                partner.year_service = 0

    @api.depends('date_birthday')
    def _compute_years_completed(self):
        for partner in self:
            if partner.date_birthday:
                partner.years_completed = datetime.now().year - partner.date_birthday.year
            else:
                partner.years_completed = 0

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
            args = ['|','|',('name', operator, name), ('vat', operator, name), ('code_contact',operator, name)] + args
            partners_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        else:
            partners_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return partners_ids

    # Funcion para contar cuantos garantias dio el contacto
    guarantor_count = fields.Integer(compute='_compute_guarantor_count', string='Garantías asignadas')

    @api.depends('guarantor')
    def _compute_guarantor_count(self):
        guarantor_one = self.env['loan.application'].search([('guarantor_one','=',self.id)])
        guarantor_two = self.env['loan.application'].search([('guarantor_two', '=', self.id)])
        loan = len(guarantor_one) if guarantor_one else 0
        loan1 = len(guarantor_two) if guarantor_two else 0
        # loan = self.env['loan.application'].search([]).filtered(lambda x: x.guarantor.id == self.id)
        self.guarantor_count = loan + loan1

    def action_view_guarantor(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("rod_cooperativa.action_loan_application")
        action['domain'] = [
            '|',
            ('guarantor_one.id', '=', self.id),
            ('guarantor_two.id', '=', self.id)
        ]
        return action

    def action_view_partner_invoices(self):
        return True

    # Campo por default Pais
    country_id = fields.Many2one('res.country', string='País', default=29)

    @api.onchange('state_id')
    def _onchange_state_id(self):
        for partner in self:
            if partner.state_id:
                partner.zip = partner.state_id.code

    # Parentesco
    # def _compute_my_field(self):
    #     for record in self:
    #         record.family_id = [(0, 0, {'partner_id': record.id})]
    family_id = fields.One2many('family', 'partner_id', string='Familiares')

    # @api.onchange('partner_status_especific')
    @api.depends('partner_status_especific')
    def _onchange_partner_status(self):
        for record in self:
            if record.partner_status_especific == 'active_service' or record.partner_status_especific == 'letter_a' or record.partner_status_especific == 'active_reserve':
                record.partner_status = 'active'
            if record.partner_status_especific == 'passive_reserve_a' or record.partner_status_especific == 'passive_reserve_b':
                record.partner_status = 'passive'
            if record.partner_status_especific == 'leave':
                record.partner_status = 'leave'
            if record.partner_status_especific == False:
                record.partner_status = False

    def _init_partners(self):
        view_id = self.env.ref('rod_cooperativa.res_partner_tree_inh').id
        search_id = self.env.ref('rod_cooperativa.view_res_partner_filter_inherit').id
        return {
            'name': 'Socios',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            # 'view_id': view_id,
            'view_mode': 'tree,kanban',
            'search_view_id': search_id,
            'domain': [],
        }

    def init_loan_emergency(self):
        loan_application = self.env['loan.application'].create({'partner_id': self.id,
                                                                'date_application': datetime.now(),
                                                                'type_loan': 'emergency',
                                                                })
        return {
            'name': 'Detalle del prestamo',
            'type': 'ir.actions.act_window',
            'res_model': 'loan.application',
            'res_id': loan_application.id,
            'view_mode': 'form',
            'target': 'current',
        }
    def action_partner_coap(self):
        return True

    def update_destination(self):
        payroll = self.env['payroll.payments'].search([('partner_status_especific', '=', 'active_service')])


    # def init_loan(self):
    #     partner_payroll = self.env['partner.payroll'].create({'partner_id': self.id,
    #                                                           'date_registration': datetime.now(),
    #                                                           'total_contribution': 0,
    #                                                           'advanced_payments': 0,
    #                                                           'state': 'draft'})
    #     view_id = self.env.ref('rod_cooperativa_aportes.action_partner_payroll')
    #     return {
    #         'name': 'Detalle del Registro',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'partner.payroll',
    #         'res_id': partner_payroll.id,
    #         'view_mode': 'form',
    #         'target': 'current',
    #     }
