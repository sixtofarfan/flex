# -*- coding: utf-8 -*-
{
    'name': "Forma de pago",

    'summary': """
        Nueva resolución SUNAT""",

    'description': """
        Agrega funcionalidad a la factura electrónica para agregar los datos
        solicitados por la nueva resolución SUNAT, la cual solicita que se
        envien los datos del crédito otorgado, cantidad de cuotas, montos,
        moneda y fecha de vencimiento de cada cuota.
    """,

    'author': "Ing. Jean Paul Cais",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','sale','l10n_pe_cpe'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/account_move.xml',
        'views/account_payment_terms.xml',
        'wizard/bill_wizard.xml'
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
