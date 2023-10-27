from odoo import api, fields, models, tools, _

class RecordsCabinetMinistryLoans(models.Model):
    _name ='records.cabinet.ministry.loans'
    _description = 'Records Cabinet Ministry Loans'

    name = fields.Char(string='Name', required=True)
