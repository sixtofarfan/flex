from odoo import models, fields, api
from decimal import *
from odoo.exceptions import UserError
import json
from datetime import *
import urllib3
import re
import base64

from odoo.addons.payment.models.payment_acquirer import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'
    retencion_amount = fields.Float(string='Monto de Retencion')

    def send_ebill(self):
        parameters = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        self.verify_invoice_data(parameters)
        DetractionCodes = parameters.catalog_51_detraction_ids.mapped('code')
        AdvancesCodes = parameters.catalog_51_advance_ids.mapped('pse_code')
        fact_line = next(filter(lambda s: s.serie_id == self.serie_id and s.billing_type == parameters.billing_type,
                                parameters.serial_nubefact_lines))
        # Defining variables
        ebill_lines, m_anticipos, c_anticipos, invoice_with_advance, exportation = [], [], [], False, None
        total_saved, total_free, total_exonerate, total_inafect, total_export, total_discount, total_igv, total_advance, total_icbper = 0, 0, 0, 0, 0, 0, 0, 0, 0

        # stupid counter
        c = 0

        for line in self.invoice_line_ids:
            exportation_type = next(
                filter(lambda tax: tax.eb_afect_igv_id and tax.eb_afect_igv_id.code == '40', line.tax_ids), None)
            if exportation_type:
                exportation = True if exportation_type.eb_tributes_type_id.code == '9995' else False
            advance_product = next(
                filter(lambda a_line: a_line.product_id == line.product_id, parameters.advance_product_ids), None)
            if advance_product and self.op_type_sunat_id.pse_code in AdvancesCodes:
                if self.billing_type == '0':
                    ebill_lines.append(self.generate_lines(line, advance_product, True, c, m_anticipos, c_anticipos))
                if self.billing_type == '1':
                    self.generate_lines(line, advance_product, True, c, m_anticipos, c_anticipos)
                    total_advance += abs(line.price_subtotal)
                # raise UserError(str(ebill_lines))
                c += 1
            # if not advance_product or not self.op_type_sunat_id.code in AdvancesCodes:
            else:
                ebill_lines.append(self.generate_lines(line, advance_product, False))

        # raise UserError(str(ebill_lines))
        # Defining flag to know if the invoice is free or not
        free_flag = True
        for e_line in ebill_lines:
            if self.billing_type == '0':
                # Creating json's totals to send to Nubefact
                total_icbper += e_line['impuesto_bolsas']
                total_discount += e_line['descuento']
                if e_line['anticipo_regularizacion'] == "true":
                    total_igv -= e_line['igv']
                else:
                    if e_line['tipo_de_igv'] not in ['2', '3', '4', '5', '6', '7', '10', '11', '12', '13', '14', '15']:
                        total_igv += e_line['igv']
                if e_line['tipo_de_igv'] in ['1']:
                    free_flag = False
                    if e_line['anticipo_regularizacion'] == "true":
                        total_saved -= e_line['subtotal']
                    else:
                        total_saved += e_line['subtotal']
                if e_line['tipo_de_igv'] in ['2', '3', '4', '5', '6', '7', '10', '11', '12', '13', '14', '15']:
                    total_free += e_line['subtotal']
                if e_line['tipo_de_igv'] in ['8']:
                    free_flag = False
                    if e_line['anticipo_regularizacion'] == "true":
                        total_exonerate -= e_line['subtotal']
                    else:
                        total_exonerate += e_line['subtotal']
                if e_line['tipo_de_igv'] in ['9']:
                    free_flag = False
                    if e_line['anticipo_regularizacion'] == "true":
                        total_inafect -= e_line['subtotal']
                    else:
                        total_inafect += e_line['subtotal']
                if e_line['tipo_de_igv'] in ['16']:
                    if exportation:
                        total_inafect += e_line['subtotal']
                        free_flag = False
                    else:
                        total_free += e_line['subtotal']
                if e_line['anticipo_regularizacion'] == "true":
                    invoice_with_advance = True
                    total_advance += e_line['subtotal']
                    free_flag = False

            if self.billing_type == '1':
                # Creating json's totals to send to OdooFacturacion

                total_icbper += e_line['total_icbper']
                total_discount += e_line['descuento']
                if e_line['anticipo_regularizacion'] == "true":
                    total_igv -= e_line['total_igv']
                else:
                    if e_line['codigo_tipo_precio'] == "01":
                        total_igv += e_line['total_igv']
                if e_line['codigo_tipo_afectacion_igv'] in ['10']:
                    free_flag = False
                    total_saved += e_line['total_valor_item']
                if e_line['codigo_tipo_afectacion_igv'] in ['11', '12', '13', '14', '15', '16', '21', '31', '32', '33',
                                                            '34', '35', '36', '37']:
                    total_free += e_line['total_item']
                if e_line['codigo_tipo_afectacion_igv'] in ['20']:
                    total_exonerate += e_line['total_valor_item']
                    free_flag = False
                if e_line['codigo_tipo_afectacion_igv'] in ['30']:
                    total_inafect += e_line['total_valor_item']
                    free_flag = False
                if e_line['codigo_tipo_afectacion_igv'] in ['40']:
                    if exportation:
                        total_inafect += e_line['total_valor_item']
                        free_flag = False
                    else:
                        total_free += e_line['total_valor_item']
            # else:
            #	invoice_with_advance = True
            #	#total_advance +=  e_line['total_valor_item']
            #	free_flag = False

        if self.billing_type == '1' and c > 0:
            for c_line in c_anticipos:
                total_igv -= c_line['total_igv']
                total_saved -= c_line['total_valor_item']

        total_saved = float(Decimal(str(abs(total_saved))).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP))
        total_igv = float(Decimal(str(abs(total_igv))).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP))

        head_total = total_saved + total_inafect + total_exonerate + total_igv

        invoice_footer = self.narration if parameters.comment_add_check and self.narration else ""
        invoice_footer += ('<br>' + parameters.bank_numbers) if parameters.bank_numbers else ""

        if self.billing_type == '0':
            # Creating json's header to send to Nubefact
            ebill_json = {
                "operacion": "generar_comprobante",
                "tipo_de_comprobante": self.type_document_id.pse_code,
                "serie": self.ref.split('-')[0],
                "numero": int(self.ref.split('-')[1]),
                "sunat_transaction": int(self.op_type_sunat_id.pse_code),
                "cliente_tipo_de_documento": self.partner_id.commercial_partner_id.l10n_latam_identification_type_id.code_sunat,
                "cliente_numero_de_documento": self.partner_id.commercial_partner_id.vat,
                "cliente_denominacion": self.partner_id.commercial_partner_id.name,
                "cliente_direccion": self.partner_id.street,
                "cliente_email": self.partner_id.email if self.partner_id.email else "",
                "cliente_email_1": "",
                "cliente_email_2": "",
                "fecha_de_emision": datetime.strftime(self.invoice_date, '%Y-%m-%d'),
                "fecha_de_vencimiento": datetime.strftime(self.invoice_date_due, '%Y-%m-%d'),
                "moneda": self.currency_id.pse_code,
                "tipo_de_cambio": self.currency_rate if self.currency_id.name != 'PEN' else "",
                "porcentaje_de_igv": float(
                    Decimal(str(parameters.igv_tax_id.amount)).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)),
                "descuento_global": "",
                "total_descuento": total_discount,
                "total_anticipo": total_advance,
                "total_gravada": total_saved,
                "total_inafecta": total_inafect,
                "total_exonerada": total_exonerate,
                "total_igv": total_igv,
                "total_gratuita": total_free,
                "total_otros_cargos": "",
                "total_impuestos_bolsas": total_icbper,
                "total": head_total,
                "percepcion_tipo": "",
                "percepcion_base_imponible": "",
                "total_percepcion": "",
                "total_incluido_percepcion": "",
                "detraccion": "true" if self.op_type_sunat_id.code in DetractionCodes else "false",
                "detraccion_tipo": int(
                    self.detraction_type_id.pse_code) if self.op_type_sunat_id.code in DetractionCodes else "",
                "detraccion_total": self.detraction_amount if self.op_type_sunat_id.code in DetractionCodes else 0,
                "medio_de_pago_detraccion": self.detraction_payment_id.pse_code if self.op_type_sunat_id.code in DetractionCodes else "",
                "observaciones": "Pedido: {0}\n{1}".format(self.invoice_origin,
                                                           invoice_footer) if parameters.invoice_origin_check and self.invoice_origin else (
                    invoice_footer),
                "documento_que_se_modifica_tipo": self.doc_invoice_relac[
                    0].type_document_id.pse_code if self.type_document_id.pse_code in ['3', '4'] else "",
                "documento_que_se_modifica_serie": self.doc_invoice_relac[0].nro_comprobante.split('-')[
                    0] if self.type_document_id.pse_code in ['3', '4'] else "",
                "documento_que_se_modifica_numero": self.doc_invoice_relac[0].nro_comprobante.split('-')[
                    1] if self.type_document_id.pse_code in ['3', '4'] else "",
                "tipo_de_nota_de_credito": int(
                    self.credit_note_type_id.code) if self.type == 'out_refund' and self.type_document_id.pse_code == '3' else "",
                "tipo_de_nota_de_debito": int(
                    self.debit_note_type_id.code) if self.type == 'out_invoice' and self.type_document_id.pse_code == '4' else "",
                "enviar_automaticamente_a_la_sunat": "true",
                "enviar_automaticamente_al_cliente": "true" if self.partner_id.email else "false",
                "codigo_unico": "",
                "condiciones_de_pago": self.invoice_payment_term_id.name if self.invoice_payment_term_id else "",
                "medio_de_pago": "",
                "placa_vehiculo": "",
                "orden_compra_servicio": (
                    self.doc_origin_customer if self.doc_origin_customer else "") if parameters.doc_origin_customer_check else "",
                "tabla_personalizada_codigo": "",
                "formato_de_pdf": ""
            }

            # agregando plazo de pagos
            plazos = self.invoice_payment_term_id.line_ids
            total_dias = 0
            for p in plazos:
                total_dias += p.days
            json_plazos = []

            if self.retencion_amount < 0:
                raise ValidationError('El campo "Retencion" no debe ser negativo')
            if total_dias > 0:
                index = 0
                amount_accumulated = 0
                fecha = datetime.strptime(str(self.invoice_date), '%Y-%m-%d')
                # fecha = self.invoice_date
                if parameters.send_multi_credits:
                    for p in plazos:
                        index += 1
                        if p.option == 'day_after_invoice_date':
                            fecha = fecha + timedelta(days=(p.days))
                            # fecha = fecha.strftime('%d-%m-%Y')
                            str_date = f'''{fecha.day}/{fecha.month}/{fecha.year}'''
                        if p.option in ['after_invoice_month', 'day_following_month']:
                            if not p.day_of_the_month > 0:
                                raise ValidationError('dia del mes invalido')
                            next_mes = int(fecha.month) + 1
                            str_date = f'''{p.day_of_the_month}/{next_mes}/{fecha.year}'''
                            # fecha = datetime.strptime(str_date, '%Y-%m-%d')
                        if p.option in ['day_current_month']:
                            if not p.day_of_the_month > 0:
                                raise ValidationError('dia del mes invalido')
                            str_date = f'''{p.day_of_the_month}/{fecha.month}/{fecha.year}'''
                            # fecha = datetime.strptime(str_date, '%Y-%m-%d')

                        importe = None
                        if p.value == 'balance':
                            importe = head_total - amount_accumulated
                        if p.value == 'percent':
                            importe = p.value_amount * head_total / 100
                        if p.value == 'fixed':
                            importe = p.value_amount

                        amount_accumulated += importe
                        if fecha and importe:
                            json_plazos.append({
                                "cuota": index,
                                # "cuota": 1,
                                "fecha_de_pago": str_date,
                                "importe": round(importe - self.retencion_amount, 10) if index == 1 else round(importe,
                                                                                                               10)
                            })
                else:
                    fecha = fecha + timedelta(days=(total_dias))
                    str_date = f'''{fecha.day}/{fecha.month}/{fecha.year}'''
                    json_plazos.append({
                        "cuota": 1,
                        "fecha_de_pago": str_date,
                        "importe": round(head_total - self.retencion_amount, 10)
                    })

                # raise ValidationError(index)
                # raise ValidationError(str(json_plazos))
                if json_plazos:
                    ebill_json.update({"venta_al_credito": json_plazos})
                    ebill_json["medio_de_pago"] = 'credito'

        if self.billing_type == '1':
            # Creating json's header to send to OdooFacturacion
            datos_del_cliente = {
                "codigo_tipo_documento_identidad": self.partner_id.commercial_partner_id.l10n_latam_identification_type_id.code_sunat,
                "numero_documento": self.partner_id.commercial_partner_id.vat,
                "apellidos_y_nombres_o_razon_social": self.partner_id.commercial_partner_id.name,
                "direccion": self.partner_id.street,
                "correo_electronico": self.partner_id.email or self.commercial_partner_id.email or "",
                "codigo_pais": "PE",
                "ubigeo": ""
            }
            m_totales = {
                "total_descuentos": "%.6f" % total_discount,
                "total_anticipos": "%.2f" % total_advance,
                "total_operaciones_gravadas": "%.2f" % abs(total_saved),
                "total_operaciones_inafectas": "%.2f" % abs(total_inafect),
                "total_operaciones_exoneradas": "%.2f" % abs(total_exonerate),
                "total_operaciones_gratuitas": "%.2f" % abs(total_free),
                "total_exportacion": 0.00,
                "total_icbper": "%.2f" % total_icbper,
                "total_igv": "%.2f" % abs(total_igv),
                "total_impuestos": "%.2f" % abs(total_igv + total_icbper),
                "total_valor": "%.2f" % total_saved,
                "total_venta": "%.2f" % head_total
            }
            m_acciones = {
                "formato_pdf": "a4"
            }
            o_observaciones = '<b>Forma de pago: </b>%s<br>' % self.invoice_payment_term_id.name if self.invoice_payment_term_id else ""
            o_observaciones += '<b>Pedido:</b> {0}\n{1}'.format(self.invoice_origin,
                                                                invoice_footer) if parameters.invoice_origin_check and self.invoice_origin else invoice_footer
            ebill_json = {
                "codigo_tipo_operacion": self.op_type_sunat_id.code,
                "codigo_tipo_documento": self.type_document_id.code,
                "serie_documento": self.ref.split('-')[0],
                "numero_documento": int(self.ref.split('-')[1]),
                "fecha_de_emision": datetime.strftime(self.invoice_date, '%Y-%m-%d'),
                "fecha_de_vencimiento": datetime.strftime(self.invoice_date_due, '%Y-%m-%d'),
                "hora_de_emision": str(fields.Datetime.now()),
                "codigo_tipo_moneda": self.currency_id.name,
                # "tipo_de_cambio": self.currency_rate if self.currency_id.name != 'PEN' else "",
                "informacion_adicional": o_observaciones,
                "enviar_automaticamente_al_cliente": "true" if self.partner_id.email else "false",
                "codigo_unico": "",
                "condiciones_de_pago": self.invoice_payment_term_id.name if self.invoice_payment_term_id else "",
                "medio_de_pago": "",
                # "placa_vehiculo": "",
                "numero_orden_de_compra": (
                    self.doc_origin_customer if self.doc_origin_customer else "") if parameters.doc_origin_customer_check else ""
            }
            if self.type_document_id.code in ['07', '08']:
                ebill_json.update({
                                      'motivo_o_sustento_de_nota': self.credit_note_type_id.name if self.type_document_id.code in [
                                          '07'] else self.debit_note_type_id.name})
                tipo_nota = '01'
                for fac_relacionada in self.doc_invoice_relac:
                    fact = self.env['account.move'].search(
                        [('ref', '=', fac_relacionada.nro_comprobante), ('type', '=', 'out_invoice'),
                         ('type_document_id', '=', fac_relacionada.type_document_id.id)])
                    afecta_ext = ""
                    tipo_nota = fac_relacionada.type_document_id.code
                    if len(fact) > 0:
                        if fact[0].codigo_unico:
                            afecta_ext = fact[0].codigo_unico
                            m_documento_afectado = {
                                "external_id": str(afecta_ext)
                            }
                        else:
                            m_documento_afectado = {
                                "codigo_tipo_documento": fac_relacionada.type_document_id.code,
                                "serie_documento": fac_relacionada.nro_comprobante.split('-')[0],
                                "numero_documento": fac_relacionada.nro_comprobante.split('-')[1]
                            }
                    else:
                        m_documento_afectado = {
                            "codigo_tipo_documento": fac_relacionada.type_document_id.code,
                            "serie_documento": fac_relacionada.nro_comprobante.split('-')[0],
                            "numero_documento": fac_relacionada.nro_comprobante.split('-')[1]
                        }
                ebill_json.update({'codigo_tipo_nota': tipo_nota})
                ebill_json.update({'documento_afectado': m_documento_afectado})
            ebill_json.update({"datos_del_cliente_o_receptor": datos_del_cliente})
            ebill_json.update({"totales": m_totales})
            ebill_json.update({"acciones": m_acciones})
            if len(m_anticipos) > 0:
                ebill_json.update({"anticipos": m_anticipos})

        # Add guides info
        guide_lines = []

        if len(self.guide_line_ids) > 0 and self.type_document_id.code in ['01']:
            for guide in self.guide_line_ids:
                if not guide.numberg:
                    raise UserError(u'El # Guia de Remision no esta establecido en su albarán.')
                if self.billing_type == '0':
                    # Creating json's guias to send to Nubefact
                    guide_lines.append({
                        "guia_tipo": 1,
                        "guia_serie_numero": self.check_format_numberg(guide.numberg)
                    })
                if self.billing_type == '1':
                    # Creating json's guias to send to OdooFacturacion
                    guide_lines.append({
                        "codigo_tipo_documento": "09",
                        "numero": self.check_format_numberg(guide.numberg)
                    })

            ebill_json.update({"guias": guide_lines})

        ebill_json.update({"items": ebill_lines})
        # Creating alternative header just for informative reasons
        einvoice = {
            "move_id": self.id,
            "total_saved": total_saved,
            "total_inafect": total_inafect,
            "total_exonerate": total_exonerate,
            "total_free": total_free,
            "total_discount": total_discount,
            "total_advance": total_advance,
            "total_igv": total_igv,
            "total_icbper": total_icbper,
            "total_voucher": head_total
        }
        #raise UserError(str(ebill_json))
        self.json_sent = str(ebill_json)
        # Deleting Informative table in case exits one cause i don't want to have trash data
        self.einvoice_id.unlink()
        self.write({'einvoice_id': self.env['einvoice'].create(einvoice).id})
        http = urllib3.PoolManager()
        try:
            if self.billing_type == '0':
                r = http.request('POST',
                                 fact_line.nubefact_path,
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': 'Token token = "%s"' % fact_line.nubefact_token},
                                 body=json.dumps(ebill_json))
            if self.billing_type == '1':
                r = http.request('POST',
                                 fact_line.nubefact_path + '/documents',
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': 'Bearer %s' % fact_line.nubefact_token},
                                 body=json.dumps(ebill_json))
        except urllib3.exceptions.HTTPError as e:
            raise UserError("Error al intentar conectarse: \n\t %s" % e.reason)
        response = json.loads(r.data.decode('utf-8'))
        #raise UserError(str(response))
        if self.billing_type == '0':
            if 'errors' in response:
                raise UserError('Respuesta del Facturador: ' + response['errors'])
            if 'codigo_hash' in response:
                self.hash_code = response['codigo_hash']
            if 'enlace_del_pdf' in response:
                self.print_version = response['enlace_del_pdf']
                pdf = http.request('GET', response['enlace_del_pdf'])
            # self.binary_version = base64.encodestring(''.join(pdf.readlines()))
            if 'enlace_del_xml' in response:
                self.xml_version = response['enlace_del_xml']
            if 'enlace_del_cdr' in response:
                self.cdr_version = response['enlace_del_cdr']
            if 'cadena_para_codigo_qr' in response:
                self.qr_code = response['cadena_para_codigo_qr']
            if 'aceptada_por_sunat' in response:
                self.sunat_state = '3'
            self.json_response = str(response)
        if self.billing_type == '1':
            if response['success']:
                self.hash_code = response['data']['hash']
                self.print_version = response['links']['pdf']
                pdf = http.request('GET', response['links']['pdf'])
                # self.binary_version = base64.encodestring(''.join(pdf.readlines()))
                self.xml_version = response['links']['xml']
                self.cdr_version = response['links']['cdr']
                self.qr_code = response['data']['qr_text']
                self.codigo_unico = response['data']['external_id']
                self.sunat_state = '3'
            else:
                raise UserError('Respuesta del Facturador: ' + response['message'])

        return self.env['popup.it'].get_message("SE ENVIO EL COMPROBANTE SATISFACTORIAMENTE")



