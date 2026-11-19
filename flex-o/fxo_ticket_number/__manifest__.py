# -*- encoding: utf-8 -*-
{
	'name': 'Fxo Ticket Number',
	'category': 'helpdesk',
	'author': 'Flexxoone',
	'website': 'http://flexxoone.com',
	'depends': ['helpdesk', 'website_helpdesk_form'],
	'version': '1.0',
	'description':"""
	Modulo para agregar secuenciador en tickets
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/data.xml',
		'views/helpdesk_ticket.xml',
		'views/helpdesk_templates.xml',
	],
	'installable': True
}