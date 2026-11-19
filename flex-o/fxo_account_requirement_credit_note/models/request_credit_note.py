# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RequestCreditNote(models.Model):
	_name = 'request.credit.note'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Request Credit Note'

	name = fields.Char(string='Nombre', default='/', required=True, readonly=True)
	partner_id = fields.Many2one('res.partner', string='Cliente', domain=[('is_customer', '=', True)], required=True, 
		states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],'done': [('readonly', True)], 'canceled': [('readonly', True)]})
	date = fields.Date(string='Fecha de Solicitud', default=fields.Date.today(), required=True)
	confirmation_date = fields.Date(string='Fecha de Confirmacion')
	currency_id = fields.Many2one('res.currency', related='move_id.currency_id', string='Moneda', required=True)
	credit_note_type_id = fields.Many2one('einvoice.catalog.09', string='Tipo', required=True, 
		states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],'done': [('readonly', True)], 'canceled': [('readonly', True)]})
	reason = fields.Char(string='Motivo de Nota de Credito', 
		states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],'done': [('readonly', True)], 'canceled': [('readonly', True)]})
	move_id = fields.Many2one('account.move', string='Documento', required=True, 
		states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],'done': [('readonly', True)], 'canceled': [('readonly', True)]})
	note = fields.Char(string='Motivo de Cancelacion', readonly=True)
	internal_type_id = fields.Many2one('einvoice.catalog.09.internal', string='Tipo Descuento', required=True, 
		states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],'done': [('readonly', True)], 'canceled': [('readonly', True)]})
	discount = fields.Float(string='Descuento', default=100,
		states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],'done': [('readonly', True)], 'canceled': [('readonly', True)]})
	discount_type = fields.Selection([
		('percent', 'Porcentaje'),
		('amount', 'Monto'),
	], string='Tipo de Descuento', default='percent',
		states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],'done': [('readonly', True)], 'canceled': [('readonly', True)]})
	credit_note_id = fields.Many2one('account.move', string='Nota de Credito', readonly=True)
	line_ids = fields.One2many('request.credit.note.line', 'request_id', 
		states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],'done': [('readonly', True)], 'canceled': [('readonly', True)]})
	approval_line_ids = fields.One2many('approval.request', 'request_credit_note_id', string='Aprobaciones')
	state = fields.Selection([
			('draft', 'Borrador'),
			('confirmed', 'Confirmado'),
			('approved', 'Aprobado'),
			('done', 'Finalizado'),
			('canceled', 'Cancelado'),
		], string='Estado', default='draft')
	user_id = fields.Many2one('res.users', string='Solicitante', default=lambda self: self.env.user.id)
	team_id = fields.Many2one('crm.team', string='Equipo', default=lambda self: self.env.user.sale_team_id.id)

	@api.onchange('user_id')
	def _get_team_by_user(self):
		for rec in self:
			rec.team_id = rec.user_id.sale_team_id.id

	@api.constrains('discount')
	def _verify_discount(self):
		for record in self:
			if record.discount > 100:
				raise UserError('El descuento no puede ser mayor al 100%')

	@api.constrains('line_ids')
	def _verify_discounts(self):
		for record in self:
			if record.line_ids and all(i.discount == 0 for i in record.line_ids):
				raise UserError('Es necesario colocar un descuento en al menos una de las lineas')

	def set_draft(self):
		self.state = 'draft'
		self.name = '/'

	def set_confirm(self):
		if not self.line_ids:
			raise UserError('Es necesario tener lineas para confirmar una solicitud')
		if not self.user_id or not self.team_id:
			raise UserError('Es necesario especificar un Solicitante')
		self.confirmation_date = fields.Date.today()
		Team = self.team_id
		Category = Team.mapped('approval_credit_note_id').filtered(lambda l: self.env.user in l.mapped('user_ids'))
		if Category:
			self.env['approval.request'].create({
				'request_credit_note_id': self.id,
				'name': self.name,
				'request_owner_id': self.env.user.id,
				'category_id': Category.id,
				'date_confirmed': self.confirmation_date,
				'date_start': self.date,
				'date_end': self.confirmation_date,
				'location': Team.name,
			})
		else:
			raise UserError('Usted no se encuentra en ningun equipo de Ventas con Confirmacion para Notas de Credito')
		self.state = 'confirmed'
		self.name = self.env['ir.sequence'].next_by_code('sol_credit_note') or '/'

	def set_approve(self):
		self.state = 'approved'

	def get_cancel_wizard(self):
		return {
			'name': 'Cancelar Solicitud',
			'type': 'ir.actions.act_window',
			'res_model': 'request.credit.note.wizard',
			'views': [(False, 'form')],
			'context': self._context,
			'target': 'new'
		}

	def get_move_lines(self):
		self.line_ids.unlink()
		for line in self.move_id.invoice_line_ids:
			discount = line.quantity * line.price_unit
			self.env['request.credit.note.line'].create({
				'request_id': self.id,
				'move_line_id': line.id,
				'quantity': line.quantity,
				'price_unit': line.price_unit,
				'price_subtotal': line.quantity * line.price_unit,
				'discount': discount,
			})

	def generate_credit_note(self):
		new_moves = []
		for record in self:
			if record.state != 'approved':
				raise UserError('Solo se puede generar notas de credito en estado Aprobado')
			moves = record.mapped('move_id')
			default_values_list = []
			# for move in moves:
			# 	default_values_list.append({
			# 		'glosa': _('Reversal of: %s, %s') % (move.name, record.reason) if record.reason else _('Reversal of: %s') % (move.name),
			# 		'date': record.date or move.date,
			# 		'invoice_date': move.is_invoice(include_receipts=True) and (record.date or move.date) or False,
			# 		'journal_id': move.journal_id.id,
			# 		'invoice_payment_term_id': None,
			# 		'credit_note_type_id': record.credit_note_type_id.id,
			# 		'internal_type_id': record.internal_type_id.id,
			# 		'auto_post': True if record.date > fields.Date.context_today(record) else False,
			# 		'currency_rate': move.currency_rate,
			# 	})
			# 	old_lines = record.line_ids.filtered(lambda l: l.discount > 0)
			# 	new_move = move._reverse_moves(default_values_list)
			# 	invoice_line_ids = []
			# 	for line in old_lines:
			# 		new_line = new_move.invoice_line_ids.filtered(lambda l:l.product_id == line.product_id)
			# 		new_line.with_context(check_move_validity=False).write({
			# 			'price_unit': line.price_unit,
			# 			'price_subtotal': line.price_subtotal,
			# 		})
			# 		invoice_line_ids.append(new_line.ids)
			# 	del_lines = new_move.invoice_line_ids.filtered(lambda l:l.product_id not in old_lines.mapped('product_id'))
			# 	del_lines.with_context(check_move_validity=False).unlink()
			# 	new_move._compute_amount()
			# 	for line in new_move.line_ids:
			# 		line.with_context(check_move_validity=False)._onchange_credit()
			# 		line.with_context(check_move_validity=False)._onchange_debit()
			# 	new_move.with_context(check_move_validity=False)._move_autocomplete_invoice_lines_values()
			# 	new_move.with_context(check_move_validity=False)._compute_invoice_taxes_by_group()
			# 	new_move.with_context(check_move_validity=False)._recompute_dynamic_lines()
			# 	new_move.with_context(check_move_validity=False)._onchange_invoice_line_ids()
			# 	record.credit_note_id = new_move.id
			# 	invoice_relac = {
			# 		'move_id': new_move.id,
			# 		'type_document_id': move.type_document_id.id,
			# 		'date': move.invoice_date,
			# 		'nro_comprobante': move.ref,
			# 		'amount_currency': 0 if move.currency_id.name == 'PEN' else move.amount_total, 
			# 		'amount': move.amount_total if move.currency_id.name == 'PEN' else 0,
			# 		'bas_amount': move.amount_untaxed,
			# 		'tax_amount': move.amount_tax,
			# 	}
			# 	self.env['doc.invoice.relac'].create(invoice_relac)
			# 	new_move.currency_rate = move.currency_rate
			# 	new_moves.append(new_move.id)
			# # Create action.

			document_code = self.env['einvoice.catalog.01'].search([('code','=','07')],limit=1)

			for move in moves:
				inv = {
					'partner_id' : record.partner_id.id,
					'glosa': _('Reversal of: %s, %s') % (move.name, record.reason) if record.reason else _('Reversal of: %s') % (move.name),
					'date': record.date or move.date,
					#'invoice_date': move.is_invoice(include_receipts=True) and (record.date or move.date) or False,
					'journal_id': 1,
					'invoice_payment_term_id': None,
					'credit_note_type_id': record.credit_note_type_id.id,
					'internal_type_id': record.internal_type_id.id,
					'auto_post': True if record.date > fields.Date.context_today(record) else False,
					'currency_rate': move.currency_rate,
					'currency_id': record.currency_id,
					'type': 'out_refund',
					'type_document_id': document_code.id,
					'invoice_line_ids': []
				}
			invoice_line_ids =[]
			for item in record.line_ids:
				temp = {
                                                'product_id': item.product_id,
						'name' :            item.move_line_id.name,
						'quantity':         item.quantity,
						'price_unit':       item.price_unit,
						'price_subtotal':   item.price_subtotal,
						'account_id':  item.move_line_id.account_id.id,
						'product_uom_id' : item.move_line_id.product_uom_id.id,
						'partner_street_destination' :  item.move_line_id.partner_street_destination.id, 
						'partner_street_destination_header' : item.move_line_id.partner_street_destination_header.id,
						'service_id' : item.move_line_id.service_id,
						'tax_ids': [(6, 0, item.move_line_id.tax_ids.ids)]
					}
					
				invoice_line_ids.append(temp)
			for  item in invoice_line_ids:
					inv['invoice_line_ids'].append((0, 0, item))
			
			new_move = self.env['account.move'].sudo().create(inv)
			record.credit_note_id = new_move.id
			invoice_relac = {
				'move_id': new_move.id,
				'type_document_id': move.type_document_id.id,
				'date': move.invoice_date,
				'nro_comprobante': move.ref,
				'amount_currency': 0 if move.currency_id.name == 'PEN' else move.amount_total, 
				'amount': move.amount_total if move.currency_id.name == 'PEN' else 0,
				'bas_amount': move.amount_untaxed,
				'tax_amount': move.amount_tax,
			}
			self.env['doc.invoice.relac'].create(invoice_relac)
			new_move.currency_rate = move.currency_rate
			new_moves.append(new_move.id)
		# Create action.
			record.state = 'done'
		new_moves = self.env['account.move'].browse(new_move.id)
		action = {
			'name': _('Reverse Moves'),
			'type': 'ir.actions.act_window',
			'res_model': 'account.move',
		}
		if len(new_moves) == 1:
			action.update({
				'view_mode': 'form',
				'res_id': new_moves.id,
			})
		else:
			action.update({
				'view_mode': 'tree,form',
				'domain': [('id', 'in', new_moves.ids)],
			})
		return action

	def unlink(self):
		for record in self:
			if record.state != 'draft':
				raise UserError('Solo se pueden eliminar Solicitudes en estado Borrador')
		return super(RequestCreditNote, self).unlink()

class RequestCreditNoteLine(models.Model):
	_name = 'request.credit.note.line'
	_description = 'Request Credit Note Line'

	request_id = fields.Many2one('request.credit.note', ondelete='cascade')
	move_line_id = fields.Many2one('account.move.line')
	product_id = fields.Many2one('product.product', related='move_line_id.product_id', string='Producto')
	quantity = fields.Float(string='Cantidad')
	price_unit = fields.Float(string='Precio')
	price_subtotal = fields.Float(string='Subtotal')
	discount = fields.Float(string='Descuento')
	account_id = fields.Many2one('account.account', related='move_line_id.account_id', string='Cuenta')
	partner_street_destination = fields.Many2one('res.partner', related='move_line_id.partner_street_destination', string='Direccion Dest')
	partner_street_destination_header = fields.Many2one('res.partner', related='move_line_id.partner_street_destination_header')
	service_id = fields.Char(related='move_line_id.service_id', string='ID Serv')
	product_uom_id = fields.Many2one('uom.uom', related='move_line_id.product_uom_id', string='UM')


	# 'account_id':  item.move_line_id.account_id.id,
	# 					'product_uom_id' : item.move_line_id.product_uom_id.id,
	# 					'partner_street_destination' :  item.move_line_id.partner_street_destination.id, 
	# 					'partner_street_destination_header' : item.move_line_id.partner_street_destination_header.id,
	# 					'service_id' : item.move_line_id.service_id,

	@api.constrains('discount')
	def verify_discount(self):
		for rec in self:
			if rec.discount > rec.price_subtotal:
				raise UserError('El monto de descuento %d no puedo ser mayor al monto subtotal %d' % (rec.discount, rec.price_subtotal))

	@api.onchange('quantity', 'price_unit')
	def _get_subtotal(self):
		for record in self:
			record.price_subtotal = record.quantity * record.price_unit

	@api.onchange('discount', 'price_subtotal')
	def _get_discount(self):
		for record in self:
			if record.request_id.discount:
				record.discount = record.price_subtotal * record.request_id.discount / 100
