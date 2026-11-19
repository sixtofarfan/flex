# -*- encoding: utf-8 -*-
{
	'name': 'FXO HR Massive Advances',
	'category': 'hr',
	'author': 'Flexxoone',
	'website': 'http://flexxoone.com',
	'depends': ['hr_fields_it', 'hr_advances_and_loans'],
	'version': '1.0',
	'description':"""
	Modulo para generar Adelantos de Quincena masivamente
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/hr_payslip_input_type.xml',
		'data/hr_salary_rule.xml',
		'views/hr_advance.xml',
		'views/hr_main_parameter.xml',
		'views/hr_payslip_run.xml',
	],
	'installable': True
}