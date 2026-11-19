# -*- coding: utf-8 -*-
from odoo import api, fields, models
from contextlib import closing
from datetime import datetime
import json
import cx_Oracle
from cx_Oracle import Error

class SyncDataIn(models.Model):
    _name = 'sync.data.in'
    _order = 'fecha_proceso'

    name = fields.Char('Numero de Transaccion')
    fecha_proceso = fields.Datetime('Fecha proceso')
    tipo = fields.Selection([('I', 'Ingreso'), ('S','Salida')], 'tipo de proceso')
    datas_json = fields.Text("JSON Data", readonly=True)
    cabecera_id = fields.Char(string='Id de Factura Origen')
    invoice_id = fields.Many2one('account.move', string='Factura registrada')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft')


    def registrar_documento(self, item):
        REGISTRO_TERMINADO = 'T'
        existe_error = False
        numero_documento = ''
      #  try:
        #if True:
        existe_error = False
        cabecera_id = item.get('id')
        partner_id = self.obtener_receptor(item.get('receptor'), item.get('id'))

        if not partner_id:
            existe_error = True
            str_error = 'No existe cliente'
            self.registrar_error_proceso(str_error, cabecera_id)

        data_documento = item.get('documento')
        serie_documento = data_documento.get('serie_documento')
        numero_documento = data_documento.get('correlativo_documento')
        existe_documento = self.existe_registro(data_documento)
        print("***********:", existe_documento)
        #equipo_venta_id = self.obtener_canal_venta(item.get('equipo_venta'))

        if existe_documento:
            existe_error = True
            str_error = 'Documento ya registrado'
            self.registrar_error_proceso(str_error, cabecera_id)

        # journal_id = self.env['account.journal'].search([('code', '=', serie_documento), ('type', '=', 'sale'),('pe_invoice_code', '=', data_documento.get('codigo_tipo_documento'))])
        journal_id = self.env['account.journal'].search([('code', '=', serie_documento), ('type', '=', 'sale') ])
        #for journal in journal_id:
        #    print("journal_id :", journal.id)
        #    print("journal_id :", journal.name)

        if not journal_id:
            existe_error = True
            str_error = 'No existe Journal'
            self.registrar_error_proceso(str_error, cabecera_id)

        date_invoice = datetime.strptime(data_documento.get('fecha_emision'), '%Y-%m-%d').date()
        # today = fields.Date.context_today(self, datetime.now())
        # days = datetime.strptime(today, '%Y-%m-%d').date() - date_invoice
        # if days.days > 50 or days.days < 0:
        #     existe_error = True
        #     str_error = 'La fecha de emision no puede ser menor a 6 dias de hoy ni mayor a la fecha de hoy.'
        #     self.registrar_error_proceso(str_error, cabecera_id)

        if not existe_error:
            tipo_documento = self.env['einvoice.catalog.01'].search([('code', '=', data_documento.get('codigo_tipo_documento')) ])
            nota_cred_deb = False
            inv = {
                'partner_id': partner_id.id,
                'partner_shipping_id': partner_id.id,
                'date': data_documento.get('fecha_emision'),
                'invoice_date_due': data_documento.get('fecha_vencimiento'),
                'type' : data_documento.get('tipo'),
                'journal_id': journal_id.id,
                'type_document_id':tipo_documento.id,
                'ref': data_documento.get('correlativo_documento'), 
                'glosa':data_documento.get('correlativo_documento'), 
                'cabecera_id': cabecera_id,
                'invoice_line_ids' :[]
            }     
            invoice_line_ids = self.registrar_detalle_documento(item.get('detalle_docuento'))
                   
            for  item in invoice_line_ids:
                inv['invoice_line_ids'].append((0, 0, item))

            invoice_id = self.env['account.move'].create(inv)

            if data_documento.get('codigo_tipo_documento') in ('07', '08'):
                nota_cred_deb = item.get('nota_credito') or item.get('nota_debito')

            if nota_cred_deb:
                codigo_nota_deb = False
                codigo_nota_cred = False
                if data_documento.get('codigo_tipo_documento') == '07':
                    codigo_nota_cred = item.get('codigo_motivo')
                elif data_documento.get('codigo_tipo_documento') == '08':
                    codigo_nota_deb = item.get('codigo_motivo')
                invoice_id.write({
                    'origin_doc_code': nota_cred_deb.get('tipo_documento'),
                    'origin_doc_number': nota_cred_deb.get('numero_documento'),
                    'origin': nota_cred_deb.get('numero_documento'),
                    'name': nota_cred_deb.get('descripcion'),
                    'pe_debit_note_code': codigo_nota_deb,
                    'pe_credit_note_code': codigo_nota_cred
                })


            if not existe_error:
                invoice_id.write({
                    'name': data_documento.get('correlativo_documento'),
                   # 'move_name': data_documento.get('correlativo_documento'),
                    'data_sync_id': self.id
                })

                #invoice_id.compute_taxes()

                self.invoice_id = invoice_id.id

       # except ValueError:
        #    str_error = 'error al registrar documento'
        #    self.registrar_error_proceso(str_error, cabecera_id)
        #    existe_error = True
        return existe_error

    def obtener_canal_venta(self, equipo_venta):
        nombre_equipo_venta = equipo_venta.get('nombre_equipo_venta')
        equipo_venta_id = self.env['crm.team'].search([('name','=', nombre_equipo_venta)])
        if not equipo_venta_id:
            equipo_venta_id = self.env['crm.team'].create({'name':nombre_equipo_venta, 'team_type': 'sales'})

        return equipo_venta_id

    def obtener_producto_servicio(self, detalle):
        TYPE2TIPOPRODUCTO = {'SERVICES': 'service', 'PRODUCT': 'product'}
        tipo = detalle.get('tipo')
        codigo_producto = detalle.get('codigo_producto')

        product_id = self.env['product.product'].search([('default_code', '=', codigo_producto)])
        if product_id:
            product_id = product_id[0]
        else:
            company_id = self.env.user.company_id
            if tipo == 'PRODUCT':
                product_id = company_id.product_varios_id
            if tipo == 'SERVICES':
                product_id = company_id.service_varios_id

            nombre_producto = detalle.get('descripcion_producto')
            print('nombre_producto:', nombre_producto)

            #buscando product_template
            product_template_id = self.env['product.template'].search([('type', '=', tipo),('default_code', '=', codigo_producto)])

            if not product_template_id:
                val_producto = {
                    'name': detalle.get('descripcion_producto'),
                    'type': TYPE2TIPOPRODUCTO[tipo],
                    'uom_id': 1,
                    'uom_po_id': 1,
                    'default_code': codigo_producto,
                    #'categ_id': product_id.categ_id.id,
                    'list_price': product_id.list_price,
                    'standard_price': product_id.standard_price,
                    #'taxes_id': [(6, 0, [product_id.taxes_id.id])],
                    #'supplier_taxes_id': [(6, 0, [product_id.supplier_taxes_id.id])],
                    'invoice_policy': product_id.invoice_policy
                }
                product_template_id = self.env['product.template'].create(val_producto)

            #creando producto.
            val_producto = {
                'description': detalle.get('descripcion_producto'),
                'name': detalle.get('descripcion_producto'),
                #'categ_id': product_template_id.id,
                'default_code': codigo_producto,
                #'categ_id': product_id.categ_id.id,
                'list_price': product_id.list_price,
                'invoice_policy': product_id.invoice_policy
            }
            product_id = self.env['product.product'].create(val_producto)

        return product_id

    def registrar_detalle_documento(self, detalle_item):
        existe_error = False
        invoice_line_ids = []
        for detalle in detalle_item:
            cabecera_id = detalle.get('id')

            #Obtencion del producto/servicio
            product_id = self.obtener_producto_servicio(detalle)
            print("product_id:", product_id)

            #Obtener impuesto
            porc_tax = detalle.get('porcentaje_impuesto')
            tax_id = self.env['account.tax'].search([('amount', '=', float(porc_tax)), ('price_include','=',False),('type_tax_use', '=', 'sale')])

            if not tax_id:
                existe_error = True
                str_error = 'No existe Impuesto'
                self.registrar_error_proceso(str_error, cabecera_id)

            #Obtener medida
            if not product_id.uom_id:
                existe_error = True
                str_error = 'No existe Medida'
                self.registrar_error_proceso(str_error, cabecera_id)

            # if not invoice_id.journal_id:
            #     existe_error = True
            #     str_error = 'No existe Diario'
            #     self.registrar_error_proceso(str_error, cabecera_id)

            # if len(invoice_id.journal_id) > 1:
            #     existe_error = True
            #     str_error = 'Existe mas de un Diario'
            #     self.registrar_error_proceso(str_error, cabecera_id)

            # if not invoice_id.journal_id.default_debit_account_id:
            #     existe_error = True
            #     str_error = 'No existe Cuenta'
            #     self.registrar_error_proceso(str_error, cabecera_id)

            #registro de linea
            if not existe_error:
                datos_linea  = {
                    'discount' : detalle.get('porcentaje_descuento'),
                    'name' : detalle.get('codigo_producto') + '-' + detalle.get('descripcion_producto'),
                    'quantity': detalle.get('numero_item'),
                    'tax_ids': [(6, 0, tax_id.ids)],
                    'pe_affectation_code': '10',
                    'product_uom_id': product_id.uom_id.id,
                    'price_unit': detalle.get('precio_unitario'),
                    'product_id': product_id.id,
                    'detalle_id': detalle.get('detalle_id')
                }
                invoice_line_ids.append(datos_linea)

        return invoice_line_ids

    def obtener_receptor(self, data_receptor, cabecera_id):
        doc_type = data_receptor.get('tipo_documento')
        numero_documento = data_receptor.get('numero_documento')
        nombre = data_receptor.get('razon_social')

        se_crear_cliente = False
        cliente_id = self.env['res.partner'].search([('vat', '=', numero_documento)])
        if not cliente_id:
            se_crear_cliente = True
            cliente_id = self.env['res.partner'].create({
              #  'doc_type': doc_type,
                'vat': numero_documento,
                'name': nombre,
                'email': data_receptor.get('correo_electronico')
            })

            existe_error = False
            if doc_type == '1':
                company_id = self.env.user.company_id
                if len(numero_documento) != 8:
                    existe_error = True
                    str_error = 'El DNI no es correcto'
                    self.registrar_advertencia_proceso(str_error, cabecera_id)
                    cliente_id = company_id.anonymous_id
                if not existe_error:
                    respuesta = cliente_id.buscar_dni(numero_documento.strip())
                    if not respuesta or respuesta['detail'] == 'Not found.':
                        existe_error = True
                        str_error = 'El Numero de DNI ingresado es incorrecto o no existe'
                        self.registrar_advertencia_proceso(str_error, cabecera_id)
                        cliente_id = company_id.anonymous_id
                if existe_error and not company_id.anonymous_id:
                    #self.registrar_error_proceso(str_error, cabecera_id)
                    cliente_id = company_id.anonymous_id
                if existe_error and company_id.anonymous_id:
                    cliente_id = company_id.anonymous_id
            # if not existe_error:
            #     cliente_id.update_document()

            email = data_receptor.get('correo_electronico')
            if cliente_id and not existe_error and email:
                cliente_id.write({
                    'email': email
                })
        return cliente_id

    def procesar(self):
        data_json = self.datas_json
        data_json = json.loads(data_json)
        self.registrar_documento(data_json)


    def validar_documento_receptor(self, datos_receptor = {}):
        if not datos_receptor:
            datos_partner = self.env['res.partner'].browser([('doc_type', datos_receptor.get('tipo_documento')), ('doc_number', datos_receptor.get('numero_documento'))])
            if datos_partner:
                return datos_partner.id
            else:
                return -1

    def registrar_advertencia_proceso(self, detalle_error, cabecera_id):
        REGISTRO_ERROR = 'R'
        sql_update = ("""
            UPDATE CLI_DOCUMENTO SET DESCRIPCION_VALIDACION = substr(DESCRIPCION_VALIDACION|| ' '  || '%s', 0, 50) WHERE ID_DOCUMENTO_FAC = %s
        """)%(detalle_error, cabecera_id)

        self.ejecutar_script(sql_update)

    def registrar_error_proceso(self, detalle_error, cabecera_id):
        REGISTRO_ERROR = 'E'
        sql_update = ("""
            UPDATE CLI_DOCUMENTO SET DESCRIPCION_VALIDACION = substr(DESCRIPCION_VALIDACION|| ' '  || '%s', 0, 50), ESTADO_PROCESO = '%s' WHERE ID_DOCUMENTO_FAC = %s
        """)%(detalle_error, REGISTRO_ERROR, cabecera_id)

        self.ejecutar_script(sql_update)

    def existe_registro(self, data_documento):
        invoice_id = self.env['account.move'].search([('ref', '=', data_documento.get('correlativo_documento'))])
        print(invoice_id)
        return invoice_id

    def select_detalle_in(self, cabecera_id):
        sql_select = ("""
            SELECT 
                NULL AS ID_DOCUMENTO_DETALLE,
                ID_DOCUMENTO_FAC,
                COD_PRODUCTO,
                DESCRIPCION,
                CANTIDAD,
                UNIDAD_MEDIDA,
                PRECIO_VENTA,
                CODIGO_IMPUESTO,
                MONTO_BASE,
                MONTO_IMPUESTO,
                PORCENTAJE, 
                TIPO_PRODUCTO,
                MONTO_DESCUENTO,
                FACTOR_DESCUENTO*100 as FACTOR_DESCUENTO,
                VALOR_UNITARIO
            FROM VW_DETALLE_PERU
            WHERE ID_DOCUMENTO_FAC = %s
            """)%(cabecera_id)

        registros = self.ejecutar_script(sql_select)
        registro = {}
        lista_id_procesado = []
        lista_registro = []
        if registros is not None and len(registros) > 0:
            for r in registros:
                r = list(r)
                id_detalle = r[0]
                maestro_id = r[1]
                codigo_producto = r[2]
                descripcion_producto = r[3]
                numero_item = r[4]
                unidad_medida = r[5]
                precio_venta = r[6]
                codigo_impuesto = r[7]
                monto_base_impuesto = r[8]
                monto_impuesto = r[9]
                porcentaje_impuesto = r[10]
                tipo = r[11]
                descuento = r[12]
                porcentaje_descuento = r[13]
                precio_unitario = r[14]

                lista_id_procesado.append(id_detalle)
                detalle = {
                    'id': maestro_id,
                    'id_detalle': id_detalle,
                    'codigo_producto': codigo_producto,
                    'descripcion_producto': descripcion_producto,
                    'numero_item': numero_item,
                    'unidad_medida': unidad_medida,
                    'precio_unitario': precio_unitario,
                    'codigo_impuesto': codigo_impuesto,
                    'monto_base_impuesto': monto_base_impuesto,
                    'monto_impuesto': monto_impuesto,
                    'porcentaje_impuesto': porcentaje_impuesto,
                    'tipo': tipo,
                    'descuento': descuento,
                    'porcentaje_descuento': porcentaje_descuento
                }

                lista_registro.append(detalle)

        return lista_registro

    def select_automatic_in(self):
        TYPE2JOURNAL = {'01':'out_invoice',
                        '03':'out_invoice',
                        '07':'out_refund',
                        '08':'out_invoice'}
        REGISTRO_NUEVO = 'N'

        sql_select = ("""
        SELECT 
            ID_DOCUMENTO_FAC, 
            TIPO_DOC_ENTIDAD, 
            NUM_DOC_IDENTIDAD, 
            RAZON_SOCIAL, 
            DIRECCION, 
            SUBSTR(TIPO_DOC_IDEN, 2, 1) AS TIPO_DOC_IDEN, 
            NUM_DOC_IDE, 
            APELLIDOS,
            DIRECCION_CLIENTE,
            SERIE, 
            NUMERACION,
            TO_CHAR(FECHA, 'YYYY-MM-DD') AS FECHA,
            CODIGO_TIPO_DOC,
            TIPO_MONEDA,
            TO_CHAR(FECHA_VENCIMIENTO, 'YYYY-MM-DD') AS FECHA_VENCIMIENTO, 
            TOTAL_VALOR_VENTAS,
            TIPO_COMPROBANTE, 
            NUMERO_OTRO_DOC,
            CODIGO_MOTIVO_GENE,
            NULL AS DESCRIPCION_MOT_NC_ND,
            ID_BODEGA, 
            NOMBRE_BODEGA,
            EMAIL AS CORREO_ELECTRONICO
        FROM VW_CABECERA_PERU
          WHERE ESTADO_PROCESO = '%s' """%REGISTRO_NUEVO)

        #print(sql_select)
        registros = self.ejecutar_script(sql_select)

        registro = {}
        lista_id_procesado = []
        lista_registro = []
        if registros is not None and len(registros) > 0:
            for r in registros:
                r = list(r)
                cabecera_id = r[0]
                print ('xxxxxxxxxxxxxxx')
                print (cabecera_id)
                print ('xxxxxxxxxxxxxxx')

                emisor_tipo_documento = r[1]
                emisor_numero_documento =  r[2]
                emisor_razon_social = r[3]
                emisor_direccion = r[4]
                receptor_tipo_documento = r[5]
                receptor_numero_documento = r[6]
                receptor_razon_social = r[7]
                receptor_direccion = r[8]
                #print ('******************')
                #print (receptor_numero_documento)
                #print (receptor_razon_social) 
                documento_serie_documento = r[9]
                documento_numero_documento = r[10]
                documento_fecha_emision = r[11]
                documento_tipo_documento = r[12]
                documento_codigo_moneda = r[13]
                documento_fecha_vencimiento = r[14]
                documento_importe_total = r[15]

                doc_rel_nota_credito_debito_tipo_doc = r[16]
                doc_rel_nota_credito_debito_numero_documento = r[17]
                #doc_rel_nota_credito_debito_serie_documento = r[18]
                doc_rel_nota_credito_debito_codigo_motivo = r[18]
                doc_rel_nota_credito_debito_descripcion = False #r[19]

                lista_id_procesado.append(cabecera_id)

                id_equipo_venta = r[20]
                nombre_equipo_venta = r[21]
                correo_electronico = r[22]

                if not self.existe_regitro_cabecera(cabecera_id):
                    p_estado = 'N' #r[20]

                    type = TYPE2JOURNAL[documento_tipo_documento]
                    registro = {
                        'id': cabecera_id,
                        'emisor': {
                            'tipo_documento': emisor_tipo_documento,
                            'numero_documento': emisor_numero_documento,
                            'razon_social': emisor_razon_social,
                            'direccion': emisor_direccion,
                        },
                        'receptor': {
                            'tipo_documento': receptor_tipo_documento,
                            'numero_documento': receptor_numero_documento,
                            'razon_social': receptor_razon_social,
                            'direccion': receptor_direccion,
                            'correo_electronico': correo_electronico
                        },
                        'documento': {
                            'serie_documento': documento_serie_documento,
                            'numero_documento': documento_numero_documento,
                            'correlativo_documento': (str(documento_serie_documento)+'-'+str(documento_numero_documento)),
                            'fecha_emision': documento_fecha_emision,
                            'codigo_tipo_documento': documento_tipo_documento,
                            'codigo_moneda': documento_codigo_moneda,
                            'fecha_vencimiento': documento_fecha_vencimiento,
                            'importe_total': documento_importe_total,
                            'tipo': type
                        },
                        'equipo_venta':{
                            'id_equipo_venta': id_equipo_venta,
                            'nombre_equipo_venta': nombre_equipo_venta
                        },
                        'nota_credito': {},
                        'nota_debito': {},
                        'detalle_docuento' : [],
                        'estado': p_estado
                    }
                    detalle_documento = self.select_detalle_in(cabecera_id)

                    if detalle_documento:
                        registro['detalle_docuento'] = detalle_documento

                    if documento_tipo_documento == '08':
                        nota_credito = {
                            'documento_relacionado_nota_credito': {
                                'tipo_documento': doc_rel_nota_credito_debito_tipo_doc,
                                'numero_documento': doc_rel_nota_credito_debito_numero_documento,
                                #'serie_documento': doc_rel_nota_credito_debito_serie_documento,
                                'codigo_motivo': doc_rel_nota_credito_debito_codigo_motivo,
                                'descripcion': doc_rel_nota_credito_debito_descripcion
                            }
                        }
                        registro['nota_credito'] = nota_credito

                    if documento_tipo_documento == '07':
                        nota_debito = {
                            'documento_relacionado_nota_debito': {
                                'tipo_documento': doc_rel_nota_credito_debito_tipo_doc,
                                'numero_documento': doc_rel_nota_credito_debito_numero_documento,
                                #'serie_documento': doc_rel_nota_credito_debito_serie_documento,
                                'codigo_motivo': doc_rel_nota_credito_debito_codigo_motivo,
                                'descripcion': doc_rel_nota_credito_debito_descripcion
                            }
                        }
                        registro['nota_debito'] = nota_debito


                    record = self.with_context(tz="America/Lima")
                    fecha_actual = fields.Datetime.context_timestamp(record, datetime.now())
                    local_date = datetime.strptime(fecha_actual.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")
                    reg_in = {
                        'name': registro.get('documento').get('correlativo_documento'),
                        'tipo': 'I',
                        'datas_json' : str(json.dumps(registro)),
                        'cabecera_id' : registro.get('id')
                    }

                    registro_id = self.env['sync.data.in'].create(reg_in)
                    # sfr print("registro_id:", registro_id)
                    registro_id.procesar()
                else:
                    print("Registro existente")

    def select_automatic_out(self):
        REGISTRO_TERMINADO = 'T'
        registros = self.env['sync.data.in'].search([('state', '=', 'draft')], limit=2)

        for registro in registros:
            try:
                #registro.procesar()
                invoice_id = registro.invoice_id
               # invoice_id.action_invoice_open()

                pe_response = False
                if invoice_id.pe_response or invoice_id.pe_cpe_id.note:
                    pe_response = invoice_id.pe_response[:49] or invoice_id.pe_cpe_id.note[:49] or ''

                if invoice_id.pe_digest:
                    sql_update = """
                               UPDATE CLI_DOCUMENTO SET CODIGO_HASH = '%s', DESCRIPCION_VALIDACION = '%s', ESTADO_PROCESO = '%s', FECHA_PROCESO = SYSDATE WHERE ID_DOCUMENTO_FAC = %s
                           """ % (invoice_id.pe_digest, pe_response, REGISTRO_TERMINADO, invoice_id.cabecera_id)
                    self.ejecutar_script(sql_update)

                    registro.state = 'done'
                    registro.fecha_proceso = fields.Date.context_today(self, datetime.now())

            except ValueError:
                print("error:", ValueError)

    def procesar_facturas_pendientes(self):
        REGISTRO_TERMINADO = 'T'
        invoice_ids = self.env['account.move'].search([('state', '=', 'draft')])
        # sfr print("Pendientes:", invoice_ids)
        for invoice_id in invoice_ids:
            try:
                invoice_id.action_invoice_open()
                pe_response = False
                if invoice_id.pe_response or invoice_id.pe_cpe_id.note:
                    pe_response = invoice_id.pe_response[:49] or invoice_id.pe_cpe_id.note[:49] or ''

                if invoice_id.pe_digest:
                   sql_update = """
                       UPDATE CLI_DOCUMENTO SET CODIGO_HASH = '%s', DESCRIPCION_VALIDACION = '%s', ESTADO_PROCESO = '%s', FECHA_PROCESO = SYSDATE WHERE ID_DOCUMENTO_FAC = %s
                   """ % (invoice_id.pe_digest, pe_response, REGISTRO_TERMINADO, invoice_id.cabecera_id)
                   self.ejecutar_script(sql_update)

                #if invoice_id.partner_id.email:
                #    invoice_id.action_invoice_sent()

            except ValueError:
                print("error:", ValueError)

    def select_automatic_annul(self):
        REGISTRO_ANULADO = 'A'
        REGISTRO_TERMINADO = 'T'

        sql_select = """
                    SELECT ID_DOCUMENTO_FAC FROM CLI_DOCUMENTO WHERE ESTADO_PROCESO = '%s'
                """ % (REGISTRO_ANULADO)
        registros = self.ejecutar_script(sql_select)

        if registros is not None and len(registros) > 0:
            for registro in registros:
                registro = list(registro)
                cabecera_id = registro[0]
                invoice_ids = self.env['account.move'].search([('cabecera_id', '=', cabecera_id)])
                for invoice_id in invoice_ids:
                    invoice_id.action_invoice_annul()
                    sql_update = """UPDATE CLI_DOCUMENTO SET ESTADO_PROCESO = '%s' where ID_DOCUMENTO_FAC = %s """% (REGISTRO_TERMINADO, cabecera_id)
                    self.ejecutar_script(sql_update)

    def ejecutar_script(self, sql):
        company_id = self.env.user.company_id
        username = company_id.sync_data_server_id.usuario
        clave = company_id.sync_data_server_id.password
        puerto = company_id.sync_data_server_id.puerto
        nombre_servicio = company_id.sync_data_server_id.nombre_servicio
        servidor = company_id.sync_data_server_id.servidor

        if username and clave and puerto and nombre_servicio and servidor:
            try:
                dsn_tns = cx_Oracle.makedsn(servidor, puerto, service_name=nombre_servicio)
                conexion = cx_Oracle.connect(user=username, password=clave, dsn=dsn_tns)
                cursor = conexion.cursor()
                sql_alter_session = """alter session set nls_date_format ='DD-MM-RR'"""
                cursor.execute(sql_alter_session)
                cursor.execute(sql)

                if sql.upper().find('UPDATE') != -1:
                    conexion.commit()
                if sql.upper().find('SELECT') != -1:
                    result = cursor.fetchall()
                    print("longitud de datos: %s"%result)
                    return result
            except:
                print("error en conexion")
                return None
        else:
            print('sin conexion')

    def existe_regitro_cabecera(self, cabecera_id):
        existe = False
        registro = self.env['account.move'].search([('cabecera_id','=',cabecera_id)])
        if registro:
            existe = True
        return existe

    def sen_invoice_sunat(self):
        invoice = self.env['account.move'].search(
            [('amount_total_signed', '>', 0), ('state', '=', 'draft')])
        for item in invoice:
            item.action_invoice_open()
            self.registrar_estado(item.cabecera_id)
    
    def registrar_estado(self,cabecera_id):
        sql_update = "UPDATE CLI_DOCUMENTO SET ESTADO_PROCESO = 'T' where ID_DOCUMENTO_FAC = " + str(cabecera_id)
        self.ejecutar_script(sql_update)

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    cabecera_id = fields.Char(string='Id de tabla de tabla origen')
    data_sync_id = fields.Many2one('sync.data.in', string='Documento Sync')


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'
    
    detalle_id = fields.Char(string='id de tabla detalle origen')
