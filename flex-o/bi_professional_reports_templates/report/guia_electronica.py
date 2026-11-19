# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ReportPickingGuia(models.AbstractModel):
	_name = 'report.bi_professional_reports_templates.report_picking_guia'

	@api.model
	def _get_report_values(self, docids, data=None):
		docs = self.env['stock.picking'].browse(docids)
		return {
			'doc_ids': docs.ids,
			'doc_model': 'stock.picking',
			'docs': docs,
		}




class stock_picking(models.Model):
	_inherit = 'stock.picking'

	nombre_mes = fields.Char(
		string=u'Mes',
		compute='_nombre_mes'    )
	dia= fields.Char(
		string=u'Mes',
		compute='_nombre_dia'    )
	years= fields.Char(
		string=u'Mes',
		compute='_nombre_year'    )

	type_print = fields.Boolean(string='Usar Lineas para la guia')

  

	def _nombre_dia(self):
		for item in self:
			dia= slice(8,11)
			item.dia = item.fecha_kardex[dia]

	def _nombre_year(self):
		for item in self:
			dia = slice(2,4)
			item.years = item.fecha_kardex[dia]

	def _nombre_mes(self):
		for item in self:
			mes = slice(5,7)
			fecha = item.fecha_kardex
			dato = fecha[mes]
			if dato == '01':
				item.nombre_mes = 'Enero'
			elif  dato == '02':
				item.nombre_mes = 'Febrero'
			elif  dato == '03':
				item.nombre_mes = 'Marzo'
			elif  dato == '04':
				item.nombre_mes = 'Abril'
			elif  dato == '05':
				item.nombre_mes = 'Mayo'
			elif  dato == '06':
				item.nombre_mes = 'Junio'
			elif  dato == '07':
				item.nombre_mes = 'Julio'
			elif  dato == '08':
				item.nombre_mes = 'Agosto'
			elif  dato == '09':
				item.nombre_mes = 'Setiembre'
			elif  dato == '10':
				item.nombre_mes = 'Octubre'
			elif  dato == '11':
				item.nombre_mes = 'Noviembre'
			elif  dato == '12':
				item.nombre_mes = 'Diciembre'

class Stock_Move(models.Model):
	_inherit = "stock.move"

	report_series = fields.Text('Series',compute='get_series')

	def get_series(self):
		for i in self:
			txt = ""
			for m in i.move_line_ids:
				if m.lot_id.name:
					txt+= m.lot_id.name+ ', '
			i.report_series = txt