# -*- coding: utf-8 -*-
{
    'name': "CPE Import",

    'summary': """
        Import xml invoice files from SUNAT
        """,

    'description': """
        This module imports the invoices of xml files sent 
        to the email account configured in the journal.
    """,

    'author': "Flexxoone & Jean Paul Casis",
    'website': "http://soft.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_fields_it'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        'data/data.xml',
        'wizards/import_file.xml',
        'views/invoice_view.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
