# -*- coding: utf-8 -*-
{
    'name': "jp_not_docmiciliated_data",

    'summary': """
        Add functionallity to non domicialiated partners""",

    'description': """
        This module adds functionallity to non domiciliated page in
        partner so you can select the items from SUNAT lists and not
        add them manually.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://soft.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account_fields_it'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/table_35.xml',
        'data/table_25.xml',
        'data/table_27.xml',
        'view/res_country.xml',
        'view/res_partner.xml',
        'view/table_25.xml',
        'view/table_27.xml',
        # 'views/templates.xml',
    ],
}
