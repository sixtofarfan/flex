# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	def validate_moves(self):
		bank_line_ids = self.line_ids.filtered(lambda l: l.journal_entry_ids)
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		log = ''
		for line in bank_line_ids:
			ConcilationLine = MainParameter.concilation_line_ids.filtered(lambda l: any(c.name in line.name for c in l.concept_ids))
			Lines = self.env['account.move.line'].search([('statement_line_id', '=', line.id)])
			if ConcilationLine and ConcilationLine.partner_bank:
				for ml in Lines:
					if ml.partner_id != self.journal_id.bank_partner_id:
						ml.partner_id = self.journal_id.bank_partner_id
						log += 'Asiento %s\n' % ml.move_id.name
			elif line.type:
				for ml in Lines:
					if ml.partner_id != line.partner_id:
						ml.partner_id = line.partner_id
						log += 'Asiento %s\n' % ml.move_id.name
						if ml.payment_id and ml.payment_id.partner_id != line.partner_id:
							ml.payment_id.partner_id = line.partner_id
							log += 'Pago %s\n' % ml.payment_id.name
		if log:
			return self.env['popup.it'].get_message('Se cambio el partner de los siguientes Documentos:\n' + log)
		else:
			return self.env['popup.it'].get_message('No se cambio el partner de ningun documento')