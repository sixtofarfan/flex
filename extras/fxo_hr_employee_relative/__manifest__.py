# -*- encoding: utf-8 -*-
{
	'name': 'Fxo Hr Employee Relative',
	'category': 'hr',
	'author': 'Flexxoone',
	'depends': [
		'hr_payroll',
		'fxo_hr_fields',
	],
	'version': '1.0',
	'description':"""
	Modulo permite registrar familiares del empleado
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
        'security/ir.model.access.csv',
		'security/rules_security.xml',
        'views/hr_employee_child.xml',
		'views/hr_employee.xml',
    ],
	'installable': True
}