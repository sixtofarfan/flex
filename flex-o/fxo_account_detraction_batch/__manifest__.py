# -*- coding: utf-8 -*-
{
	'name': "Fxo Account Invoice Control",
	'description': """
		Modulo para Generar Detracciones en Multiples facturas
	""",
	'author': "Flexxoone",
	'depends': ['base', 'account', 'jp_automate_multipayment'],
	'category': 'account',
	'version': '1.0',
	'data': [
		'security/security.xml',
		'views/account_move.xml',
		'wizard/detraction_batch_wizard.xml',
	],
}