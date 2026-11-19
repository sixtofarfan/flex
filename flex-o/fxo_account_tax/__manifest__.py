# -*- coding: utf-8 -*-
{
	'name': "Fxo Account Tax",
	'description': """
		Modulo para agregar campos diario y tipo de documento en impuestos para filtros en facturas
	""",
	'author': "Flexxoone",
	'depends': [
		'account',
        'account_fields_it',
	],
	'website': "http://soft.pvodoo.com",
	'category': 'account',
	'version': '0.1',
	'data': [
		'security/ir.model.access.csv',
		'views/main_parameter.xml',
	],
}