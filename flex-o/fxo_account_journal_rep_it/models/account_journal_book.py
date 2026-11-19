# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountJournalBook(models.Model):
	_inherit = 'account.journal.book'

	description = fields.Char(string='Descripcion')
	circular = fields.Char(string='Circular')