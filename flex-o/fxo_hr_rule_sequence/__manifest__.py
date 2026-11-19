# -*- encoding: utf-8 -*-
{
	'name': 'FXO Hr Salary Rule Sequence',
	'category': 'hr',
	'author': 'Flexxoone',
	'depends': ['hr_payroll'],
	'version': '1.0',
	'description':"""
	Modulo to add espaces for sequence in hr.salary.rule
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/hr_salary_rule.xml',
			 'wizard/hr_salary_rule_wizard.xml'],
	'installable': True
}