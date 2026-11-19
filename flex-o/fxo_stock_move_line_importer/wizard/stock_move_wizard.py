# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import sys, subprocess

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	from xlrd import *
except:
	install('xlrd')

class StockMoveWizard(models.TransientModel):
	_name = 'stock.move.wizard'
	_description = 'Stock Move Wizard'

	file = fields.Binary(string='Archivo de Importacion', required=True)

	def import_stock_move_lines(self):
		if not self.file:
			raise UserError('Es necesario adjuntar un archivo para la importacion')
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError('No se ha especificado una ruta de descarga en Parametros Principales de Contabilidad')
		route = MainParameter.dir_create_file + 'ImportLines.xlsx'
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.file))
		tmp.close()
		wb = open_workbook(route)
		sheet = wb.sheet_by_index(0)
		if sheet.ncols != 4:
			raise UserError('El archivo de importacion debe tener 4 columnas con la siguiente forma: \n \t PARA | LOTE/NRO SERIE | REALIZADO | UNIDAD DE MEDIDA')
		StockMove = self.env['stock.move'].browse(self._context.get('active_id'))
		for i in range(1, sheet.nrows):
			Location = self.env['stock.location'].search([('name', '=', sheet.cell_value(i, 0))])
			Lot = self.env['stock.production.lot'].search([('name', '=', sheet.cell_value(i, 1))])
			UOM = self.env['uom.uom'].search([('name', '=', sheet.cell_value(i, 3))])
			if not Location:
				raise UserError('No se ha encontrado el Almacen %s de la linea %d' % (sheet.cell_value(i, 0), i))
			if not Lot:
				Lot = self.env['stock.production.lot'].create({
					'company_id': self.env.company.id,
					'product_id': StockMove.product_id.id,
					'name': sheet.cell_value(i, 1),
				})
			try:
				float(sheet.cell_value(i, 2))
			except:
				raise UserError('El monto de la linea %d debe tener el formato de numero' % i)
			if not UOM:
				raise UserError('No se ha encontrado la Unidad de Medida %s de la linea %d' % (sheet.cell_value(i, 3), i))

			self.env['stock.move.line'].create({
				'move_id': StockMove.id,
				'location_dest_id': Location.id,
				'lot_id': Lot.id,
				'qty_done': float(sheet.cell_value(i, 2)),
				'product_uom_id': UOM.id,
			})

		return self.env['popup.it'].get_message('Se importaron todas las lineas satisfactoriamente')