# -*- encoding: utf-8 -*-
{
	'name': 'Letras de Cambio - Account Bills of Exchange',

    'summary': """
        Gestión de letras de cambio. Management of bills of exchange.""",

    'description': """
		Este módulo proporciona funcionalidad a Odoo para intercambiar
		Facturas con letras de cambio. Gestionar las letras de cambio
		y controlar la fecha de vencimiento

		******

        This module provides functionallity to Odoo to exchange
		invoices with bills of exchange. Manage the bills of exchange
		and control due date.
    """,

    'author': "Ing. Jean Paul Casis",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Accounting',
    'version': '13.1.0.0.0',
    "license": "AGPL-3",
    'support': 'pollarolas@gmail.com',
    'website': 'https://www.odoo.com',
    # 'license': 'OPL-1',
    'images': ['static/description/banner.png'],

    # any module necessary for this one to work correctly
	'depends': [
		'account',
		'sale',
		'l10n_pe',
		# 'l10n_pe_currency_rate',
		'jp_currency_rate_live',
		# 'l10n_pe_vat',
		'account_debit_note',
		# 'account_base_it',
		'web_notify',
	],
	
    # always loaded
	'data':	[
		'security/group_bills.xml',
		'security/ir.model.access.csv',
		'data/attachment.xml',
		# 'data/boe_conf.xml',
		'data/einvoice_catalog_01.xml',
		'data/res_currency_data.xml',
		'data/sequences.xml',
		'data/sunat_payment_method_data.xml',
		'view/account_bill_form_view.xml',
		'view/account_advanced_bill_form_view.xml',
		'view/account_refinancing_form_view.xml',
		'view/account_bill_view.xml',
		'view/account_import_bill_form_view.xml',
		'view/account_move_views.xml',
		'view/account_journal.xml',
		'view/bank_disbursement.xml',
		'view/bill_print_view.xml',
		'view/send_to_bank.xml',
		'view/renew_bill.xml',
		'view/res_config_settings_views.xml',
		'view/account_boe_dashboard_view.xml',
		'view/res_currency_view.xml',
		'view/protest_payment.xml',   
		'view/hide_letras_it_menu.xml',
		'wizard/disburse_wizard.xml',
		'wizard/get_financial_expenses.xml',
		'wizard/get_renew_date.xml',
		'wizard/import_lines_wizard.xml',
		'wizard/pay_bill_wizard.xml',
		'wizard/renew_bill_wizard.xml',
		'wizard/send_to_bank_wizard.xml',
		'wizard/unique_bank_number_wizard.xml',
		'wizard/get_post_date_and_rate.xml',
		'template/layout_templates.xml',
		'template/planilla_bcp.xml',
		'template/planilla_bbva.xml',
		'template/bill_form_template.xml',
		'template/bill_template.xml',
		'template/bill_template_renew.xml',
		'template/refinancing_form_template.xml',
		],

	'installable': True,
    'application': True,
	'price': 3500,
	'currency': 'USD',
}
