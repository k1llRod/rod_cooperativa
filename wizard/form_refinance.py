from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FormRefinance(models.TransientModel):
    _name = 'form.refinance'

    name = fields.Char(string='Codigo de refinancimiento', default='Nuevo')
    capital_initial = fields.Float(string='Monto de prestamo inicial')
    capital_rest = fields.Float(string='Capital Restante')
    capital_rest_scheduled = fields.Float(string='Capital restante programado')
    quantity_month_initial = fields.Integer(string='Cantidad de meses inicial')
    interest_days_rest = fields.Float(string='Días de Interés Restantes')
    total_capital_rest = fields.Float(string='Total Capital Restante')
    amount_refinance = fields.Float(string='Monto a Refinanciar', required=True)
    month_refinance = fields.Integer(string='Meses a Refinanciar', required=True)
    date_refinance = fields.Date(string='Fecha de Refinanciamiento', required=True)
    data_loan_id = fields.Many2one('loan.application', string='Datos del prestamo')
    amount_delivered = fields.Float(string='Monto a entregar' ,compute='_compute_amount_delivered', store=True)

    fixed_fee = fields.Float(string='Cuota fija ($)', compute='_compute_index_loan_fixed_fee')
    index_loan = fields.Float(string='Indice de prestamo ($)', compute='_compute_index_loan_fixed_fee')
    index_loan_bs = fields.Float(string='Indice de prestamo (Bs)')
    contingency_fund = fields.Float(string='Fondo de contingencia %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.contingency_fund')))
    monthly_interest = fields.Float(string='Indice de prestamo por mes %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest')))
    amount_min_def = fields.Float(string='Min. Defensa %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_min_def')), digits=(6, 3))
    commission_min_def = fields.Float(string='Comision Min. Defensa %', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.percentage_commission_min_def')),
                                      digits=(6, 3))
    flag_expansion = fields.Boolean(string='Ampliacion')
    @api.onchange('month_refinance','amount_refinance')
    def _compute_index_loan_fixed_fee(self):
        try:
            interest = (self.monthly_interest + self.contingency_fund) / 100
            index_quantity = (1 - (1 + interest) ** (-self.month_refinance))
            self.index_loan = interest / index_quantity if index_quantity != 0 else 0
            self.fixed_fee = self.amount_refinance * self.index_loan
        except:
            self.index_loan = 0
    def init_refinance(self):
        """Entrada del botón: verifica pagos programados y, si hay, abre confirmación."""
        self.ensure_one()
        programmed = self.data_loan_id.loan_payment_ids.filtered(lambda p: p.state == 'scheduled')
        if programmed:
            # --- Construir etiquetas de periodo únicas y ordenadas ---
            period_labels = []
            for p in programmed:
                val = getattr(p, 'period', False)  # si tu campo es period_id, igual funciona por display_name
                period_labels.append(val)
            # únicos y ordenados
            unique_periods = sorted(set(period_labels))
            periods_str = ', '.join(unique_periods) if unique_periods else _('(sin periodo)')

            message = _(
                "El préstamo tiene pagos PROGRAMADOS para el siguiente ciclo.\n\n"
                "- N° pagos programados: %(n)d\n"
                "- Períodos: %(periods)s\n\n"
                "Si continúas, el sistema procederá con el refinanciamiento igualmente."
            ) % {'n': len(programmed), 'periods': periods_str}

            return {
                'type': 'ir.actions.act_window',
                'name': _('Confirmar refinanciamiento'),
                'res_model': 'loan.refinance.confirm.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_original_wizard_id': self.id,
                    'default_message': message,
                }
            }
        # Si no hay programados, ejecutar directamente
        return self._do_refinance()

    def _do_refinance(self):
        """Ejecución real del refinanciamiento (crea el nuevo loan y cambia estado del actual)."""
        self.ensure_one()
        new_loan = self.env['loan.application'].create({
            'name': self.name,
            'type_loan': 'regular',
            'partner_id': self.data_loan_id.partner_id.id,
            'months_quantity': self.month_refinance,
            'amount_loan_dollars': self.amount_refinance,
            'date_application': self.date_refinance,
            'refinance_loan_id': self.data_loan_id.id,
            'amount_devolution': self.amount_delivered,
            'interest_day_rest': self.interest_days_rest,
            'total_interest_month_surpluy': self.interest_days_rest,
            'state': 'init',
        })
        new_loan._onchange_amount_loan_dollars()
        new_loan._onchange_amount_devolution()
        if not new_loan:
            raise ValidationError(_('Error en el proceso de refinanciamiento'))

        self.data_loan_id.state = 'refinanced' if not self.flag_expansion else 'expansion'

        return {
            'type': 'ir.actions.act_window',
            'name': _('Préstamo'),
            'view_mode': 'form',
            'res_model': 'loan.application',
            'res_id': new_loan.id,
            'target': 'current',
        }

    @api.depends('amount_refinance','flag_expansion')
    def _compute_amount_delivered(self):
        for rec in self:
            if rec.flag_expansion == False:
                if rec.capital_rest_scheduled > 0:
                    rec.amount_delivered = rec.amount_refinance - rec.capital_rest_scheduled - rec.interest_days_rest
                else:
                    rec.amount_delivered = rec.amount_refinance - rec.capital_rest - rec.interest_days_rest
            else:
                if rec.capital_rest_scheduled > 0:
                    rec.amount_delivered = rec.amount_refinance - rec.capital_rest_scheduled
                else:
                    rec.amount_delivered = rec.amount_refinance - rec.capital_rest
