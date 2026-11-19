# -*- coding: utf-8 -*-
{
    'name': 'Fxo Bank Statement Mass Unreconcile',
    'category': 'account',
    'author': 'Flexxoone',
    'version': '1.0',
    'depends': ['account'],
    'description': """
Bank statements: mass unreconcile and delete
============================================
* What it does: adds to the bank statement form a button to revert the
  reconciliation of every line at once, a button per line to revert and delete
  that line, and a button to delete the whole statement (reverting first).
* Configuration: none.
* Usage: Accounting > Bank statements > open a statement in "New" state.
  Validated statements must be reset to "New" first.
    """,
    'data': ['views/account_bank_statement.xml'],
    'auto_install': False,
    'installable': True,
}
