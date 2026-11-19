# -*- encoding: utf-8 -*-
{
	'name': 'Fxo Hr Social Benefits',
	'category': 'hr',
	'author': 'Flexxoone',
	'depends': [
		'hr_base_it',
		'hr_social_benefits',
		'fxo_hr_fields',
		'fxo_hr_print_contract',
		'hr_fifth_category_certificate',
	],
	'version': '1.0',
	'description':"""
	Modulo para obtener la remuneracion computable del contrato y ya no del basico del mes
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'report/report_paperformat.xml',
		'report/templates.xml',
		'report/report.xml',
		'views/hr_liquidation.xml',
		'views/hr_main_parameter.xml',
		'views/hr_cts.xml',
		'wizard/hr_fifth_category_wizard.xml',
	],
	'installable': True
}