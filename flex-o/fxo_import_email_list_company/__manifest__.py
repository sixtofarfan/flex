# -*- coding: utf-8 -*-
{
    'name': "Fxo Import Email List Company",
    'description': """
       Permite crear una lista de correos con todos sus destinatarios por compañía.
    """,
    'author': "Flexxoone",
    'depends': ['mass_mailing', 'fxo_res_partner_category', 'fxo_res_partner_state'],
    'website': "http://soft.pvodoo.com",
    'category': 'Mail',
    'version': '0.1',
    'data': [
        'views/mailing_list_views.xml',
        'views/mailing_contact_view.xml',
        'views/mailing_mailing_views.xml',
        'wizard/import_email_list_wzd.xml',
    ],
}
