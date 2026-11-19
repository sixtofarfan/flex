# -*- coding: utf-8 -*-
{
    'name':
    " FXO Proyecto Extencion",
    'summary':
        """  FXO Proyecto Extencion  """,
    'description':
        """ FXO Proyecto Extencion """,
    'author': "Jean Pierre L",
    'category': 'project',
    'version': '0.1',
    'depends':[
        'sale_timesheet',
        'project',
        'project_category',
        'fxo_feasibility',
        'fxo_project_aprovate',
        'fxo_sale_subscription_state_update',
        'account_base_it',
        'ebill',
        'odoo_job_costing_management',
        'project_advance_team',
        'material_purchase_requisitions',
        'project_enterprise',
        'project_status',
        'purchase',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/account_analytic_group.xml',
        'views/main_parameter.xml',
        'views/project.xml',
        'views/res_country_state.xml',
        'views/res_partner.xml',
        'views/wk_location_team.xml',
        'views/wk_team.xml',
        'views/ir_attachment.xml',
        'views/purchase_order.xml',
    ],
}
