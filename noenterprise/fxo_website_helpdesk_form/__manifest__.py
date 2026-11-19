# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Online Ticket Submission',
    'category': 'Website/Website',
    'sequence': 58,
    'summary': 'Qualify helpdesk queries with a website form',
    'depends': [
        # SFR para activar website quitar comentarios
        #'website_helpdesk_form',
        'account',
        'fxo_feasibility',
        'mail',
        'fxo_res_partner_collection',
    ],
    'description': """

    """,
    'data': [
        'views/helpdesk_views.xml',
        # SFR para activar website quitar comentarios
        #'views/helpdesk_templates.xml',
        'security/ir.model.access.csv'
    ],
    'license': 'OEEL-1',
}
