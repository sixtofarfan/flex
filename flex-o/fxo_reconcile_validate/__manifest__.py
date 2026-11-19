# -*- encoding: utf-8 -*-
{
	'name': 'Fxo Reconcile Validate',
	'category': 'account',
	'author': 'Flexxoone',
	'depends': [
        'fxo_account_custom_reconcile'
	],
	'version': '1.0',
	'description':"""
	Modulo para arreglar errores en asientos generados con custom_reconcile
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/account_bank_statement.xml'],
	'installable': True
}