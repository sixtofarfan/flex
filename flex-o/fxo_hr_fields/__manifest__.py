# -*- encoding: utf-8 -*-
{
	'name': 'Fxo Hr Fields',
	'category': 'hr',
	'author': 'Flexxoone',
	'website': 'http://flexxoone.com',
	'depends': [
		'hr_fields_it',
		'hr_vacations',
	],
	'version': '1.0',
	'description':"""
	Modulo para agregar campos a la Planilla
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/hr_contract.xml',
		'views/hr_payslip.xml',
		'views/hr_vacation_control.xml',
	],
	'installable': True
}