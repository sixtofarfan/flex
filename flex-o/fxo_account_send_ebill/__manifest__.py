# -*- coding: utf-8 -*-
{
	'name': "Fxo Account Send Ebill",
	'description': """
		Modulo para enviar de forma masiva cpe's
	""",
	'author': "Flexxoone",
	'depends': [
		'ebill',
		'fxo_subscription_invoice_extend',
		'l10n_pe_cpe',
	],
	'website': "http://soft.pvodoo.com",
	'category': 'account',
	'version': '0.1',
	'data': [
		'views/account_move.xml',
		'views/main_parameter.xml',
		'views/res_partner.xml'
	],
}