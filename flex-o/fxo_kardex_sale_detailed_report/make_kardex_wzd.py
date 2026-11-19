# -*- coding: utf-8 -*-
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import odoo.addons.decimal_precision as dp

import base64
from odoo import models, fields, api
import codecs

from odoo.exceptions import ValidationError

values = {}


class sale_detailed_report(models.TransientModel):
    _name = "sale.detailed.report"

    fini = fields.Date('Fecha inicial', required=True)
    ffin = fields.Date('Fecha final', required=True)
    products_ids = fields.Many2many('product.product', 'rel_wiz_sale_detailed_report', 'product_id', 'report_id')
    location_ids = fields.Many2many('stock.location', 'rel_location_valorado_sale_detailed_report', 'location_id',
                                    'report_id',
                                    'Ubicacion', required=True)
    allproducts = fields.Boolean('Todos los productos', default=True)
    destino = fields.Selection([('csv', 'CSV')], 'Destino')
    check_fecha = fields.Boolean('Editar Fecha')
    alllocations = fields.Boolean('Todos los almacenes', default=True)

    fecha_ini_mod = fields.Date('Fecha Inicial')
    fecha_fin_mod = fields.Date('Fecha Final')
    analizador = fields.Boolean('Analizador')
    clientes = fields.Many2many('res.partner', string="Clientes")
    user_ids = fields.Many2many('res.users', string="Usuarios")
    type_pickings_id = fields.Many2many('stock.picking.type', string="Tipo Operaciòn")
    type_pickings_sunat_id = fields.Many2many('type.operation.kardex', string="Tipo Operaciòn SUNAT")
    all_clientes = fields.Boolean(default=True, string="Todos los Clientes")
    all_users = fields.Boolean(default=True, string="Todos los Vendedores")
    all_type_operation = fields.Boolean(default=True, string="Todos los Tipo de Operacion")
    all_type_operation_sunat = fields.Boolean(default=True, string="Todos los Tipo de Operacion SUNAT")

    @api.onchange('fecha_ini_mod')
    def onchange_fecha_ini_mod(self):
        self.fini = self.fecha_ini_mod

    @api.onchange('fecha_fin_mod')
    def onchange_fecha_fin_mod(self):
        self.ffin = self.fecha_fin_mod

    @api.model
    def default_get(self, fields):
        res = super(sale_detailed_report, self).default_get(fields)
        import datetime
        fecha_hoy = str(datetime.datetime.now())[:10]
        fecha_inicial = fecha_hoy[:4] + '-01-01'
        res.update({'fecha_ini_mod': fecha_inicial})
        res.update({'fecha_fin_mod': fecha_hoy})
        res.update({'fini': fecha_inicial})
        res.update({'ffin': fecha_hoy})

        # locat_ids = self.pool.get('stock.location').search(cr, uid, [('usage','in',('internal','inventory','transit','procurement','production'))])
        locat_ids = self.env['stock.location'].search(
            [('usage', 'in', ('internal', 'inventory', 'transit', 'procurement', 'production'))])
        locat_ids = [elemt.id for elemt in locat_ids]
        res.update({'location_ids': [(6, 0, locat_ids)]})
        return res

    @api.onchange('alllocations')
    def onchange_alllocations(self):
        if self.alllocations == True:
            locat_ids = self.env['stock.location'].search(
                [('usage', 'in', ('internal', 'inventory', 'transit', 'procurement', 'production'))])
            self.location_ids = [(6, 0, locat_ids.ids)]
        else:
            self.location_ids = [(6, 0, [])]

    def do_csvtoexcel_two2(self):
        cad = ""

        s_prod = [-1, -1, -1]
        s_loca = [-1, -1, -1]

        if self.all_type_operation_sunat == True:
            operations_sunat_ids = self.env['type.operation.kardex'].search([])
            lst_operations_sunat = operations_sunat_ids.ids
        else:
            lst_operations_sunat = self.type_pickings_sunat_id.ids
        operations_sunat = '('
        for ops in lst_operations_sunat:
            operations_sunat = operations_sunat + str(ops) + ','
            # s_prod.append(producto)
        operations_sunat = operations_sunat[:-1] + ')'

        if self.all_type_operation == True:
            operations_ids = self.env['stock.picking.type'].search([])
            lst_operations = operations_ids.ids
        else:
            lst_operations = self.user_ids.ids
        operations = '('
        for op in lst_operations:
            operations = operations + str(op) + ','
            # s_prod.append(producto)
        operations = operations[:-1] + ')'

        if self.all_users == True:
            users_ids = self.env['res.users'].search([])
            lst_users = users_ids.ids
        else:
            lst_users = self.user_ids.ids
        users = '('
        for user in lst_users:
            users = users + str(user) + ','
            # s_prod.append(producto)
        users = users[:-1] + ')'

        if self.all_clientes == True:
            partner_ids = self.env['res.partner'].search([])
            lst_partners = partner_ids.ids
        else:
            lst_partners = self.clientes.ids
        partners = '('
        for partner in lst_partners:
            partners = partners + str(partner) + ','
            # s_prod.append(producto)
        partners = partners[:-1] + ')'

        if self.alllocations == True:
            locat_ids = self.env['stock.location'].search(
                [('usage', 'in', ('internal', 'inventory', 'transit', 'procurement', 'production'))])
            lst_locations = locat_ids.ids
        else:
            lst_locations = self.location_ids.ids
        lst_products = self.products_ids.ids
        productos = '('
        almacenes = '('
        date_ini = self.fini
        date_fin = self.ffin
        if self.allproducts:
            lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids

        else:
            lst_products = self.products_ids.ids

        if len(lst_products) == 0:
            raise ValidationError('No existen productos seleccionados')

        for producto in lst_products:
            productos = productos + str(producto) + ','
            s_prod.append(producto)
        productos = productos[:-1] + ')'
        for location in lst_locations:
            almacenes = almacenes + str(location) + ','
            s_loca.append(location)
        almacenes = almacenes[:-1] + ')'

        import io
        from xlsxwriter.workbook import Workbook
        output = io.BytesIO()

        direccion = self.env['main.parameter'].search([])[0].dir_create_file
        workbook = Workbook(direccion + 'kardex_producto.xlsx')
        worksheet = workbook.add_worksheet("Kardex")
        bold = workbook.add_format({'bold': True})
        bold.set_font_size(8)
        normal = workbook.add_format()
        boldbord = workbook.add_format({'bold': True})
        boldbord.set_border(style=2)
        boldbord.set_align('center')
        boldbord.set_align('vcenter')
        boldbord.set_text_wrap()
        boldbord.set_font_size(8)
        boldbord.set_bg_color('#DCE6F1')

        especial1 = workbook.add_format({'bold': True})
        especial1.set_align('center')
        especial1.set_align('vcenter')
        especial1.set_text_wrap()
        especial1.set_font_size(15)

        numbertres = workbook.add_format({'num_format': '0.000'})
        numberdos = workbook.add_format({'num_format': '0.00'})
        numberseis = workbook.add_format({'num_format': '0.000000'})
        numberseis.set_font_size(8)
        numberocho = workbook.add_format({'num_format': '0.00000000'})
        numberocho.set_font_size(8)
        bord = workbook.add_format()
        bord.set_border(style=1)
        bord.set_font_size(8)
        numberdos.set_border(style=1)
        numberdos.set_font_size(8)
        numbertres.set_border(style=1)
        numberseis.set_border(style=1)
        numberocho.set_border(style=1)
        numberdosbold = workbook.add_format({'num_format': '0.00', 'bold': True})
        numberdosbold.set_font_size(8)

        formatdate = workbook.add_format({'num_format': 'dd-mm-yyyy'})
        x = 10
        tam_col = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        tam_letra = 1.2

        worksheet.merge_range(1, 5, 1, 10, "REPORTE DETALLADO DE VENTAS", especial1)
        worksheet.write(2, 1, 'FECHA INICIO:', bold)
        worksheet.write(3, 1, 'FECHA FIN:', bold)

        worksheet.write(2, 2, str(self.fini))
        worksheet.write(3, 2, str(self.ffin))
        import datetime

        # worksheet.merge_range(8,0,9,0, u"Fecha Alm.",boldbord)

        headers = [
            (u"Fecha Emision", 1),
            (u"Tipo", 1),
            (u"Serie Factura", 1),
            (u"Almacen", 1),
            (u"Fecha de Venc.", 1),
            (u"Guia", 1),
            (u"Observaciones", 1),
            (u"RUC", 1),
            (u"Empresa", 1),
            (u"Direccion", 1),
            (u"Departamento", 1),
            (u"Provincia", 1),
            (u"Distrito", 1),
            (u"Categoria de Producto", 1),
            (u"Producto", 1),
            (u"Codigo Producto", 1),
            (u"Bonificacion", 1),
            (u"Lotes", 1),
            (u"Cantidad", 1),
            (u"Valor Venta unitario V/U", 1),
            (u"%Desc", 1),
            (u"Sub Total", 1),
            (u"Total", 1),
            (u"Costo unit.", 1),
            (u"Vendedor", 1),
            (u"Equipo de Venta", 1),
            (u"Tipo Cliente", 1),
            (u"Destino", 1),
            (u"Origen", 1),

        ]
        xp = 0
        for h in headers:
            xp += h[1]
            worksheet.merge_range(8, xp, 9, xp, h[0], boldbord)

        query_new = f'''
        SELECT am.invoice_date as fecha_emision,
           ec01.code  as tipo,
           am.ref  as serie,
           aml.doc_almacenx  as doc_almacenx,
           am.invoice_date_due as invoice_date_venx,
           aml.numbergx as guia ,
           aml.albaran_originx as albaran_originx,
           rp.vat as rucx,
           rp.name as empresax,
           aml.direccion_completax as direccion_completax,
           rcs.name as departamentox,
           rcsp.name as provinciax,
           rcsd.name as distritox,	   
           pc.name as categoria_productox,
           pt.name as product_namex,
           pt.default_code as product_codex,
           CASE
                WHEN aml.is_free = True THEN 'SI'
                ELSE 'NO'
                END as bonificacionx,
           aml.lotesx as lotesx,
           aml.demandadox as demandadox, 
           CASE
                WHEN aml.is_free = True THEN 0
                ELSE aml.price_unit
                END as invoice_price_unitxy,	
           CASE
                WHEN aml.is_free = True THEN 0
                ELSE aml.discount
                END as invoice_line_descx,
           CASE
                WHEN aml.is_free = True THEN 0
                ELSE round(aml.price_subtotal::DECIMAL,2)
                END as invoice_line_subtotalxy,
           CASE
                WHEN aml.is_free = True THEN 0
                ELSE round(aml.price_total::DECIMAL,2)
                END as invoice_line_totalxy,           
            round(aml.cost_unitx::DECIMAL,2) as costo_unit,                
            am.invoice_user_name as vendedorx,
            ct.name as sale_team,          
            aml.tipo_clienteex as tipo_clienteex,
            aml.destino_loccx as destino_loccx,
            aml.origin_loccx  as origin_loccx
            FROM account_move_line aml 
            LEFT JOIN account_move am ON (aml.move_id=am.id)
            LEFT JOIN einvoice_catalog_01 ec01 ON (am.type_document_id=ec01.id)
            LEFT JOIN res_partner rp ON (am.partner_id=rp.id)
            LEFT JOIN res_country_state rcs ON (rp.state_id=rcs.id)
            LEFT JOIN res_country_state rcsp ON (rp.province_id=rcsp.id)
            LEFT JOIN res_country_state rcsd ON (rp.district_id=rcsd.id)
            LEFT JOIN product_product pp ON (aml.product_id=pp.id)
            LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
            LEFT JOIN product_category pc ON (pt.categ_id = pc.id)
            LEFT JOIN res_users ru ON (am.invoice_user_id=ru.id)
            LEFT JOIN crm_team  ct ON (am.team_id = ct.id)
            WHERE am.invoice_date between '{date_ini}' and '{date_fin}'
                    AND pp.id IN {productos}
                    AND origin_locx IN {almacenes}                    
                    AND ru.id IN {users}     
                    AND type_picking_idx IN {operations}               
                    AND rp.id IN {partners}  
                    AND type_operation_sunatx IN {operations_sunat}                  
                '''

        self.env.cr.execute(query_new)

        k = self.env.cr.fetchall()

        for line in k:
            xi = 1
            for l in line:
                worksheet.write(x, xi, str(l).replace('\n', ' ').replace('\r', '') if l else '', bord)
                xi += 1

            x = x + 1

        workbook.close()

        f = open(direccion + 'kardex_producto.xlsx', 'rb')

        return self.env['popup.it'].get_file('Kardex_Valorado.xlsx', base64.encodestring(b''.join(f.readlines())))
