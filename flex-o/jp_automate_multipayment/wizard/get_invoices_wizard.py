# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
from datetime import *

class GetInvoices(models.TransientModel):
	_name = "get.invoices.wizard"
	_description = "Get Invoices Wizard"
	
	invoices = fields.Many2many('account.move', string='Invoices')
	provisions = fields.Many2many('account.move.line', string='Provisions', domain=lambda self: self._get_provision_domain())
	advances = fields.Many2many('account.payment', string='Advances', domain=lambda self: self._get_advance_domain())
	txt_file = fields.Binary(string='Archivo TXT SUNAT')

	@api.model
	def _get_provision_domain(self):
		domain = [('full_reconcile_id', '=', False)]
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if MainParameter.detractions_account:
			domain.append(('account_id', '=', MainParameter.detractions_account.id))
		return domain

	@api.model
	def _get_advance_domain(self):
		Multipayment = self.env['multipayment.advance.it'].browse(self._context.get('active_id'))
		domain = [('journal_id', '=', Multipayment.journal_id.id)] if Multipayment else []
		return domain

	def get_invoices_wizard(self):
		active_id = self.env.context.get('active_id')
		if not active_id:
			return ''

		return {
			'name': _('Get Invoices'),
			'res_model': 'get.invoices.wizard',
			'view_mode': 'form',
			'view_id': self.env.ref('jp_automate_multipayment.view_get_invoices_wizard').id,
			'context': "{'default_type': 'out_invoice'}",
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def get_invoices_detraction_wizard(self):
		active_id = self.env.context.get('active_id')
		if not active_id:
			return ''

		return {
			'name': _('Get Invoices'),
			'res_model': 'get.invoices.wizard',
			'view_mode': 'form',
			'view_id': self.env.ref('jp_automate_multipayment.view_get_invoices_detraction_wizard').id,
			'context': "{'default_type': 'out_invoice'}",
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def get_detractions_wizard(self):
		active_id = self.env.context.get('active_id')
		if not active_id:
			return ''

		return {
			'name': _('Get Invoices'),
			'res_model': 'get.invoices.wizard',
			'view_mode': 'form',
			'view_id': self.env.ref('jp_automate_multipayment.view_get_detraction_wizard').id,
			'context': "{'default_type': 'out_invoice'}",
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
		
	def insert(self):
		vals=[]
		active_id = self.env.context.get('active_id')
		pma = self.env['multipayment.advance.it'].search([('id','=', active_id)])
		# pma_line = pma.invoice
		for invoice in self.invoices:
			val = {
					'main_id': active_id,
					'partner_id': invoice.partner_id.id,
					'tipo_documento': invoice.type_document_id.id,
					'invoice_id': invoice.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable'))[0].id,
					'account_id': invoice.journal_id.default_debit_account_id.id,
					'tc': invoice.currency_rate,
					'saldo': invoice.amount_residual,
				}
			'''if pma.is_detraction_payment:
				detraction = invoice.amount_total * ( invoice.partner_id.p_detraction / 100 )
				val['type_operation'] = invoice.type_operation.id
				val['type_good_service'] = invoice.type_good_service.id
				val['importe_divisa'] = detraction
				val['debe'] = detraction * invoice.currency_rate if invoice.currency_id != self.env.company.currency_id else detraction
				vals.append(val)'''
			if pma.invoice_type == 'out_invoice':
				val['importe_divisa'] = invoice.amount_residual * -1
				val['haber'] = invoice.amount_residual * invoice.currency_rate if invoice.currency_id != self.env.company.currency_id else invoice.amount_residual
			else:
				val['importe_divisa'] = invoice.amount_residual 
				val['debe'] = invoice.amount_residual * invoice.currency_rate if invoice.currency_id != self.env.company.currency_id else invoice.amount_residual
			if pma.is_retention_payment:
				MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
				if not MainParameter or not MainParameter.p_retention:
					raise UserError(u'No se ha configurado datos para retenciones en Parametros Principales en la pestaña Retenciones para su Compañía')
				#if invoice.amount_total >= MainParameter.min_amount:
				retention = invoice.amount_total * MainParameter.p_retention/100
				val['importe_divisa'] = retention * (-1 if pma.invoice_type == 'out_invoice' else 1)
				val['debe' if pma.invoice_type == 'out_invoice' else 'haber'] = (retention * invoice.currency_rate if invoice.currency_id != self.env.company.currency_id else retention)
				# vals.append(val)
				#else:
				#	raise UserError('El monto de la factura no supera el monto minimo de %d configurado en Parametros Principales en la Pestaña Detracciones' % MainParameter.min_amount)
			# else:
			# 	val['type_operation'] = invoice.type_operation.id
			# 	val['type_good_service'] = invoice.type_good_service.id
			# 	val['importe_divisa'] = invoice.amount_residual * -1
			# 	val['haber'] = invoice.amount_residual * invoice.currency_rate if invoice.currency_id != self.env.company.currency_id else invoice.amount_residual
			vals.append(val)

			if pma.is_detraction_payment:
				val['importe_divisa'] = invoice.detra_amount
				val['debe'] = invoice.detra_amount * invoice.currency_rate if invoice.currency_id and invoice.currency_id.name == 'USD' else invoice.detra_amount
				val['haber'] = 0
		self.env['multipayment.advance.it.line'].create(vals)
		for line in pma.invoice_ids:
			line._update_debit_credit()
			line._get_partner_bank_account()
		pma._get_line_ids()

	def insert_detractions(self):
		pma = self.env['multipayment.advance.it'].browse(self._context.get('active_id'))
		# pma_line = pma.invoice
		if pma.is_detraction_payment:
			for pro in self.provisions:
				origin_invoice = self.env['account.move'].search([('ref','=', pro.nro_comp),('type','=','out_invoice' if pro.balance > 0 else 'in_invoice'),('partner_id','=',pro.partner_id.id)])
				self.env['multipayment.advance.it.line'].create({
					'main_id': self._context.get('active_id'),
					'partner_id': pro.partner_id.id,
					'tipo_documento': self.env['einvoice.catalog.01'].search([('code', '=', '00')], limit=1).id,
					'invoice_id': pro.id,
					'operation_type': origin_invoice.type_op_det,
					'good_services': origin_invoice.code_operation,
					'account_id': pro.account_id.id,
					'tc': pro.move_id.currency_rate,
					'currency_id': pro.currency_id.id if pro.currency_id else None,
					'saldo': pro.amount_residual,
					'importe_divisa': abs(pro.amount_residual),
					'debe': abs(pro.amount_residual) * pro.move_id.currency_rate if pro.currency_id and pro.currency_id.name == 'USD' else abs(pro.amount_residual),
				})
		for line in pma.invoice_ids:
			line._get_partner_bank_account(is_detraction=True)
		pma._get_line_ids()


	def insert_provisions(self):
		Advance = self.env['multipayment.advance.it'].browse(self._context.get('active_id'))
		Advance.provision_ids = [(6, 0, self.provisions.ids)]

	def insert_advances(self):
		Advance = self.env['multipayment.advance.it'].browse(self._context.get('active_id'))
		Advance.advance_ids = [(6, 0, self.advances.ids)]
		for adv in Advance.advance_ids:
			adv._get_partner_bank_account()

	def import_txt_sunat(self):
		return self.importing_file(self.txt_file, self.env['account.move'].browse(self._context.get('active_ids')))

	def importing_file(self, file, moves):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales para su Compañía')
		route = MainParameter.dir_create_file + 'TXT_SUNAT.txt'
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(file))
		tmp.close()
		op_number, date, ref, res_list = '', '', '', []
		with open(route, encoding='cp1252') as f:
			for line in f:
				if "Fecha y hora de pago" in line:
					date = line.split()[5]
				if "Numero de constancia" in line:
					op_number = line.split()[3]
				if "Número de Comprobante" in line:
					ref = line.split()[3] + '-' + line.split()[4]
					res_list.append((ref, op_number))
		for k, v in res_list:
			move = moves.filtered(lambda m: m.ref == k)
			move.voucher_number = v
			move.date_detraccion = datetime.strptime(date, '%d/%m/%Y').date()
			
		return self.env['popup.it'].get_message('Se Importo el archivo correctamente')
