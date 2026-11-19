# -*- coding: utf-8 -*-
from odoo  import models, fields, api
from odoo.exceptions import UserError
from decimal import *
import json, urllib3, re, base64
from datetime import *
import requests
from base64 import encodestring

class AccountMove(models.Model):
	_inherit = 'account.move'

	def generate_lines(self, line, advance_product, advance_regularization, c=None, anticipos=None, c_anticipos=None):
		free = ['2','3','4','5','6','7','10','11','12','13','14','15']
		if self.billing_type == '0':
			# taxes with Nubefact
			igv_type = next(filter(lambda tax:tax.eb_afect_igv_id,line.tax_ids)).eb_afect_igv_id.pse_code
		if self.billing_type == '1':
			# taxes with OdooFacturacion
			igv_type = next(filter(lambda tax:tax.eb_afect_igv_id,line.tax_ids)).eb_afect_igv_id.code
			free = ['11','12','13','14','15','16','21','31','32','33','34','35','36','37']
		
		tax_included = next(filter(lambda t:t.price_include,line.tax_ids),None)
		tax_line = next(filter(lambda tax:tax.eb_tributes_type_id and tax.eb_tributes_type_id.code != '7152',line.tax_ids),None)
		tax_percentage = tax_line.amount/100
		quantity = abs(line.quantity)
		price_subtotal = float(Decimal(str(abs(line.price_subtotal))).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP))
		if tax_included:
			price = abs(line.price_unit / (1 + tax_percentage))
			price_igv = abs(line.price_unit)
		else:
			price = abs(line.price_unit)
			price_igv = abs(line.price_unit * (1 + tax_percentage))
		discount = abs((price * quantity) * (line.discount/100))
		igv = abs(price_subtotal * tax_percentage)
		bag_tax = next(filter(lambda tax:tax.eb_tributes_type_id and tax.eb_tributes_type_id.code == '7152',line.tax_ids),None)
		bag_tax = quantity * bag_tax.amount if bag_tax else 0
		total = price_subtotal + igv + bag_tax
		onu_code = line.product_id.onu_code.code if advance_product != line.product_id and line.product_id.type in ['service','product'] else ""
		if self.billing_type == '0':
			#Creating json line to send to Nubefact
			ebill_line = {
				"unidad_de_medida": 'ZZ' if line.product_id.type == 'service' else 'NIU',
				"codigo": line.ref_code if line.ref_code else '',
				"descripcion": line.name + ' (Gratuita)' if igv_type in free else line.name,
				"cantidad": quantity,
				"valor_unitario": price,
				"precio_unitario": price_igv,
				"descuento": discount,
				"subtotal": price_subtotal,
				"tipo_de_igv": igv_type,
				"igv": 0 if igv_type in free else igv,
				"impuesto_bolsas": bag_tax,
				"total": total,
				"anticipo_regularizacion": "false",
				"anticipo_documento_serie": "",
				"anticipo_documento_numero": "",
				"codigo_producto_sunat": onu_code if onu_code else ""
			}
		if self.billing_type == '1':
			#Creating json line to send to OdooFacturacion
			if not advance_regularization:
				ebill_line = {
					"unidad_de_medida": 'ZZ' if line.product_id.type == 'service' else 'NIU',
					"codigo_interno": line.ref_code if line.ref_code else '',
					"descripcion": line.name + ' (Trans.Gratuita)' if igv_type in free else line.name,
					"cantidad": quantity,
					"valor_unitario": 0.00 if igv_type in free else price,
					"codigo_tipo_precio": "02" if igv_type in free else "01",
					"precio_unitario": price_igv,
					"descuento": discount,
					"total_base_igv": price_subtotal,
					"codigo_tipo_afectacion_igv": igv_type,
					"porcentaje_igv": (tax_percentage * 100),
					"total_valor_item": price_subtotal,
					"total_igv": igv,
					"total_icbper": bag_tax,
					"total_impuestos": (igv + bag_tax),
					"total_item": total,
					"anticipo_regularizacion": "false",
					"codigo_producto_sunat": onu_code if onu_code else ""
				}
			else:
				c_ebill_line = {
					"unidad_de_medida": 'ZZ' if line.product_id.type == 'service' else 'NIU',
					"codigo_interno": line.ref_code if line.ref_code else '',
					"descripcion": line.name + ' (Trans.Gratuita)' if igv_type in free else line.name,
					"cantidad": quantity,
					"valor_unitario": 0.00 if igv_type in free else price,
					"codigo_tipo_precio": "02" if igv_type in free else "01",
					"precio_unitario": price_igv,
					"descuento": discount,
					"total_base_igv": price_subtotal,
					"codigo_tipo_afectacion_igv": igv_type,
					"porcentaje_igv": (tax_percentage * 100),
					"total_valor_item": price_subtotal,
					"total_igv": igv,
					"total_icbper": bag_tax,
					"total_impuestos": (igv + bag_tax),
					"total_item": total,
					"anticipo_regularizacion": "false",
					"codigo_producto_sunat": onu_code if onu_code else ""
				}
				c_anticipos.append(c_ebill_line)
				ebill_line = None
		#Creating altern line to save into another model just for informative reasons
		einvoice_line = {
			'move_line_id': line.id,
			'code': line.ref_code,
			'uom': 'ZZ' if line.product_id.type == 'service' else 'NIU',
			'unit_value': price,
			'unit_price': price_igv,
			'discount_value': discount,
			'percentage_discount': line.discount,
			'sunat_product_code': onu_code,
			'igv_type': igv_type,
			'subtotal': price_subtotal,
			'igv': igv,
			'icbper': bag_tax,
			'total': total,
			'advance_regularization': False
		}
		if advance_regularization:
			series = self.advance_ids.mapped('serie')
			numbers = self.advance_ids.mapped('number')
			einvoice_line['advance_regularization'] = True
			if self.billing_type == '0':
				#Creating json line to send to Nubefact
				ebill_line['anticipo_regularizacion'] = "true"
				ebill_line['anticipo_documento_serie'] = einvoice_line['advance_document_serie'] = series[c]
				ebill_line['anticipo_documento_numero'] = einvoice_line['advance_document_number'] = numbers[c]
			if self.billing_type == '1':
				#Creating json line to send to OdooFacturacion
				item_anticipo={
					"numero": series[c] +"-"+ numbers[c],
					"codigo_tipo_documento": "02",
					"monto": price_subtotal
					}
				anticipos.append(item_anticipo)
		line.einvoice_line_id.unlink()
		line.write({'einvoice_line_id': self.env['einvoice.line'].create(einvoice_line).id})
		#raise UserError(str(ebill_line))
		return ebill_line