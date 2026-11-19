# -*- encoding: utf-8 -*-
{
	'name': 'Fxo Hr Multiple Payment',
	'category': 'hr',
	'author': 'Flexxoone',
	'website': 'http://flexxoone.com',
	'depends': ['fxo_account_multiple_payment',
				'hr_fields_it'],
	'version': '1.0',
	'description':"""
	Modulo para Generar Pagos Masivos en distintos bancos
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'data/data.xml',
			'views/multiple_payment_bbva_cts.xml',
			'views/multiple_payment_bbva_slip.xml',
			'views/multiple_payment_bcp_cts.xml',
			'views/multiple_payment_bcp_slip.xml',
			'views/multiple_payment_interbank_cts.xml',
			'views/multiple_payment_interbank_slip.xml',
			'views/multiple_payment_scotiabank_cts.xml',
			'views/multiple_payment_scotiabank_slip.xml',
			'views/account_menus.xml',],
	'installable': True
}
