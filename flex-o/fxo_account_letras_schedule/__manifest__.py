# -*- coding: utf-8 -*-
{
    'name': 'Fxo Bills of Exchange: schedule and invoice type',
    'category': 'account',
    'author': 'Flexxoone',
    'version': '1.0',
    # jp_kardex_sunat: only so that this module's invoice picker search runs before its override
    'depends': ['account_letras_it', 'fields_gamma', 'jp_kardex_sunat'],
    'description': """
Bills of exchange (Canje de Letras): schedule generation and invoice type
==========================================================================
* What it does: adds the invoice types C - Monthly consumption, P - Project and
  N - None (new default). In the exchange of invoices for bills it loads the
  pending invoices of the partner, fills document type, amount and invoice type
  from the selected invoice, and generates the schedule of bills from three
  parameters (number of bills, days to the first due date, days between bills).
  Each bill gets the invoice type of the first invoice. The accounting entry
  ("Comprobar" / "Procesar") is not changed.
* Configuration: none (it uses the bill accounts of the Main Parameters).
* Usage: Accounting > Vendors (or Customers) > Canje de Letras: choose the
  partner, "Load pending invoices" or pick them, set the parameters in the
  "Schedule of Bills" tab and press "Generate Schedule".
    """,
    'data': ['views/account_letras_payment_views.xml'],
    'auto_install': False,
    'installable': True,
}
