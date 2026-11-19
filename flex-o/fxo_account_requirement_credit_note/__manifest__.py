# -*- encoding: utf-8 -*-
{
	'name': 'Fxo Account Requirement Credit Note',
	'category': 'account',
	'author': 'Flexxoone',
	'website': 'http://flexxoone.com',
	'depends': ['account', 'account_base_it', 'ebill', 'sale','fxo_account_analytic' ,'fxo_subscription_invoice_extend','approvals', 'sales_team'],
	'version': '1.0',
	'description':"""
	Modulo para Generar Solicitudes de Notas de Credito
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/data.xml',
		'views/einvoice_catalog_09_internal.xml',
		'views/request_credit_note.xml',
		'views/crm_team.xml',
		'views/approval_request.xml',
		'views/approval_category.xml',
		'wizard/request_credit_note_wizard.xml',
		'views/account_move.xml',
		'views/menus.xml',
	],
	'installable': True
}
