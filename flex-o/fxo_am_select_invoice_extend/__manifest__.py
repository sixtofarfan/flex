# -*- coding: utf-8 -*-
{
	'name': "Fxo Am Select Invoice",
	'description':
		""" 
		Modulo para agregar order_id en funcion _onchange_account_line_id
		""",
	'author': "Flexxoone",
	'website': "http://flexxoone.com/",
	'category': 'account',
	'version': '1.0',
	'depends':[
			'jp_am_select_invoice','fxo_payment_request'
			],
	'data': [
		'views/move_line.xml'
	],
}