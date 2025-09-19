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
    interest_days_rest_scheduled = fields.Float(string='Días de Interés Restantes Programados')
    total_capital_rest = fields.Float(string='Total Capital Restante')
    amount_refinance = fields.Float(string='Monto a Refinanciar', required=True)
    month_refinance = fields.Integer(string='Meses a Refinanciar', required=True)
    date_refinance = fields.Date(string='Fecha de Refinanciamiento', required=True)
    date_initial_loan = fields.Date(string='Fecha de inicio del prestamo')
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

    def _int_or_false(env, key):
        val = env['ir.config_parameter'].sudo().get_param(key)
        try:
            return int(val) if val and val not in ('False', 'false', '0') else False
        except (TypeError, ValueError):
            return False

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

        ICP = self.env['ir.config_parameter'].sudo()

        # Leer y convertir IDs de cuentas SIN helper
        raw_loan = ICP.get_param('rod_cooperativa.account_loan_id')
        raw_egreso = ICP.get_param('rod_cooperativa.account_egreso_id')
        raw_refi = ICP.get_param('rod_cooperativa.account_monto_refinanciamiento')
        raw_meses = ICP.get_param('rod_cooperativa.account_monto_meses_interes')  # clave corregida

        acc_loan_id = int(str(raw_loan).strip()) if raw_loan and str(raw_loan).strip().isdigit() and str(
            raw_loan).strip() != '0' else False
        acc_egreso_id = int(str(raw_egreso).strip()) if raw_egreso and str(raw_egreso).strip().isdigit() and str(
            raw_egreso).strip() != '0' else False
        acc_refi_id = int(str(raw_refi).strip()) if raw_refi and str(raw_refi).strip().isdigit() and str(
            raw_refi).strip() != '0' else False
        acc_meses_interes_id = int(str(raw_meses).strip()) if raw_meses and str(raw_meses).strip().isdigit() and str(
            raw_meses).strip() != '0' else False

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
            # No asignamos cuentas aquí para no pelear con onchanges
            'state': 'init',
        })

        if not new_loan:
            raise ValidationError(_('Error en el proceso de refinanciamiento'))

        # Ejecuta cálculos que puedan pisar campos
        new_loan._onchange_amount_loan_dollars()
        new_loan._onchange_amount_devolution()
        new_loan._compute_change_dollars_bolivian()
        new_loan._onchange_interest_day_rest()

        # Ahora sí, escribe cuentas (Many2one) como enteros válidos
        write_vals = {}
        if acc_loan_id:
            write_vals['account_loan_id'] = acc_loan_id
        if acc_egreso_id:
            write_vals['account_egreso_id'] = acc_egreso_id
        if acc_refi_id:
            write_vals['account_monto_refinanciamiento'] = acc_refi_id
        if acc_meses_interes_id:
            write_vals['account_monto_meses_interes'] = acc_meses_interes_id

        if write_vals:
            new_loan.write(write_vals)

        # Cambia estado del préstamo original
        new_state = 'expansion' if self.flag_expansion else 'refinanced'
        self.data_loan_id.state = new_state

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
                    rec.amount_delivered = rec.amount_refinance - rec.capital_rest_scheduled - rec.interest_days_rest_scheduled
                else:
                    rec.amount_delivered = rec.amount_refinance - rec.capital_rest - rec.interest_days_rest
            else:
                if rec.capital_rest_scheduled > 0:
                    rec.amount_delivered = rec.amount_refinance - rec.capital_rest_scheduled
                else:
                    rec.amount_delivered = rec.amount_refinance - rec.capital_rest
