# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Theme Negocio',
    'description': 'Theme Negocio business & ecommerce theme',
    'category': 'Theme/Ecommerce',
    'sequence': 1000,
    'version': '1.0',
    'author': 'Adventumweb',
    'support': 'megatheme@gmail.com',
    'license' : 'OPL-1',
    'depends': ['website', 'website_theme_install'],
    'data': [
        'views/customize_model.xml',
        'views/HeaderStyle.xml',
    ],
    'live_test_url': 'http://theme-negocio.adventumweb.com/',
	'images': [ 'static/description/preview.jpg','static/description/priview_screenshot.jpg'],
    'price': 99.00,
    'currency': 'EUR',
    'application': False
}
