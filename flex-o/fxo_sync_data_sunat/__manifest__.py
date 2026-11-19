# -*- encoding: utf-8 -*-
{
	'name': 'Sync Data Sunat',
	'category': 'Sync Data',
	'author': 'FLEXXOONE',
	'depends': ['account', 'l10n_pe_server', 'l10n_pe_cpe'],
	'version': '1.0',
	'description':"""
		Sincronizacion de data desde bd.
	""",
	'auto_install': False,
	'demo': [],
    'qweb' : [],
	'data':	['views/sync_data_in_view.xml',
			'views/sync_data_server_view.xml',
			#'views/res_config.xml',
			'views/company_view.xml',
			'data/sync_data.xml',
			'security/ir.model.access.csv',
			],
	'installable': True
}
