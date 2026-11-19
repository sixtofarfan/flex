# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_round


class DetractionBatchWizard(models.TransientModel):
	_name = 'detraction.batch.wizard'
	_description = 'Detraction Batch Wizard'

	detraction_date = fields.Date(string='Fecha de Detraccion', default=fields.Date.today())

	def get_batch_detraction(self):
		#if not self.env.user.has_group('fxo_account_detraction_batch.group_detraction_batch'):
		#	raise UserError('Usted no tiene permisos para acceder a esta funcionalidad')
		log = ''
		active_ids = self.env['account.move'].browse(self._context.get('active_ids'))
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		decimals = MainParameter.round_detractions
		if any(move.amount_residual == 0 for move in active_ids):
			raise UserError(_('Some invoices have been canceled in their entirety, please check the amount owed.'))
		for rec in active_ids:

			rec._constrains_linked_to_detractions()
			ReportBase = self.env['report.base']
			if rec.currency_id == rec.env.company.currency_id:
				amount = ReportBase.custom_round(rec.detra_amount, decimals=decimals) if decimals > 0 else ReportBase.custom_round(rec.detra_amount)
				inv_amount = rec.amount_total
			else:
				amount = rec.detra_amount
				inv_amount = rec.amount_total * rec.currency_rate
			if not MainParameter.limit_line_ids:
				raise UserError('Falta configurar lineas de limites de credito en Parametros Principales en la pestaña Detracciones')
			for line in MainParameter.limit_line_ids:
				if rec.type_good_service in line.catalog_54_ids:
					detraction_limit = line.amount
					break
				else:
					detraction_limit = 0
			p_retention = rec.percent_detraction/100 if rec.percent_detraction else 1
			if rec.referencial_value:
				if rec.currency_id.name == 'PEN':
					detra_amount = float_round(rec.referencial_value * p_retention, 2) if rec.referencial_value > rec.amount_total else rec.detra_amount
				else:
					detra_amount = float_round((rec.referencial_value * p_retention)/rec.currency_rate, 2) if rec.referencial_value > (rec.amount_total * rec.currency_rate) else rec.detra_amount
			else:
				detra_amount = rec.detra_amount
				
			if rec.linked_to_detractions  and not rec.move_detraccion_id and inv_amount >= detraction_limit and rec.journal_id.register_sunat:
				p_retention = rec.percent_detraction/100 if rec.percent_detraction else 1
				wizard = self.env['account.detractions.wizard'].create({
					'fecha': rec.invoice_date,
					'monto': detra_amount #if not rec.referencial_value else float_round(rec.referencial_value * p_retention, 2),
				})
				context = {
					'invoice_id': rec.id,
					'active_id': rec.id,
					'default_fecha': rec.invoice_date,
					'default_monto': amount,
				}
				wizard.with_context(context).generar()
		return self.env['popup.it'].get_message('Se procesaron todos los documentos de manera correcta')

		# for rec in active_ids:
		# 	inv_amount = 0 
		# 	if rec.referencial_value:
		# 		inv_amount = rec.referencial_value
		# 	inv_amount = rec.amount_total if rec.currency_id == self.env.company.currency_id else rec.amount_total * rec.currency_rate
		# 	amount = rec.detra_amount
		# 	p_retention = rec.percent_detraction / 100 if rec.percent_detraction else 1
		# 	wizard = self.env['account.detractions.wizard'].create({
		# 		'fecha': rec.invoice_date,
		# 		'monto': amount if not rec.referencial_value else float_round(rec.referencial_value * p_retention, 2),
		# 	})
		# 	context = {
		# 		'invoice_id': rec.id,
		# 		'active_id': rec.id,
		# 		'default_fecha': rec.invoice_date,
		# 		'default_monto': amount,
		# 	}
		# 	wizard.with_context(context).generar()

		# # 	rec._onchange_detraction_partner_id()
		# 	rec._onchange_linked_to_detractions()
		# 	MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		# 	if rec.linked_to_detractions and not rec.move_detraccion_id and rec.state == 'posted':
		# 		wizard = self.env['account.detractions.wizard'].create({
		# 			'fecha': self.detraction_date,
		# 			'monto': rec.detra_amount, #self.env['report.base'].custom_round(
		# 				# rec.detra_amount, decimals=MainParameter.round_detractions) if MainParameter.round_detractions > 0 \
		# 				# else self.env['report.base'].custom_round(rec.detra_amount),
		# 		})
		# 		context = {
		# 			'active_id': rec.id,
		# 			'default_fecha': rec.invoice_date,
		# 			'default_monto': rec.detra_amount,
		# 			'invoice_id': rec.id
		# 		}
		# 		wizard.with_context(context).generar()
		# 	else:
		# 		log += '%s\n' % rec.name

		# if log:
		# 	return self.env['popup.it'].get_message('No se pudieron procesar los siguientes documentos:\n%s' % log)
		# else:
		# 	return self.env['popup.it'].get_message('Se procesaron todos los documentos de manera correcta')