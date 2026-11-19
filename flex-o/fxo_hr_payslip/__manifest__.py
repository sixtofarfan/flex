# -*- encoding: utf-8 -*-
{
	'name': 'Fxo HR Payslip',
	'category': 'hr',
	'author': 'Flexxoone',
	'depends': [
		'hr_payroll', 
		'hr_fields_it',
		'fxo_hr_print_contract',
	],
	'version': '1.0',
	'description':"""
	Modulo para agregar vista pivot en planillas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/hr_payslip_run_view.xml',
		'views/hr_payslip_run_wd_view.xml',
	],
	'installable': True
}