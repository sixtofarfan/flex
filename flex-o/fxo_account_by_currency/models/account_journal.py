# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountJournal(models.Model):
	_inherit = 'account.journal'

	is_refundable = fields.Boolean(string='Es reembolsable', default=False)

class CurrencyJournalItem(models.Model):
	_inherit = 'currency.journal.item'

	type = fields.Selection([
		('income', 'Cobro'),
		('expense', 'Gasto'),
	], string='Tipo de Ingreso')