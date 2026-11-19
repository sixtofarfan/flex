# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class StockMoveLine(models.Model):
	_inherit = "stock.move.line"

	use_create_lots = fields.Boolean(related='picking_id.picking_type_id.use_create_lots')

class StockMove(models.Model):
	_inherit = 'stock.move'

	@api.constrains('move_line_nosuggest_ids')
	def _check_lots(self):
		for record in self:
			log = ""
			black_list = []
			for line in record.move_line_nosuggest_ids:
				if line.lot_name not in black_list:
					if len(record.move_line_nosuggest_ids.filtered(lambda l:l.lot_name == line.lot_name)) > 1:
						log += 'Serie %s \n' % line.lot_name
						black_list.append(line.lot_name)
			if log:
				raise UserError('Se encontraron las siguientes series repetidas:\n' + log)