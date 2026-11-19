# -*- coding: utf-8 -*-
{
	'name': "Fxo Account Payment Application",
	'description': """
		Modulo para aplicar pagos de forma masiva y llevar un registro de los mismos
	""",
	'author': "Flexxoone",
	'depends': [
		#'fxo_payment_request',
		'fxo_account_payment_multidisengage',
		'jp_advance_payment_widget',
	],
	'website': "http://soft.pvodoo.com",
	'category': 'account',
	'version': '0.1',
	'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/data.xml',
		'views/account_payment_application.xml',
		'views/main_parameter.xml',
		'wizard/account_payment_application_wizard.xml',
		'wizard/get_invoices_wizard.xml',
	],
}
