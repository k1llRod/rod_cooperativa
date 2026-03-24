from odoo import api, fields, models, tools, _

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
    amount_pm_debe = fields.Float(string='Monto salida Post-Mortem (Debe)', store=True)
    account_pm_post_mortem_id = fields.Many2one('account.account', string='Cuenta Post-Mortem (Haber)',  store=True)
    amount_pm_post_mortem = fields.Float(string='Monto Post-Mortem (Haber)', store=True)
    account_pm_regulation_cup_id = fields.Many2one('account.account', string='Cuenta tasa de regulacion CUP (Haber)',  store=True)
    amount_pm_regulation_cup = fields.Float(string='Monto tasa de regulacion CUP (Haber)', store=True)
    account_pm_inscription_id = fields.Many2one('account.account', string='Cuenta desvincualcion Post-Mortem (Haber)',  store=True)
    amount_pm_inscription = fields.Float(string='Monto desvincualcion Post-Mortem (Haber)', store=True)

    state = fields.Selection([('draft', 'Borrador'),
                              ('verification', 'Verificacion'),
                              ('paid', 'Pagado')],
                             string='Estado', default='draft')

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('post.mortem')
        vals['name'] = name
        vals['account_pm_debe_id'] = self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.account_pm_debe_id', default=False) or False
        vals['account_pm_post_mortem_id'] = self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.account_pm_post_mortem_id', default=False) or False
        vals['account_pm_regulation_cup_id'] = self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.account_pm_regulation_cup_id', default=False) or False
        vals['account_pm_inscription_id'] = self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.account_pm_inscription_id', default=False) or False
        res = super(PostMortem, self).create(vals)
        return res

    def action_verification(self):
        self.state = 'verification'
    def action_paid(self):
        self.state = 'paid'

    def action_draft(self):
        self.state = 'draft'

    @api.onchange('amount_pm_debe', 'amount_pm_regulation_cup', 'amount_pm_inscription')
    def _onchange_amounts_balance(self):
        for record in self:
            # Aseguramos que los valores sean tratados como float para evitar errores de None
            debe_total = record.amount_pm_debe or 0.0
            cup = record.amount_pm_regulation_cup or 0.0
            ins = record.amount_pm_inscription or 0.0

            # Haber = PostMortem + Cup + Inscripcion -> PostMortem = Debe - (Cup + Inscripcion)
            record.amount_pm_post_mortem = debe_total - (cup + ins)
            record.return_amount = record.amount_pm_post_mortem

            if record.amount_pm_post_mortem < 0:
                return {
                    'warning': {
                        'title': _("Alerta de Montos"),
                        'message': _("Las deducciones superan el monto total del beneficio (Debe).")
                    }
                }
