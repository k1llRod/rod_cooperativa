from odoo import models, fields, api, _



class NominalRelationshipMindefLoan(models.Model):
    _name = 'nominal.relationship.mindef.loan'
    _description = 'Relacion nominal prestamos mindef'

    name = fields.Char(string='N')
    management = fields.Char(string='Gestion')
    month = fields.Char(string='Mes')
    supporting_document = fields.Char(string='Documento respaldo')
    eit_codorg = fields.Char(string='eit_codorg')
    eit_codrep = fields.Char(string='eit_codrep')
    distribution = fields.Char(string='Reparticion')
    group = fields.Char(string='Grupo')
    group_description = fields.Char(string='Descripcion del grupo')
    identification = fields.Char(string='Identificador')
    creditor = fields.Char(string='Acreedor')
    code_concept = fields.Char(string='Codigo concepto')
    code_creditor = fields.Char(string='Codigo acreedor')
    bank_account = fields.Char(string='Cuenta bancaria')
    personal_code = fields.Char(string='Codigo personal')

    organism = fields.Char(string='Organismo')
    eit_item = fields.Char(string='Item EIT')
    ci = fields.Char(string='Cédula de identidad')
    degree = fields.Char(string='Grado')
    mension = fields.Char(string='Mension')
    name_complete = fields.Char(string='Nombre completo')
    amount_bs = fields.Float(string='Monto Bs')
    amount_usd = fields.Float(string='Monto USD')
    tot2 = fields.Float(string='Tot2')
    comision = fields.Float(string='Comision')
    date_register = fields.Date(string='Fecha de registro', default=fields.Date.today())
    date_process = fields.Date(string='Fecha de proceso')
    loan_regular = fields.Boolean(string='Regular')
    loan_emergency = fields.Boolean(string='Emergencia')
    period_process = fields.Char(string='Periodo de proceso')
    diference = fields.Float(string='Diferencia')
    observation = fields.Char(string='Observacion')
    state = fields.Selection([('draft', 'Borrador'), ('no_reconciled', 'No conciliado'), ('reconciled', 'Conciliado'),
                              ('observed', 'Observado')], string='Estado')

    def homologate_data_mindef_loan(self):
        return {
            'name': 'Homologar cuotas de prestamos MINDEF',
            'type': 'ir.actions.act_window',
            'res_model': 'homolagate.form.loan',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }