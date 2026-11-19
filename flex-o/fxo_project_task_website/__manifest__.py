# -*- coding: utf-8 -*-
{
    'name': "Project Task",

    'summary': """
        Add some fields to fron end purchase order""",

    'description': """
        This module add extra fields to purchase orders in front end
        so portal users can see ir the project have been finished and
        also the state of the order.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.flexxoone.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'project',
        'project_enterprise',
        'odoo_job_costing_management',
        'project_status',
        'fxo_project_extended',
        'fxo_feasibility',
    ],

    # always loaded
    'data': [
        'views/portal_templates.xml',
    ],
}
