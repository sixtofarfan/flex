# -*- encoding: utf-8 -*-
{
	'name': 'Importador de Saldos Iniciales IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	Sub-menu para importar saldos de Cliente y Proveedores
	""",

    'author': "Ing. Jean Paul Casis",
    'website': "http://soft.pvodoo.com",

	'auto_install': False,
	'demo': [],
	'data':	[
		'views/import_move_apertura_it.xml'
		],
	'installable': True
}
