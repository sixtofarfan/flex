# -*- coding: utf-8 -*-
from odoo  import models, fields, api
from odoo.exceptions import UserError
from datetime import *

class StockMove(models.Model):
	_inherit = 'stock.move'

	description = fields.Char(string='Descripcion')

	@api.onchange('product_id', 'move_line_ids.lot_name', 'move_line_ids.lot_id', 'move_line_ids.qty_done')
	def get_description_by_product(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		for rec in self:
			desc = ''
			if rec.product_id:
				desc += '[%s] %s' % (rec.product_id.default_code or '', rec.product_id.name) 
			if MainParameter.including_lots and rec.product_id.tracking == 'serial' and rec.move_line_ids:
				desc += '\n SERIES: ' + ','.join([i.lot_name for i in rec.mapped('move_line_ids') if i.lot_name])
			if MainParameter.including_lots and rec.product_id.tracking == 'lot' and rec.move_line_ids:
				desc += '\n' + '\n'.join(['LOTE: {1} CANT: {2} VENC: {0}'.format(
					i.lot_id.life_date and datetime.strftime(i.lot_id.life_date, '%d-%m-%Y') or 'No tiene', 
					i.lot_id.name,
					i.qty_done,
					) for i in rec.mapped('move_line_ids')])
			elif MainParameter.including_lots_make and rec.product_id.tracking == 'lot' and rec.move_line_ids:
				desc += '\n' + '\n'.join(['R.SN: {0} LOTE: {1} CANT: {2} F.FAB {3} VENC {4}'.format(
					i.product_id.healt_register,i.lot_id.name,i.product_uom_qty,
					i.lot_id.manufacturing_date and datetime.strftime(i.lot_id.manufacturing_date, '%d-%m-%Y') or 'No tiene', 
					i.lot_id.life_date and datetime.strftime(i.lot_id.life_date, '%d-%m-%Y') or 'No tiene', 
					) for i in rec.mapped('move_line_ids')])


			rec.description = desc

	@api.onchange('product_id', 'move_line_nosuggest_ids.lot_name', 'move_line_nosuggest_ids.lot_id', 'move_line_nosuggest_ids.qty_done')
	def get_description_by_product_nosuggest(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		for rec in self:
			desc = ''
			if rec.product_id:
				desc += '[%s] %s' % (rec.product_id.default_code or '', rec.product_id.name)
			if MainParameter.including_lots and rec.product_id.tracking == 'serial' and rec.move_line_nosuggest_ids:
				desc += '\n SERIES: ' + ','.join([i.lot_name for i in rec.mapped('move_line_nosuggest_ids') if i.lot_name])
			elif MainParameter.including_lots and rec.product_id.tracking == 'lot' and rec.move_line_nosuggest_ids:
				desc += '\n' + '\n'.join(['LOTE: {1} CANT: {2} VENC: {0}'.format(
					i.lot_id.life_date and datetime.strftime(i.lot_id.life_date, '%d-%m-%Y') or 'No tiene', 
					i.lot_id.name,
					i.qty_done,
					) for i in rec.mapped('move_line_nosuggest_ids')])
			rec.description = desc


class StockPicking(models.Model):
	_inherit = 'stock.picking'

	def button_validate(self):
		res = super(StockPicking, self).button_validate()
		for line in self.move_ids_without_package:
			if line.move_line_nosuggest_ids:
				line.get_description_by_product_nosuggest()
			if line.move_line_ids:
				line.get_description_by_product()
		return res

	def update_qty(self):
		for line in self.move_ids_without_package:
			if line.move_line_nosuggest_ids:
				line.get_description_by_product_nosuggest()
			if line.move_line_ids:
				line.get_description_by_product()
