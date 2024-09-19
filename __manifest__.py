# -*- coding: utf-8 -*-
{
    'name': "rod_cooperativa",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts','mail','report_xlsx','account'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/loan_application.xml',
        'views/partner_category.xml',
        'views/loan_payments.xml',
        'views/family.xml',
        'views/finalized_loan.xml',
        'data/sequence.xml',
        'views/nominal_relationship_mindef_loan.xml',
        'views/rod_cooperativa_menuitem.xml',
        'views/post_mortem.xml',
        'wizard/form_refinance.xml',
        'wizard/homologate_form_loan.xml',
        'wizard/reconcile_loan.xml',
        'wizard/form_report_xlsx.xml',
        'wizard/form_deceased.xml',
        'wizard/payment_post_mortem.xml',
        'wizard/form_finalized_loan.xml',
        # 'wizard/form_finalized_contributions.xml',
        'views/res_partner.xml',
        'reports/report.xml',
        'reports/loan_application_pdf.xml',
        'reports/payment_statement_loan.xml',
    ],

}
