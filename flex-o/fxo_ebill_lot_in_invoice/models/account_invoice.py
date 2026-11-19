# -*- coding: utf-8 -*-
from odoo  import models, fields, api
from odoo.exceptions import UserError
import json

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	ref_code = fields.Char(string='Codigo Referencia')

	@api.onchange('product_id')
	def get_ref_code(self):
		for rec in self:
			if rec.product_id:
				rec.ref_code = rec.product_id.ref_code

	def get_edit_wizard(self):
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'move.line.description.wizard',
			'views': [(False, 'form')],
			'context': {'default_name': self.name},
			'target': 'new',
		}

class SaleAdvancePaymentInv(models.TransientModel):
	_inherit = 'sale.advance.payment.inv'

	def create_invoices(self):
		t = super(SaleAdvancePaymentInv,self).create_invoices()
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		aux = ''
		lista = []
		lista2 = []
		if not MainParameter.including_lots_in_invoice:
			if len(self.picking_ids) > 0 and MainParameter.including_lots:  # Lotes y fechas de vencimiento
				for albaran in self.picking_ids:
					spos = albaran.move_ids_without_package
					for spo in spos:
						aux_dict = {}
						aux_dict['product_id'] = spo.product_id.id
						aux_dict['quantity'] = spo.quantity_done
						#aux += '\nMARCA: %s PROCED: %s\n' % (spo.product_id.brand_id.name or '', ','.join(spo.product_id.tag_ids.mapped('name')))
						if albaran.picking_type_id.show_operations:
							MoveLines = albaran.move_line_nosuggest_ids
						else:
							MoveLines = spo.move_line_ids
						for lote in MoveLines:
							if spo.product_id == lote.lot_id.product_id and spo.quantity_done == lote.qty_done:
								venc = 'VENC : ' + lote.lot_id.life_date.strftime("%d/%m/%Y") if lote.lot_id.life_date else ''
								aux += '\nLOTE : %s %s %s' % (lote.lot_id.name, lote.qty_done, venc)
						aux_dict['aux'] = aux
						aux = ''
						lista.append(aux_dict)
						lista2.append(json.dumps(aux_dict))
				#raise UserError(lista2)
				for line in self.picking_ids[0].invoice_id.invoice_line_ids:
					producto = next(iter(filter(lambda l:l['product_id'] == line.product_id.id and l['quantity'] == line.quantity,lista)),None)
					if producto:
						line.name += '%s'%(producto['aux'])
			else:
				if len(self.picking_ids) > 0 and MainParameter.including_lots_make:  # Lotes, Fecha de fabricacion 
					for albaran in self.picking_ids:
						spos = albaran.move_ids_without_package
						for spo in spos:
							aux_dict = {}
							aux_dict['product_id'] = spo.product_id.id
							aux_dict['quantity'] = spo.quantity_done
							if albaran.picking_type_id.show_operations:
								MoveLines = albaran.move_line_nosuggest_ids
							else:
								MoveLines = spo.move_line_ids
							for lote in MoveLines:
								if spo.product_id == lote.lot_id.product_id and spo.quantity_done == lote.qty_done:
									rsn = lote.product_id.healt_register
									xlote = 'LOTE :' + lote.lot_id.name
									make = 'F.FAB: ' + lote.lot_id.manufacturing_date.strftime("%d/%m/%Y") if lote.lot_id.manufacturing_date else ''
									venc = 'VENC : ' + lote.lot_id.life_date.strftime("%d/%m/%Y") if lote.lot_id.life_date else ''
									aux += '\nR.SN : %s %s %s %s %s' % (rsn, xlote, lote.qty_done, make, venc)
							aux_dict['aux'] = aux
							aux = ''
							lista.append(aux_dict)
							lista2.append(json.dumps(aux_dict))
					#raise UserError(lista2)
					for line in self.picking_ids[0].invoice_id.invoice_line_ids:
						producto = next(iter(filter(lambda l:l['product_id'] == line.product_id.id and l['quantity'] == line.quantity ,lista)),None)
						if producto:
							line.name += '%s'%(producto['aux'])


		else:
			black_list = []
			for line in self.picking_ids[0].invoice_id.invoice_line_ids:
				aux = ''
				for pick in self.picking_ids:
					for move in pick.move_ids_without_package:
						if pick.picking_type_id.show_operations:
							MoveLines = pick.move_line_nosuggest_ids
						else:
							MoveLines = move.move_line_ids
						count = 0
						if not aux:
							for lote in MoveLines:
								if count >= line.quantity:
									continue
								else:
									if move.product_id == lote.lot_id.product_id and lote.id not in black_list:
										venc = 'VENC : ' + lote.lot_id.life_date.strftime("%d/%m/%Y") if lote.lot_id.life_date else ''
										aux += '\nLOTE : %s %s %s' % (lote.lot_id.name, lote.qty_done, venc)
										black_list.append(lote.id)
										count += lote.qty_done
							if aux:
								line.name += aux
		return t
