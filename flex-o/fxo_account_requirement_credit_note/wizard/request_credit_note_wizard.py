# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RequestCreditNoteWizard(models.TransientModel):
	_name = 'request.credit.note.wizard'
	_description = 'Request Credit Note Wizard'

	name = fields.Char()
	note = fields.Char(string='Motivo de Cancelacion', required=True)

	def set_cancel(self):
		CreditNote = self.env['request.credit.note'].browse(self._context.get('active_id'))
		CreditNote.note = self.note
		CreditNote.state = 'canceled'