# -*- coding: utf-8 -*-
{
    'name': "Automate HR Multipayment",

    'summary': """
        Extend jp_automate_multipayment module""",

    'description': """
        This module extends the module jp_automate_multipayment to handle
        hr payments.
    """,

    'author': "Flexxone",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'jp_automate_multipayment',
        'hr_base_it',
        'hr_social_benefits',
        'report_tools',
        'fxo_hr_massive_advances',
    ],

    # always loaded
    'data': [
        'data/hr_type_document.xml',
        'views/multipayment_advance_it.xml',
        'views/hr_main_parameter.xml',
        'views/hr_payslip_run.xml',
    ],
}
