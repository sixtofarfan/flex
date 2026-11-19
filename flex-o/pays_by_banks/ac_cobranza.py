# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import csv 
import json
import threading
from openerp.modules.registry import Registry 
from odoo import tools
import base64
import codecs
from datetime import datetime




class recaudacion_diaria_directa_recaudacion(models.Model):
	_name = 'recaudacion.diaria.directa.recaudacion'
	_description = 'Recaudacion Diaria Directa Recaudacion'

	recaudacion_id = fields.Many2one('recaudacion.diaria.directa','Recaudacion')

	factura_id = fields.Many2one('account.move','Factura Pago',compute="get_factura_id")

	def get_factura_id(self):
		for i in self:
			factura = self.env['account.move'].search([('ref','=',i.factura_name),('type','=','out_invoice')])
			if len(factura)>0:
				i.factura_id = factura[0].id
			else:
				i.factura_id = False

	pago_id = fields.Many2one('account.payment','Pago')

	partner = fields.Many2one('res.partner','Cliente',related='factura_id.partner_id')
	factura_name = fields.Char('Factura')
	fecha = fields.Date('Fecha',related='recaudacion_id.date')
	moneda = fields.Many2one('res.currency','Moneda')
	monto = fields.Float('Monto',digits=(12,2))
	state = fields.Selection([('1','Sin Factura'),('2','Pendiente Pago'),('3','Pagado')],'Estado',compute="get_state")

	def get_state(self):
		for i in self:
			if not i.factura_id:
				i.state = '1'
			elif not i.pago_id:
				i.state = '2'
			else:
				i.state = '3'


class recaudacion_diaria_directa(models.Model):
	_name = 'recaudacion.diaria.directa'
	_description = 'Recaudacion Diaria Directa'

	name = fields.Char('Nro de Lote',default='Nueva')
	date = fields.Date('Fecha')
	banco = fields.Many2one('banco.recaudacion.directa','Banco')
	nombre_archivo = fields.Char('Nombre Archivo')
	archivo = fields.Binary('Archivo Banco')

	recaudacion_ids = fields.One2many('recaudacion.diaria.directa.recaudacion','recaudacion_id','Recaudaciones')
	state = fields.Selection([('draft','Borrador'),('process','Proceso'),('done','Finalizado')],'Estado',default='draft')
	cabecera = fields.Char('Cabecera Secret')

	cash_flow_id = fields.Many2one('account.cash.flow','Flujo de Caja')
	catalog_payment_id = fields.Many2one('einvoice.catalog.payment','Medio de Pago')
	type_doc_cash_id = fields.Many2one('einvoice.catalog.01','Tido Documento de Caja')
	cash_nro_comp = fields.Char('Nro Op. Caja')
	payment_method_id = fields.Many2one('account.payment.method',' Metodo de Pago',required=True)


	def recaudar(selfs):
		for self in selfs:
			if self.name == 'Nueva':
				self.name = 'LOT-' + str(self.id)
			for i in self.recaudacion_ids:
				i.unlink()			

			import time		
			import base64
			import codecs

			detalle = []
			parametros = self.env['main.parameter'].search([])[0]

			cabe_v1 = str(base64.b64decode(self.archivo))
			tmp_control = cabe_v1.split('\\n')[0]
			if len( self.env['recaudacion.diaria.directa'].search([('cabecera','=',tmp_control),('id','!=',self.id)]) )>0:
				raise ValidationError(u'Ya se importo anteriormente.')

			self.cabecera = tmp_control


			if self.banco.banco == 'scotia':
				for i in cabe_v1.split('\\n'):
					if len(i) >0 and i[0] == 'D':
						datos = []					
						datos.append( i[33:45].replace(' ','-') )   #factura
						datos.append( float(i[68:79]) + float('0.' + i[79:81]) )    #cuota
						detalle.append(datos)


			elif self.banco.banco == 'bbva':
				for i in cabe_v1.split('\\n'):
					if len(i)>0 and i[:2] == '02':
						datos = []
						datos.append( i[53:80].split(' ')[2].strip() )   #cod estudiando
						datos.append( float(i[80:93]) + float('0.' + i[93:98]) )    #cuota
						detalle.append(datos)

			elif self.banco.banco == 'bcp':
				for i in cabe_v1.split('\\n'):
					if len(i)>0 and i[0] == 'D':
						datos = []
						datos.append( i[27:39].replace('N','-') )   #cod estudiando
						datos.append( float( i[105:116] + '.'+ i[116:118] ) )    #cuota
						detalle.append(datos)

			for i in detalle:
				data = {
				 'factura_name':i[0],
				 'monto':i[1],
				 'moneda':self.env['res.currency'].search([('name','=','PEN')])[0].id,
				 'recaudacion_id':self.id,
				}

				self.env['recaudacion.diaria.directa.recaudacion'].create(data)
			self.state = 'process'


	def borrador(selfs):
		for self in selfs:
			flag = True
			for i in self.recaudacion_ids:
				if i.state == '3':
					flag = False

			if flag:
				self.state = 'draft'

	
	def pagado(selfs):
		for self in selfs:
			for i in self.recaudacion_ids:
				if not i.pago_id.id and i.factura_id.id:
					pago = False
					if True:
						data = {
							'journal_id':self.banco.diario.id,
							'amount':i.monto,
							'currency_id': self.env['res.currency'].search([('name','=','PEN')])[0].id,
							'payment_date':self.date,
							'cash_nro_comp':self.name,
							'communication':i.factura_id.ref,
							'cash_flow_id':self.cash_flow_id.id,
							'catalog_payment_id':self.catalog_payment_id.id,
							'type_doc_cash_id':self.type_doc_cash_id.id,
							'cash_nro_comp':self.cash_nro_comp,
							'payment_method_id':self.payment_method_id.id,
							'payment_type':'inbound',
							'partner_type':'supplier',
							'nro_comp':i.factura_id.ref,
							'type_document_id':i.factura_id.type_document_id.id,
						}
						pago = self.env['account.payment'].with_context({'default_invoice_ids': [(4, i.factura_id.id, None)]}).create(data)

						pago.post()
						i.pago_id = pago.id

			flag = True
			for i in self.recaudacion_ids:
				if i.state != '3':
					flag = False

			if flag:
				self.state = 'done'		
	
	def unlink(self):
		for i in self:
			if i.state != 'draft':
				raise ValidationError(u'No se puede eliminar una recaudacion en proceso o finalizada.')
		t = super(recaudacion_diaria_directa,self).unlink()
		return t



class banco_recaudacion_directa(models.Model):
	_name = 'banco.recaudacion.directa'
	_description = 'Banco Recaudacion Directa'

	banco = fields.Selection([('scotia','Scotia Bank'),('bbva','BBVA'),('bcp','BCP')],'Banco',help="Por ahora habilitado: scotia, bbva e bcp.")
	diario = fields.Many2one('account.journal','Diario de Banco CPE')

	_rec_name = 'diario'