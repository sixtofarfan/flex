# -*- encoding: utf-8 -*-
{
	'name': 'Pagos Masivo por Banco',
	'category': 'account',
	'author': 'ITGRUPO-PRESCOTT',
	'depends': ['account','account_base_it'],
	'version': '1.0',
	'description':"""
	Importar Recaudaciones Bancarias
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
	 'ac_cobranza_view.xml',
	 'security/ir.model.access.csv',	 
	],
	'qweb':[],
	'installable': True
}
