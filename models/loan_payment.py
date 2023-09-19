from odoo import api, fields, models, tools, _

class LoanPayment(models.Model):
    _name = 'loan.payment'
    _description = 'Pagos de prestamos'

    name = fields.Char(string='Codigo de pago', required=True)
    loan_application_ids = fields.Many2one('loan.application', string='Solicitud de prestamo', required=True)
    type_payment = fields.Selection([('1', 'Abono'), ('2', 'Transferencia')], string='Tipo de pago')
    date = fields.Date(string='Fecha de pago', required=True)
    capital_initial = fields.Float(string='Capital inicial')
    capital_index_initial = fields.Float(string='Capital')
    mount = fields.Float(string='Cuota fija')
    interest = fields.Float(string='Interes', compute='_compute_interest', store=True)
    interest_base = fields.Float(string='0.7%', compute='_compute_interest', store=True)
    res_social = fields.Float(string='F.C. 0.04%', compute='_compute_interest', store=True)
    balance_capital = fields.Float(string='Saldo capital', compute='_compute_interest', store=True)
    percentage_amount_min_def = fields.Float(string='%MINDEF')
    interest_month_surpluy = fields.Float(string='M/E', related='loan_application_ids.interest_month_surpluy')
    amount_total = fields.Float(string='D/MINDEF $', compute='_compute_interest', store=True)
    amount_total_bs = fields.Float(string='D/MINDEF Bs', compute='_change_amount_total_bs', store=True)
    state = fields.Selection([('earring', 'Pendiente'), ('paid', 'Pagado')], string='Estado', default='draft')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Moneda', related='loan_application_ids.currency_id')
    currency_id_dollar = fields.Many2one('res.currency', string='Moneda en Dólares',
                                         default=lambda self: self.env.ref('base.USD'))
    @api.depends('amount_total')
    def _change_amount_total_bs(self):
        for rec in self:
            rec.amount_total_bs = rec.amount_total * rec.currency_id_dollar.inverse_rate

    # @api.depends('mount')
    # def _compute_interest(self):
    #     for rec in self:
    #         rec.interest = rec.mount * 0.1

    @api.depends('capital_initial','balance_capital','interest','res_social')
    def _compute_interest(self):
        percentage_interest = float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.monthly_interest'))
        contingency_found = float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa.contingency_fund'))

        interest = (percentage_interest + contingency_found)/100
        for rec in self:
            rec.interest = rec.capital_initial * interest
            rec.interest_base = rec.capital_initial * round((percentage_interest/100),3)
            rec.capital_index_initial = round(rec.mount - rec.interest,2)
            rec.balance_capital = rec.capital_initial - rec.capital_index_initial
            rec.res_social = rec.capital_initial * round((contingency_found/100),4)
            rec.amount_total = rec.mount + rec.percentage_amount_min_def + rec.interest_month_surpluy








