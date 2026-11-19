# -*- encoding: utf-8 -*-
{
	'name': 'Fxo Account Multiple Payment',
	'category': 'account',
	'author': 'Flexxoone',
	'website': 'http://flexxoone.com',
	'depends': ['account_fields_it',
				'hr_social_benefits',
				'l10n_pe', 
				'l10n_latam_base',
				'fxo_account_bank_extend',],
	'version': '1.0',
	'description':"""
	Modulo para Generar Pagos Masivos en distintos bancos
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'data/l10n_latam_identification_type.xml',
			'views/multiple_payment_bbva.xml',
			'views/multiple_payment_bcp.xml',
			'views/multiple_payment_interbank.xml',
			'views/multiple_payment_scotiabank.xml',
			'views/account_menus.xml',
			'views/main_parameter.xml',
			'wizards/multiple_payment_wizard.xml'],
	'installable': True
}
