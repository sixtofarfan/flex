# -*- encoding: utf-8 -*-
{
	'name': 'Fxo Hr Fixed Inputs',
	'category': 'hr',
	'author': 'Flexxoone',
	'website': 'http://flexxoone.com',
	'depends': ['hr_fields_it'],
	'version': '1.0',
	'description':"""
	Modulo para agregar Importador de Conceptos Fijos en Lotes de Nomina
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/hr_fixed_inputs.xml',
		'views/hr_payslip.xml',
		'views/hr_payslip_run.xml',
	],
	'installable': True
}