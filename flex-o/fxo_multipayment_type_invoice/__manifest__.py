# -*- coding: utf-8 -*-
{
    'name': 'Fxo Multipayment: invoice type',
    'category': 'account',
    'author': 'Flexxoone',
    'version': '1.0',
    'depends': ['jp_automate_multipayment', 'fields_gamma'],
    'description': """
Multiple payments: invoice type (bridge module)
===============================================
* What it does: shows the invoice type (field of the module "Otros Campos",
  fields_gamma) of each paid document in Multiple Payments and in the picker of
  bills, and copies it to the journal entry of the payment. It is a separate
  module so that Multiple Payments keeps working in the databases that do not
  use fields_gamma.
* Configuration: none. It is installed automatically where both modules are.
* Usage: Accounting > Multiple Payments.
    """,
    'data': ['views/multipayment_advance_it_views.xml'],
    'auto_install': True,
    'installable': True,
}
