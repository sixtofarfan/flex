# -*- coding: utf-8 -*-
from odoo import fields,models,api, _
from odoo.exceptions import UserError
from datetime import *
import re,json,urllib3,base64

# Wizard para mostrar la preview de las guias de remision:
class Preview_Remission_Guide_Wizard(models.TransientModel):
	_inherit = 'preview.remission.guide.wizard'

	def post_request(self):
		parameters = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		guide_line = next(filter(lambda s:s.series_id == self.picking_id.serie_guia,parameters.guide_series_ids))
		if not self.electronic_guide:
			return 
		series = self.env['remission.guide.series'].search([('series_id','=',self.picking_id.serie_guia.id),('parameter_id.company_id','=',self.company_id.id)],limit=1)
		# Validaciones:
		if not series:
			raise UserError(u'No se ha encontrado una configuración de parámetros para la serie de guía %s\nVaya a Contabilidad->Configuración->Parámetros->Guía de remisión Electrónica para configurarlos.'%self.picking_id.serie_guia.name)
		now = datetime.strftime(fields.Date.context_today(self),'%Y-%m-%d')
		date_traslate_pick = self.date_traslate if self.date_traslate else self.kardex_date.date()
		traslate = datetime.strftime(date_traslate_pick,'%Y-%m-%d')



		# valor opara poner la factura en la observación
		docfact = ""
		if self.invoice_id.id:
			if self.invoice_id.state == 'posted': 
				docfact=' Fac/Bol.: '+self.invoice_id.ref
		
		if self.picking_id.sale_id.id:
			if self.picking_id.sale_id.client_order_ref:
				docfact += '  Orden de Cliente: ' + self.picking_id.sale_id.client_order_ref
		
		if not self.line_ids:
			raise UserError('No hay líneas de bienes disponibles')

		data = {
			"operacion": "generar_guia",
			"tipo_de_comprobante": 7, # guia de rem remitente = 7
			"serie": self.series,
			"numero": self.number,
			"cliente_tipo_de_documento": self.receiver_partner_id.l10n_latam_identification_type_id.code_sunat,
			"cliente_numero_de_documento":self.receiver_partner_id.vat,
			"cliente_denominacion": self.receiver_partner_id.name,
			"cliente_direccion": self.receiver_partner_id.street,
			"cliente_email": self.receiver_partner_id.email or '',
			"cliente_email_1": "",
			"cliente_email_2": "",
			"fecha_de_emision":now,
			"observaciones": 'LIC. ' + self.license_num + ' ' +self.note  if self.note else 'LIC. ' + self.license_num+ docfact,
			"motivo_de_traslado": self.transfer_reason_id.code,
			"peso_bruto_total": str(self.gross_weight) if self.gross_weight else "0",
			"numero_de_bultos": str(int(self.num_pieces)) if self.num_pieces else "0",
			"tipo_de_transporte": self.transporter_type,
			"fecha_de_inicio_de_traslado": traslate,
			"transportista_documento_tipo": self.transporter_doc_id.code_sunat,
			"transportista_documento_numero": self.transporter_doc,
			"transportista_denominacion": self.transporter_id.name,
			"transportista_placa_numero": self.license_plate or "",
			"conductor_documento_tipo": self.driver_doc_id.code_sunat,
			"conductor_documento_numero": self.driver_doc,
			"conductor_denominacion": self.driver_id.name,
			"punto_de_partida_ubigeo": self.ubigeo_start if self.ubigeo_start else self.picking_id.picking_type_id.warehouse_id.partner_id.district_id.code,
			"punto_de_partida_direccion": self.start_point,
			"punto_de_llegada_ubigeo": self.ubigeo_arrival if self.ubigeo_arrival else self.picking_id.partner_id.district_id.code,
			"punto_de_llegada_direccion": self.point_arrival,
			"enviar_automaticamente_a_la_sunat": "true",
			"enviar_automaticamente_al_cliente": "true",
			"codigo_unico": "",
			"formato_de_pdf": ""
		}
		g_items = []
		for l in self.line_ids:
			if l.move_id.state == 'done':
				g_items.append({
					"unidad_de_medida":'ZZ' if l.product_id.type=='service' else 'NIU',
					"codigo": l.default_code,
					"descripcion": l.description,
					"cantidad": l.quantity,
				})
		data.update({"items":g_items})
		#raise UserError(str(data))
		self.picking_id.json_post = data
		http = urllib3.PoolManager()
		try:
			r = http.request('POST',
							guide_line.path,
							headers = {'Content-Type':'application/json',
									   'Authorization':'Token token = "%s"'%guide_line.token},
							body = json.dumps(data))
		except urllib3.exceptions.HTTPError as e:
			raise UserError(u'Error al procesar datos de guía electrónica!\nDetalles:\n'+e.read())
		response = json.loads(r.data.decode('utf-8'))
		self.picking_id.json_get = response
		if 'errors' in response:
			raise UserError('Respuesta del Facturador: ' + response['errors'])
		if 'enlace_del_pdf' in response:
			self.picking_id.print_web_version_pdf = response['enlace_del_pdf']
		if 'enlace_del_xml' in response:
			self.picking_id.print_web_version_xml = response['enlace_del_xml']
		if 'aceptada_por_sunat' in response:
			self.picking_id.sunat_state = '3'
			self.success_message = u'La transacción se realizó con éxito!'

		return {"type": "ir.actions.do_nothing",}

class PreviewRemissionGuideWizardLine(models.TransientModel):
	_inherit = 'preview.remission.guide.wizard.line'

	description = fields.Char(related='move_id.description', string='Descripcion')
	default_code = fields.Char(related='product_id.ref_code')