# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBalancePeriodBookGamma(models.Model):
	_name = 'account.balance.period.book.gamma'
	_auto = False
	
	partner = fields.Char(string='Partner')
	fecha_doc = fields.Date(string='Fecha Emision')
	fecha_ven = fields.Date(string='Fecha Vencimiento')
	order_name = fields.Char(string='Numero de Operacion')
	td_sunat = fields.Char(string='Tipo de Documento')
	nro_comprobante = fields.Char(string='Nro. de Doc.')
	saldo_mn = fields.Float(string='Saldo S/')
	saldo_me = fields.Float(string='Saldo USD')
	moneda = fields.Char(string='Moneda')
	plazo = fields.Char(string='Plazo de Pago')
	ref_hija = fields.Char(string='Referencia Hija')
	
	foreign_agent_name = fields.Char(string='Agente del Exterior')
	consignne_name = fields.Char(string='Consignatario')
	client_order_ref  = fields.Char(string=' Referencia del Cliente')
	corporate_reference = fields.Char(string='Ref. Corporativa')
	shipping_documents = fields.Char(string='Booking/BL')
	

	order_ref = fields.Char(string='Referencia del Cliente')
	hbl = fields.Char(string='HBL')
	estado = fields.Char(string='Estado')
	homeless = fields.Boolean(string='No Domiciliado')
	aml_ids = fields.Text(string='Detalle')
	importe_total = fields.Float(string='Total USD')
	importe_total_pen = fields.Float(string='Total S/')
	partner_cobrar = fields.Char(string='Partner a Cobrar')

	def edit_linea_it(self):
		arr = str(self.aml_ids)
		arr2 = arr.replace(']','').replace('[','')
		t = arr2.split(',')

		elem = []
		for i in t:
			if i!= 0:
				elem.append(i)

		return {
			'name': 'Detalle',
			'domain' : [('id', 'in', elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.line',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': '_blank',
		}