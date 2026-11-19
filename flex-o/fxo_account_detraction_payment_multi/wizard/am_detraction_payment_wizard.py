# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AMDetractionPaymentWizard(models.TransientModel):
	_name = 'am.detraction.payment.wizard'
	_description = 'Account Move Detraction Payment Wizard'

	def _get_moves_domain(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter.detraction_journal:
			raise UserError('No se ha configurado un Diario para detracciones en Parametros Generales de Contabilidad')
		elif not MainParameter.detractions_account:
			raise UserError('No se ha configurado una Cuenta de Detracciones Proveedor en Parametros Generales de Contabilidad')
		else:
			domain = [('account_id', '=', MainParameter.detractions_account.id), ('journal_id', '=', MainParameter.detraction_journal.id)]
			return domain

	move_line_ids = fields.Many2many('account.move.line', 'am_detraction_wizard_move_line_rel', string='Apuntes', domain=_get_moves_domain)

	def add_lines(self):
		Payment = self.env['am.detraction.payment'].browse(self._context.get('active_id'))
		Payment.payment_line_ids.unlink()
		for line in self.move_line_ids:
			DocType = line.partner_id.l10n_latam_identification_type_id
			aux_month = '0' * 2
			if any(i == '-' for i in line.move_id.ref):
				serie = line.move_id.ref.split('-')[0]
				number = line.move_id.ref.split('-')[1]
			else:
				serie = ''
				number = line.move_id.ref
			self.env['am.detraction.payment.line'].create({
				'am_detraction_id': Payment.id,
				'move_line_id': line.id,
				'doc_type': DocType.code_sunat if DocType.code_sunat else '',
				'doc_number': line.partner_id.vat if line.partner_id.vat else '',
				'name': line.partner_id.name if line.partner_id.name else '',
				'code_operation': line.move_id.code_operation if line.move_id.code_operation else '',
				'amount': line.credit if line.credit > 0 else line.debit,
				'operation_type': line.move_id.type_op_det if line.move_id.type_op_det else '',
				'period': str(line.date.year) + aux_month[len(str(line.date.month)):] + str(line.date.month),
				'move_type': line.move_id.type_document_id.code if line.move_id.type_document_id.code else '',
				'move_serie': serie,
				'move_number': number, 
			})