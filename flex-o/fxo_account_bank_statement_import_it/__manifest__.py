# -*- encoding: utf-8 -*-
{
	'name': 'Fxo Importador de Lineas de Extractos Bancarios',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': [
		'account_bank_statement_import_it',
		'fields_gamma',
	],
	'version': '1.0',
	'description':"""
	Modulo para importar Lineas de Extractos Bancarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/data.xml',
		'views/account_bank_statement_line.xml',
		],
	'installable': True
}
