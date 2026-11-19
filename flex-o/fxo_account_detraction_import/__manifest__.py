# -*- coding: utf-8 -*-
{
	'name': "Fxo Account Detraction Import",
	'description': """
		Modulo para Importar campos fecha y nro de operacion de 2 Formatos de Detraccion distintos
	""",
	'author': "Flexxoone",
	'depends': ['base', 'account', 'jp_automate_multipayment'],
	'category': 'account',
	'version': '1.0',
	'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/data.xml',
		'views/account_detraction_import.xml',
	],
}