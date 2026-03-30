from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class PostMortem(models.Model):
    _name = 'post.mortem'
    _description = 'Post Mortem'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Codigo')
    family_ids = fields.Many2many('family',
                                  string='Beneficiarios/as',
                                  domain="[('partner_id', '=', partner_id)]")
    partner_id = fields.Many2one('res.partner', string='Socio')
    type_discount_post_mortem = fields.Selection([('traspaso_cossmil', 'Traspaso COSSMIL'), ('devolucion_aporte', 'Devolucion de aportes')], string='Tipo de retorno post mortem')
    type_payment = fields.Selection([('post_mortem', 'Post mortem'),
                                     ('longevity', 'Longevidad'),
                                     ('annual_discount', 'Por descuento anual')],
                                    string='Tipo de pago')
    # partner_payroll_id = fields.Many2one('partner.payroll', string='Aportes del socio')
    # since = fields.Date(string='Desde', related='partner_payroll_id.since_payment', store=True)
    # until = fields.Date(string='Hasta', related='partner_payroll_id.until_payment', store=True)
    return_amount = fields.Float(string='Monto devuelto')
    return_amount_beneficiary = fields.Float(string='M. devuelto post mortem beneficiario')
    return_logevity_amount = fields.Float(string='M. devuelto longevidad socio')
    payment_date = fields.Date(string='Fecha de pago')
    observation = fields.Text(string='Observación')
    journal_id = fields.Many2one('account.journal', string='Diario de registro')
    account_move_id = fields.Many2one('account.move', string='Asiento contable')

    account_pm_debe_id = fields.Many2one('account.account', string='Cuenta salida Post-Mortem (Debe)', store=True)
    amount_pm_debe = fields.Float(string='Monto salida Post-Mortem (Debe)')
    account_pm_post_mortem_id = fields.Many2one('account.account', string='Cuenta Post-Mortem (Haber)',  store=True)
    amount_pm_post_mortem = fields.Float(string='Monto Post-Mortem (Haber)')
    account_pm_regulation_cup_id = fields.Many2one('account.account', string='Cuenta tasa de regulacion (Haber)',  store=True)
    amount_pm_regulation_cup = fields.Float(string='Monto tasa de regulacion (Haber)')
    account_pm_inscription_id = fields.Many2one('account.account', string='Cuenta desvincualcion Post-Mortem (Haber)',  store=True)
    amount_pm_inscription = fields.Float(string='Monto desvincualcion Post-Mortem (Haber)')

    state = fields.Selection([('draft', 'Borrador'),
                              ('verification', 'Verificacion'),
                              ('paid', 'Pagado')],
                             string='Estado', default='draft')

    @api.model
    def create(self, vals):
        # Secuencia
        if not vals.get('name') or vals.get('name') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('post.mortem') or '/'

        # Obtener parámetros de configuración y asegurar que sean INT
        params = self.env['ir.config_parameter'].sudo()
        vals['account_pm_debe_id'] = int(params.get_param('rod_cooperativa.account_pm_debe_id', default=0)) or False
        vals['account_pm_post_mortem_id'] = int(
            params.get_param('rod_cooperativa.account_pm_post_mortem_id', default=0)) or False
        vals['account_pm_regulation_cup_id'] = int(
            params.get_param('rod_cooperativa.account_pm_regulation_cup_id', default=0)) or False
        vals['account_pm_inscription_id'] = int(
            params.get_param('rod_cooperativa.account_pm_inscription_id', default=0)) or False

        return super(PostMortem, self).create(vals)

    @api.onchange('amount_pm_debe', 'amount_pm_regulation_cup', 'amount_pm_inscription')
    def _onchange_amounts_balance(self):
        """
        Lógica de equilibrio:
        Debe (Gasto) = Haber (Neto + Cup + Inscripción)
        """
        for record in self:
            debe = record.amount_pm_debe or 0.0
            cup = record.amount_pm_regulation_cup or 0.0
            ins = record.amount_pm_inscription or 0.0

            # Calculamos el neto (Lo que sobra del debe tras deducciones)
            neto_post_mortem = debe - (cup + ins)

            # Asignamos los valores
            record.amount_pm_post_mortem = neto_post_mortem
            record.return_amount = neto_post_mortem

            if neto_post_mortem < 0:
                return {
                    'warning': {
                        'title': _("Cuidado"),
                        'message': _("Las deducciones son mayores al monto del Debe. El neto es negativo.")
                    }
                }

    def action_verification(self):
        self.state = 'verification'

    def action_draft(self):
        self.state = 'draft'

    def action_paid(self):
        for record in self:
            # 1. Validar equilibrio contable
            total_haber = record.amount_pm_post_mortem + record.amount_pm_regulation_cup + record.amount_pm_inscription
            if round(record.amount_pm_debe, 2) != round(total_haber, 2):
                raise UserError(
                    _("El asiento contable no está en equilibrio (Debe: %s != Haber: %s).") % (record.amount_pm_debe,
                                                                                               total_haber))

            # 2. Validar que las cuentas estén configuradas
            if not record.account_pm_debe_id or not record.account_pm_post_mortem_id:
                raise UserError(_("Faltan cuentas contables por configurar en la pestaña 'Contabilidad' o en Ajustes."))

            # 3. Preparar las líneas del asiento (Account Move Lines)
            line_ids = []

            # Línea del DEBE (Gasto)
            line_ids.append((0, 0, {
                # 'name': _('Auxilio Funerario - %s') % record.partner_id.name,
                'name': '',
                'account_id': record.account_pm_debe_id.id,
                'debit': record.amount_pm_debe,
                'credit': 0.0,
                'partner_id': record.partner_id.id,
            }))

            # Líneas del HABER (Distribución)
            # A. Neto Post Mortem
            if record.amount_pm_post_mortem > 0:
                line_ids.append((0, 0, {
                    'name': _(''),
                    'account_id': record.account_pm_post_mortem_id.id,
                    'debit': 0.0,
                    'credit': record.amount_pm_post_mortem,
                    'partner_id': record.partner_id.id,
                }))

            # B. Tasa Regulación CUP
            if record.amount_pm_regulation_cup > 0:
                line_ids.append((0, 0, {
                    'name': _(''),
                    'account_id': record.account_pm_regulation_cup_id.id,
                    'debit': 0.0,
                    'credit': record.amount_pm_regulation_cup,
                    'partner_id': record.partner_id.id,
                }))

            # C. Inscripción / Desvinculación
            if record.amount_pm_inscription > 0:
                line_ids.append((0, 0, {
                    'name': _(''),
                    'account_id': record.account_pm_inscription_id.id,
                    'debit': 0.0,
                    'credit': record.amount_pm_inscription,
                    'partner_id': record.partner_id.id,
                }))

            # 4. Crear el Asiento Contable (Account Move)
            move_vals = {
                'date': fields.Date.context_today(self),
                'journal_id': record.journal_id.id or self.env['account.journal'].search([('type', '=', 'general')],
                                                                                         limit=1).id,
                'ref': record.name,
                'move_type': 'entry',
                'line_ids': line_ids,
            }

            move = self.env['account.move'].create(move_vals)
            # move.action_post()  # Publicar el asiento automáticamente

            # 5. Guardar referencia del asiento y cambiar estado
            record.write({
                'account_move_id': move.id,
                'state': 'paid'
            })
            return {
                'name': _('Asiento contable - %s') % record.name,
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': move.id,
                'view_mode': 'form',
                'target': 'current',
            }
