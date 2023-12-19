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
    'depends': ['base', 'contacts','mail'],

    # always loaded
    'data': [
        'views/res_config_settings.xml',
        'views/loan_application.xml',
        'views/partner_category.xml',
        'views/loan_payments.xml',
        'views/family.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/rod_cooperativa_menuitem.xml',
        'wizard/form_refinance.xml',
        'wizard/homologate_form_loan.xml',
        'wizard/reconcile_loan.xml',
        'views/res_partner.xml',
        'views/nominal_relationship_mindef_loan.xml',
    ],

}
