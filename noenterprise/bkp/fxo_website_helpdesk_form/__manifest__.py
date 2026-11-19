# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Online Ticket Submission',
    'category': 'Website/Website',
    'sequence': 58,
    'summary': 'Qualify helpdesk queries with a website form',
    'depends': [
        'website_helpdesk_form','account','project','sale_subscription',
    ],
    'description': """

    """,
    'data': [
        'views/helpdesk_views.xml',
        'views/helpdesk_templates.xml',
        'security/ir.model.access.csv'
    ],
    'license': 'OEEL-1',
}
