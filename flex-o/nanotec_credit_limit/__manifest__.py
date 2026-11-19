# -*- coding: utf-8 -*-
{
    'name' : 'Gestión de Lineas de Credito',
    'version': '1.0',
    "author": "Nanotec",
    'summary': '',
    'category': 'Others',
    'description':
        """
Gestión de Lineas de Creditos
        """,
    'depends' : ['base', 'account', 'sale', 'base_table', 'account_fields_it', 'sale_parameter', 'popup_it'],
    #,'fxo_sale_order_approve'
    'data': [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/sale_config_view.xml",
        "views/wizard_confirm.xml",
        "views/wizard_confirm_manager.xml",
        "security/ir.model.access.csv",
        "data.xml",
        "views/workflow.xml",
        "views/res_partner_view.xml",
        "views/credit_view.xml",
        "views/account_payment_term.xml",
        #"views/credit_approve.xml",
        "views/sale_order.xml",
        "views/sale_order_approval.xml",
    ]
}
