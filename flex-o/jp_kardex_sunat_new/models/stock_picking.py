# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ 
from odoo.exceptions import UserError
import pytz
import datetime

class StockPicking(models.Model):
	_inherit = "stock.picking"

	@api.onchange('numberg')
	def _onchange_numberg(self):
		if self.numberg:
			serie_number = self.numberg.split('-')
			if len(serie_number)<2:
				raise UserError(_('Guide format is incorrect. Please enter serie and number separated by a dash.'))

	@api.constrains('kardex_date')
	def _onchange_kardex_date_line(self):
		sm = self.env['stock.move'].search([('picking_id','=', self._origin.id),('picking_id','!=',False)])
		for line in sm.move_line_ids:
			line.kardex_date = self.kardex_date

	def _check_items(self):
		if self.invoice_id:
			products = self.invoice_id.invoice_line_ids.mapped('product_id')
			for item in self.move_ids_without_package:
				if item.product_id not in products:
					raise UserError(_('Some products on the picking are not present in the invoice.'))

	@api.onchange('invoice_id','kardex_date')
	def _onchange_invoice_id(self):
		for picking in self:
			picking._check_items()	
			if picking.invoice_id:
				if not picking.invoice_id.id:
					invoice_id = picking.invoice_id.id.origin
				else:
					invoice_id = picking.invoice_id.id
			else:
				return
			# Convertimos la fecha en el horario del usuario
			user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
			if not user_tz:
				raise UserError(_('Please select your timezone in your profile.'))
			kardex_date = pytz.utc.localize(picking.kardex_date).astimezone(user_tz)
			scheduled_date = pytz.utc.localize(picking.scheduled_date).astimezone(user_tz)

			sm = self.env['stock.move'].search([('picking_id','=', picking._origin.id),('picking_id','!=',False)])
			if picking.invoice_id:
				am = self.env['account.move'].search([('id','=', invoice_id)])
				for move in sm:
					aml = self.env['account.move.line'].search([('move_id','=', am.id),('product_id','=', move.product_id.id),('price_unit','>',0)])
					svl = self.env['stock.valuation.layer'].search([('stock_move_id','=',move.id),('stock_landed_cost_id','=', False),('quantity','>',0)]).sorted(lambda l: l.create_date, reverse=True)
					if svl:
						svl = svl[0]
					# print(svl.ids)
					if am.currency_id != self.env.user.company_id.currency_id:
						if am.tc_per:
							svl.unit_cost = aml.price_unit * (am.currency_rate if not am.transit_move_line_id else am.transit_move_line_id.tc)
						else:
							rate = am.currency_rate if not am.transit_move_line_id else am.transit_move_line_id.tc #am.currency_id._get_conversion_rate(am.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, am.invoice_date)
							svl.unit_cost = aml.price_unit * rate
					else:
						svl.unit_cost = aml.price_unit
					move.price_unit = svl.unit_cost
					svl.value = svl.quantity * svl.unit_cost
			else:
				for move in sm:
					svl = self.env['stock.valuation.layer'].search([('stock_move_id','=',move.id),('stock_landed_cost_id','=', False),('quantity','>',0)]).sorted(lambda l: l.create_date, reverse=True)
					if svl:
						svl = svl[0]
					if move.purchase_line_id:
						if move.purchase_line_id.currency_id != self.env.user.company_id.currency_id:
							if move.picking_id.use_kardex_date:
								rate = move.purchase_line_id.currency_id._get_conversion_rate(move.purchase_line_id.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, kardex_date)
							else:
								rate = move.purchase_line_id.currency_id._get_conversion_rate(move.purchase_line_id.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, scheduled_date)
							svl.unit_cost = move.purchase_line_id.price_unit * rate #(move.purchase_line_id.price_subtotal / move.purchase_line_id.product_qty) * rate
						else:
							svl.unit_cost = move.purchase_line_id.price_unit #(move.purchase_line_id.price_subtotal / move.purchase_line_id.product_qty)
					else:
						if move.origin_returned_move_id:
							svl_origin = self.env['stock.valuation.layer'].search([('stock_move_id','=',move.origin_returned_move_id.id),('quantity','>',0),('stock_landed_cost_id','=', False)])
							svl.unit_cost = svl_origin.unit_cost
					move.price_unit = svl.unit_cost
					svl.value = svl.quantity * svl.unit_cost
	
	# Para evitar que ITgrupo ponga la fecha actual en la fecha kardex
	def action_done(self):
		kardex_date = self.kardex_date
		self._onchange_kardex_date()
		t = super(StockPicking,self).action_done()
		permiso = self.env['res.groups'].search([('name','=','Permitir Editar Fecha Kardex')])
		if len(permiso)>0:
			if self.env.uid in permiso[0].users.ids:
				self.with_context({'permitido':1}).write({'kardex_date': kardex_date})
				# self.write({'date_done': kardex_date})
			else:
				self.with_context({'permitido':1}).write({'kardex_date': fields.Datetime.now()})
		return t

	# TODO esta funcion la comente por el error***************************
	# def write(self, vals):
	# 	res = super(StockPicking, self).write(vals)
		# self._onchange_invoice_id()
		# return res
	# TODO **************************************************************

	# @api.onchange('kardex_date')
	# def _onchange_kardex_date(self):
	# 	self.write({'date_done': self.kardex_date})
	# 	moves = self.env['stock.move'].search([('picking_id', '=', self.ids)])
	# 	for move in moves:
	# 		move.date = self.kardex_date
	# 		for line in move.move_line_ids_without_package:
	# 			line.date = self.kardex_date