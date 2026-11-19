# -*- encoding: utf-8 -*-
{
	'name'    : 'Descripcion Automatizada',
	'category': 'account',
	'author'  : 'FLEXXOONE',
	'version' : '1.0',

	'description':"""
		Nueva descripcion para Facturas  con Lotes
	""",
	
	'auto_install': False,
	'demo'        : [],
	'depends'     : ['kardex_fisico_it', 'product_expiry', 'ctx_product_lot_expiry_date', 'ebill'],
	'data'        :	[
		'views/main_parameter.xml',
		'views/product_template.xml',
		'views/stock_picking.xml',
		'views/account_move.xml',
		'wizard/move_line_description_wizard.xml',
	],
	'installable' : True
}
