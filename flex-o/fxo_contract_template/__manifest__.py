# -*- encoding: utf-8 -*-
{
	'name': 'Fxo Contract Template',
	'category': 'account',
	'author': 'Flexxoone',
	'website': 'http://flexxoone.com',
	'depends': ['sale_subscription', 'report_tools', 'popup_it', 'fxo_feasibility', 'fxo_account_bank_extend'],
	'version': '1.0',
	'description':"""
	Modulo para Generar Formato de Contrato en Suscripciones
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'data/contract_main_parameter.xml',
		'views/contract_main_parameter.xml',
		'views/sale_subscription.xml',
		'views/res_partner.xml',
	],
	'installable': True
}
