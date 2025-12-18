from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class ReconcileLoan(models.TransientModel):
    _name = 'reconcile.loan'
    _description = 'Conciliar pagos de prestamos'

    date_payment = fields.Date(string="Fecha de pago", require=True, default=fields.Date.today())
    date_field_select = fields.Date(string="Fecha periodo", require=True, default=fields.Date.today() - relativedelta(months=1))
    month = fields.Char(string="Mes", compute="compute_date_format")
    year = fields.Char(string="Año", compute="compute_date_format")
    reconcile_records = fields.Integer(string="Registros para conciliar", readonly=True)
    # drawback = fields.Boolean(string="Reintegro", default=False)
    # months = fields.Many2many('month', string="Meses")
    correct_registry = fields.Integer(string="Corregir registros", readonly=True)
    reconciled_records = fields.Integer(string="Registros conciliados", readonly=True)
    outstanding_payments = fields.Integer(string="Pagos pendientes", compute='onchange_partner_status_especific',readonly=True)
    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('letter_a', 'Letra "A" de disponibilidad'),
                                                 ('passive_reserve_a', 'Reserva pasivo "A"'),
                                                 ('passive_reserve_b', 'Reserva pasivo "B"'),
                                                 ('leave', 'Baja')], string='Tipo de asociado')

    @api.depends('date_field_select')
    def compute_date_format(self):
        for record in self:
            if record.date_field_select == False:
                record.year = 'Seleccionar fecha'
                record.month = 'Seleccionar fecha'
            else:
                record.month = record.date_field_select.strftime('%m')
                record.year = record.date_field_select.strftime('%Y')
                period = record.month + '/' + record.year
                record.reconcile_records = len(self.env['nominal.relationship.mindef.loan'].search(
                    [('period_process', '=', period), ('state', '=', 'draft')]))
                record.correct_registry = len(self.env['nominal.relationship.mindef.loan'].search(
                    [('period_process', '=', period), ('state', '=', 'no_reconciled')]))
                record.reconciled_records = len(self.env['nominal.relationship.mindef.loan'].search(
                    [('period_process', '=', period), ('state', '=', 'reconciled')]))

    @api.depends('partner_status_especific')
    def onchange_partner_status_especific(self):
        if self.partner_status_especific:
            self.outstanding_payments = len(self.env['partner.payroll'].search(
                [('outstanding_payments', '>', '0'), ('state', '=', 'process'),
                 ('partner_status_especific', '=', self.partner_status_especific)]))
        else:
            self.outstanding_payments = len(self.env['partner.payroll'].search(
                [('outstanding_payments', '>', '0'), ('state', '=', 'process')]))

    def action_reconcile(self):
        self.ensure_one()

        period = f"{self.month}/{self.year}"

        Filing = self.env['nominal.relationship.mindef.loan']
        Loan = self.env['loan.application']

        # 1) Traer gabinetes (draft) del periodo
        filing_cabinet_ids = Filing.search([
            ('period_process', '=', period),
            ('state', '=', 'draft')
        ])

        if not filing_cabinet_ids:
            raise UserError(_("No hay registros en borrador para el período %s.") % period)

        # 2) Indexar por eit_item para búsqueda O(1)
        #    OJO: si hay duplicados por eit_item, esto se pisa. Ver nota al final.
        filing_by_eit = {rec.eit_item: rec for rec in filing_cabinet_ids if rec.eit_item}

        # 3) Traer préstamos en progreso (una sola vez)
        partner_loan_ids = Loan.search([('state', '=', 'progress')])
        if not partner_loan_ids:
            raise UserError(_("No hay préstamos en progreso para conciliar."))

        reconciled_count = 0

        # Estados válidos para “encontré pago del periodo pero aún conciliable”
        conciliable_states = ('scheduled', 'draft', 'pending', 'not_discounted', False)

        for loan in partner_loan_ids:
            code_contact = loan.partner_id.code_contact
            if not code_contact:
                continue

            filing = filing_by_eit.get(code_contact)
            if not filing:
                continue

            # Pagos del período (una sola vez)
            payments_period = loan.loan_payment_ids.filtered(lambda p: p.period == period)
            if not payments_period:
                # No hay pagos del periodo -> marca gabinete como no conciliado
                filing.write({
                    'state': 'no_reconciled',
                    'period_process': period,
                    'date_process': self.date_field_select,
                })
                continue

            # Pagos del período que estén en estados conciliables
            verify_period = payments_period.filtered(lambda p: p.state in conciliable_states)
            if not verify_period:
                # Si hay pagos del período pero ninguno conciliable -> lo marco igual como no conciliado
                filing.write({
                    'state': 'no_reconciled',
                    'period_process': period,
                    'date_process': self.date_field_select,
                })
                # y marco esos pagos del período como no descontados
                payments_period.write({'state': 'not_discounted'})
                continue

            # 4) Conciliar: aplicar comisión / retorno solo al/los pagos del periodo conciliables
            vals_payment = {
                # 'commission_min_def': filing.comision,
                'amount_returned_coa': filing.tot2,
            }
            verify_period.write(vals_payment)
            verify_period.confirm_ministry_defense()
            verify_period.write({'state': 'ministry_defense'})

            # 5) Marcar regularidad del préstamo según tu regla
            filing.write({
                'loan_regular': bool(verify_period.amount_total_bs >= filing.amount_bs),
                'date_process': self.date_field_select,
                'state': 'reconciled',
                'period_process': period,
            })

            reconciled_count += 1

        # 6) Resumen final correcto según estados reales
        total = len(filing_cabinet_ids)
        no_reconciled = len(filing_cabinet_ids.filtered(lambda r: r.state != 'reconciled'))

        context = {
            'default_message': _(
                "Se han conciliado %s registros de %s"
            ) % (reconciled_count, total)
        }

        return {
            'name': _('Registros conciliados'),
            'type': 'ir.actions.act_window',
            'res_model': 'alert.message',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }
    def compute_reconcile_records(self):
        for record in self:
            record.correct_registry = len(record.env['nominal.relationship.mindef.contributions'].search(
                [('period_process', '=', record.month + '/' + record.year), ('state', '=', 'reconc')]))

    def register_missing_payments(self):
        for record in self:
            record.env['nominal.relationship.mindef.contributions'].search(
                [('period_process', '=', record.month + '/' + record.year), ('state', '=','reconc')]).write({'state': 'draft'})