from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


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
        partner_loan = self.env['loan.application'].search([('state', '=', 'progress')])
        nominal_relationship = self.env['nominal.relationship.mindef.loan']
        # Acción para conciliar los pagos de aportes
        period = self.month + '/' + self.year
        filing_cabinet_ids = self.env['nominal.relationship.mindef.loan'].search(
            [('period_process', '=', period), ('state', '=', 'draft')])
        partner_loan_ids = self.env['loan.application'].search(
            [('state', '=', 'progress')])
        for partner in partner_loan_ids:
            search_partner = filing_cabinet_ids.filtered(lambda x: x.eit_item == partner.partner_id.code_contact)
            if search_partner:
                verify_period = partner.loan_payment_ids.filtered(lambda x:x.period == period)
                verify_amount_returned_coa = partner.loan_payment_ids.filtered(lambda x:x.amount_returned_coa == 0)
                if verify_period:
                    verify_period.commission_min_def = search_partner.comision
                    # verify_period.amount_returned_coa = search_partner.tot2
                    verify_period.confirm_ministry_defense()
                    if verify_amount_returned_coa:
                        verify_period.amount_returned_coa = search_partner.tot2
                    search_partner.date_process = self.date_field_select
                    search_partner.state = 'reconciled'
                    search_partner.period_process = self.month + '/' + self.year
                else:
                    search_partner.write({'state': 'no_reconciled'})
                    search_partner.write({'period_process': self.month + '/' + self.year})
                    search_partner.write({'date_process': self.date_field_select})
                # mo.ministry_defense()
                # mo.onchange_income()
        array_no_reconciled = filing_cabinet_ids.filtered(lambda x: x.period_process == period and x.state == 'draft')
        no_reconciled = len(array_no_reconciled)
        context = {'default_message': 'Se han conciliado ' + str(
            len(filing_cabinet_ids) - no_reconciled) + ' registros de ' + str(len(filing_cabinet_ids))}
        return {
            'name': 'Registros conciliados',
            'type': 'ir.actions.act_window',
            'res_model': 'alert.message',
            'view_mode': 'form',
            'view_type': 'form',
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