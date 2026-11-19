# -*- encoding: utf-8 -*-
{
	'name': 'Fxo Hr Voucher IT Extend',
	'category': 'hr',
	'author': 'Flexxoone',
	'depends': [
		'hr_payroll', 
		'hr_voucher_it',
		'fxo_hr_fields',
	],
	'version': '1.0',
	'description':"""
	Modulo para agregar campos en boleta de pago de nominas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/hr_main_parameter.xml',
	],
	'installable': True
}