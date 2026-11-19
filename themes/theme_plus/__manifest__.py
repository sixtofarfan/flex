# -*- coding: utf-8 -*-
{
    'name': "Theme Plus",
	'category': 'Theme/Creative',
	'version': '13.0',   
    'author': "Icon Technology",
    'website': "http://www.icontechnology.in",
    'support':  'info@icontechnology.in',
    'maintainer': 'Icon Technology',
	'summary': 'Fully Responsive, Clean, Modern Odoo Business Theme',
    'description': 'Plus Theme is a powerful one page Odoo theme designed for a Corporate or Agency Business design. It is a unique & clean Pixel Perfect Odoo theme Design with a creative modern look. Complete Design & all Sections very easy to customize and update using our new Snippets. It is built with various attractive features like easy to change different Color Schemes, Many Custom Designed Snippets, Manage Slider with content, Manage Partner, Manage Portfolio, Client testimonial etc many more. It can be suitable for corporate businesses, Agency, IT Service, Construction, Health & Fitness etc any type of small business.',
    'license': 'OPL-1',
	'price': 39.99,
	'currency': 'EUR',
    'live_test_url': "http://207.180.228.60:8071/",
    'images': [
        'static/description/plus.jpg',        
		'static/description/plus_screenshot.gif'
	],
	
    # any module necessary for this one to work correctly
    'depends': ['website', 'website_mass_mailing', 'website_crm'],
	
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/website_crm_data.xml',
        'views/theme_plus_navbar.xml',
        'views/snnipets.xml',
        'views/templates.xml',
        'views/assets.xml',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/theme_plus_demo_data.xml',
        'demo/res_company_demo.xml',
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
    'web_preload': True,
}
