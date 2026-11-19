# -*- coding: utf-8 -*-
{
    'name': 'Fxo Accounting Dashboards',
    'category': 'account',
    'author': 'Flexxoone',
    'version': '1.0',
    'depends': ['account_purchase_rep_it', 'fxo_account_higher_rep_it2', 'fields_gamma'],
    'description': """
Accounting dashboards: Purchase Register and Analytic Ledger
=============================================================
* What it does: adds the main menu "Accounting Dashboards" with two interactive
  dashboards (Purchase Register and Analytic Ledger): filters by company, fiscal
  year, dates and currency; KPIs, charts, searchable table with links to the
  vouchers, native list / pivot for deeper analysis and Excel (with formulas) / CSV.
  It also adds to the existing reports the account in the Purchase Register and
  the account name, 2-digit ledger account, cost center and line label in the
  Analytic Ledger.
* Configuration: none. Access with the group "Show Full Accounting Tables".
* Usage: Accounting Dashboards > Purchase Register / Analytic Ledger. The
  existing wizards in Accounting > Reports keep working with the new columns.
    """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/purchase_register_views.xml',
        'views/ledger_views.xml',
        'views/expense_analysis_views.xml',
        'views/legacy_views.xml',
        'views/menus.xml',
    ],
    'qweb': ['static/src/xml/dashboards.xml'],
    'auto_install': False,
    'installable': True,
    'application': True,
}
