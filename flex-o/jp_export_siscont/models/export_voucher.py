# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from xlsxwriter.workbook import Workbook
from datetime import datetime
import re

class ExportVoucher(models.AbstractModel):
    _name = 'report.voucher'
    _description = 'Export Voucher Wizard'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        # workbook = Workbook('export_' + self.name + '.xlsx')
        # Formato de celdas
        worksheet = workbook.add_worksheet("Voucher")
        # bold = workbook.add_format({'bold': True})
        # bold.set_font_size(8)
        # # normal = workbook.add_format()
        # boldbord = workbook.add_format({'bold': True})
        # boldbord.set_border(style=2)
        # boldbord.set_align('center')
        # boldbord.set_align('vcenter')
        # boldbord.set_text_wrap()
        # boldbord.set_font_size(8)
        # boldbord.set_bg_color('#DCE6F1')
        # especial1 = workbook.add_format({'bold': True})
        # especial1.set_align('left')
        # especial1.set_align('vcenter')
        # especial1.set_text_wrap()
        # especial1.set_font_size(15)
        # numbertres = workbook.add_format({'num_format':'0.000'})
        # numberdos = workbook.add_format({'num_format':'#,##0.00'})
        # numberseis = workbook.add_format({'num_format':'#,##0.000000'})
        # numberseis.set_font_size(8)
        # numberocho = workbook.add_format({'num_format':'#,##0.00000000'})
        # numberocho.set_font_size(8)
        # bord = workbook.add_format()
        # bord.set_border(style=1)
        # bord.set_font_size(8)
        # bord2 = workbook.add_format()
        # bord2.set_border(style=1)
        # bord2.set_font_size(8)
        # bord2.set_font_color('blue')
        # numberdos.set_border(style=1)
        # numberdos.set_font_size(8)
        # numbertres.set_border(style=1)
        # numberseis.set_border(style=1)
        # numberocho.set_border(style=1)
        # numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})
        # numberdosbold.set_font_size(8)

        # # Para los negativos
        # bord_red = workbook.add_format({'font_color': '#FF0000'})
        # bord_red.set_border(style=1)
        # bord_red.set_font_size(8)
        # bord2_red = workbook.add_format({'font_color': '#FF0000'})
        # bord2_red.set_border(style=1)
        # bord2_red.set_font_size(8)
        # numberdos_red = workbook.add_format({'num_format':'#,##0.00', 'font_color': '#FF0000'})
        # numberdos_red.set_font_size(8)
        # numberdos_red.set_border(style=1)
        # numberocho_red = workbook.add_format({'num_format':'#,##0.00000000', 'font_color': '#FF0000'})
        # numberocho_red.set_font_size(8)
        # numberocho_red.set_border(style=1)

        x= 0
        # tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        # tam_letra = 1.2

        worksheet.write(x,0,'Origen')
        worksheet.write(x,1,'Num.Voucher')
        worksheet.write(x,2,'Fecha')
        worksheet.write(x,3,'Cuenta')
        worksheet.write(x,4,'Monto Debe')
        worksheet.write(x,5,'Monto Haber')
        worksheet.write(x,6,'Moneda S/D')
        worksheet.write(x,7,'T.Cambio')
        worksheet.write(x,8,'Doc')
        worksheet.write(x,9,'Num.Doc')
        worksheet.write(x,10,'Fec.Doc')
        worksheet.write(x,11,'Fec.Ven')
        worksheet.write(x,12,'Cod.Prov.Clie')
        worksheet.write(x,13,'C.Costo')
        worksheet.write(x,14,'Presupuesto')
        worksheet.write(x,15,'F.Efectivo')
        worksheet.write(x,16,'Glosa')
        worksheet.write(x,17,'Libro C/V/R')
        worksheet.write(x,18,'Mto.Neto 1')
        worksheet.write(x,19,'Mto.Neto 2')
        worksheet.write(x,20,'Mto.Neto 3')
        worksheet.write(x,21,'Mto.Neto 4')
        worksheet.write(x,22,'Mto.Neto 5')
        worksheet.write(x,23,'Mto.Neto 6')
        worksheet.write(x,24,'Mto.Neto 7')
        worksheet.write(x,25,'Mto.Neto 8')
        worksheet.write(x,26,'Mto.Neto 9')
        worksheet.write(x,27,'Mto.IGV')
        worksheet.write(x,28,'Ref.Doc')
        worksheet.write(x,29,'Ref.Num.Doc')
        worksheet.write(x,30,'Ref.Fecha')
        worksheet.write(x,31,'D.Numero')
        worksheet.write(x,32,'D.Fecha')
        worksheet.write(x,33,'RUC')
        worksheet.write(x,34,'R.Social')
        worksheet.write(x,35,'Tipo')
        worksheet.write(x,36,'Tip.Doc.Iden')
        worksheet.write(x,37,'Medio de Pago')
        worksheet.write(x,38,'Apellido 1')
        worksheet.write(x,39,'Apellido 2')
        worksheet.write(x,40,'Nombre')
        worksheet.write(x,41,'T.Bien')

        if wizard.type_voucher == '02':
            account_move_ids = self.env['account.move'].search([('invoice_date','>=',wizard.from_date),('invoice_date','<=',wizard.to_date),('type','in', ('out_invoice','out_refund'))])#.sorted(lambda m: (m.type_document_id == '01',m.type_document_id == '07',m.type_document_id == '08',m.type_document_id == '03'))
        else:
            account_move_ids = self.env['account.move'].search([('invoice_date','>=',wizard.from_date),('invoice_date','<=',wizard.to_date),('type','in', ('in_invoice','in_refund'))])
        
        doc_ids = self.env['account.move']

        doc_ids += account_move_ids.filtered(lambda m: m.type_document_id.code == '01')
        doc_ids += account_move_ids.filtered(lambda m: m.type_document_id.code == '07')
        doc_ids += account_move_ids.filtered(lambda m: m.type_document_id.code == '08')
        doc_ids += account_move_ids.filtered(lambda m: m.type_document_id.code == '03')
        doc_ids += account_move_ids.filtered(lambda m: m.type_document_id.code not in ('01','07','08','03'))
        x = 1
        y = 1

        for move in doc_ids:
            for line in move.line_ids:
                 worksheet.write(y, 0, wizard.type_voucher) #Origen
                 worksheet.write(y, 1, x) #Num. Voucher
                 worksheet.write(y, 2, datetime.strftime(move.date,'%d/%m/%Y')) #Fecha
                 worksheet.write(y, 3, line.account_id.code) #Cuenta
                 worksheet.write(y, 4, (abs(line.amount_currency) if line.debit > 0 else '') if line.amount_currency else (line.debit if line.debit > 0 else '')) #Monto Debe
                 worksheet.write(y, 5, (abs(line.amount_currency) if line.credit > 0 else '') if line.amount_currency else (line.credit if line.credit > 0 else '')) #Monto Haber
                 worksheet.write(y, 6, move.currency_id.singular_name[:1]) #'D' if move.currency_id else 'S') #Moneda S/D
                 worksheet.write(y, 7, move.currency_rate) #T.Cambio
                 worksheet.write(y, 8, move.type_document_id.code) #Doc
                 worksheet.write(y, 9, move.ref) #Num.Doc
                 worksheet.write(y, 10, datetime.strftime(move.invoice_date or move.date,'%d/%m/%Y')) #Fec.Doc
                 worksheet.write(y, 11, datetime.strftime(move.invoice_date_due,'%d/%m/%Y')) #Fec.Ven
                 worksheet.write(y, 12, move.partner_id.vat) #Cod.Prov.Clie
                 worksheet.write(y, 13, '') #C.Costo
                 worksheet.write(y, 14, '') #Presupuesto
                 worksheet.write(y, 15, '') #F.Efectivo
                 worksheet.write(y, 16, move.glosa) #Glosa
                 worksheet.write(y, 17, ('V' if wizard.type_voucher == '02' else 'C') if line.account_id.code[:2] == '40' else '') #Libro C/V/R
                 worksheet.write(y, 18, move.amount_untaxed if line.account_id.code[:2] == '40' else '') #Mto.Neto 1
                 worksheet.write(y, 19, '') #Mto.Neto 2
                 worksheet.write(y, 20, '') #Mto.Neto 3
                 worksheet.write(y, 21, '') #Mto.Neto 4
                 worksheet.write(y, 22, '') #Mto.Neto 5
                 worksheet.write(y, 23, '') #Mto.Neto 6
                 worksheet.write(y, 24, '') #Mto.Neto 7
                 worksheet.write(y, 25, '') #Mto.Neto 8
                 worksheet.write(y, 26, '') #Mto.Neto 9
                 worksheet.write(y, 27, move.amount_tax if line.account_id.code[:2] == '40' else '') #Mto.IGV
                 worksheet.write(y, 28, '') #Ref.Doc
                 worksheet.write(y, 29, '') #Ref.Num.Doc
                 worksheet.write(y, 30, datetime.strftime(move.invoice_date,'%d/%m/%Y') if line.account_id.code[:2] == '40' else '') #Ref.Fecha
                 worksheet.write(y, 31, '') #D.Numero
                 worksheet.write(y, 32, '') #D.Fecha
                 worksheet.write(y, 33, move.partner_id.vat) #RUC
                 worksheet.write(y, 34, re.sub('[^A-Za-z0-9 ]+ ', '', move.partner_id.name)) #R.Social
                 worksheet.write(y, 35, '2' if move.partner_id.l10n_latam_identification_type_id.name == 'RUC' else '1') #Tipo
                 worksheet.write(y, 36, '6' if move.partner_id.l10n_latam_identification_type_id.name == 'RUC' else '1') #Tip.Doc.Iden
                 worksheet.write(y, 37, '') #Medio de Pago
                 worksheet.write(y, 38, '') #Apellido 1
                 worksheet.write(y, 39, '') #Apellido 2
                 worksheet.write(y, 40, '') #Nombre
                 worksheet.write(y, 41, '') #T.Bien
                 y += 1
            x += 1 
        
		# # Crear diccionario Kardex
        # ck = get_value.ComputeKardex()
        # location_ids = wizard.location_ids #self.env['stock.location'].search([('usage','=','internal')])
        # product_ids = wizard.product_ids #self.env['product.product'].search([('id','in', wizard.product_ids)])
        # for location in location_ids:
        #     for product in product_ids:
        #         list_data = ck.create_kardex_dict(product.id, wizard.locked_period, location.id, wizard.end_date.strftime('%Y-%m-%d 23:59:59'), self.env)
        #         if not list_data:
        #             continue
        #         if x > 0:
        #             x += 3
        #         # Encabezado
        #         worksheet.merge_range(x+0,0,x+0,20,'FORMATO 13.1: "REGISTRO DE INVENTARIO PERMANENTE VALORIZADO - DETALLE DEL INVENTARIO VALORIZADO"',especial1)
        #         if str(wizard.initial_date)[5:7] == str(wizard.end_date)[5:7]:
        #             period = str(wizard.initial_date)[5:7] + '-' + str(wizard.initial_date)[:4]
        #         else:
        #             period = str(wizard.initial_date)[5:7] + '-' + str(wizard.initial_date)[:4] + ' al ' + str(wizard.end_date)[:4] + '-' + str(wizard.end_date)[5:7]
        #         worksheet.write(x+2,0,'PERIODO: ' + period,bold)
        #         worksheet.write(x+3,0,'RUC: ' + self.env.user.company_id.partner_id.vat if self.env.user.company_id.partner_id.vat else 'Vat number not configured in company.',bold)
        #         worksheet.write(x+4,0,'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: ' + self.env.user.company_id.partner_id.name,bold)
        #         worksheet.write(x+5,0,'ESTABLECIMIENTO (1): ' + location.name) #+ wh_names if self.alllocations == False else 'ESTABLECIMIENTO (1): TODOS',bold)
        #         worksheet.write(x+6,0,'CÓDIGO DE LA EXISTENCIA: ' + product.default_code if product.default_code else 'CÓDIGO DE LA EXISTENCIA: Sin código de producto',bold)
        #         worksheet.write(x+7,0,'TIPO (TABLA 5): ' + product.categ_id.existence_type_id.name if product.categ_id.existence_type_id else 'No tiene tipo de existencia en la categoría',bold)
        #         worksheet.write(x+8,0,'DESCRIPCIÓN: ' + product.name,bold)
        #         worksheet.write(x+9,0,'CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): ' + product.uom_id.sunat_code if product.uom_id.sunat_code else 'CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): ' + product.uom_id.name, bold) #'El producto no tiene unidad de medida de kardex',bold)
        #         worksheet.write(x+10,0,'MÉTODO DE VALUACIÓN: ' + dict(product.categ_id._fields['property_cost_method']._description_selection(self.env)).get(product.categ_id.property_cost_method),bold)
        #         worksheet.merge_range(x+13,0,x+14,3, u"DOCUMENTO DE TRASLADO, COMPROBANTE DE PAGO, DOCUMENTO INTERNO O SIMILAR",boldbord)
        #         worksheet.write(x+15,0, u"FECHA",boldbord)
        #         worksheet.write(x+15,1, u"TIPO (TABLA 10)",boldbord)
        #         worksheet.write(x+15,2, u"SERIE",boldbord)
        #         worksheet.write(x+15,3, u"NUMERO",boldbord)
        #         worksheet.merge_range(x+13,4,x+15,4, u"TIPO DE OPERACIÓN (TABLA 12)",boldbord)
        #         worksheet.merge_range(x+13,5,x+13,7, "ENTRADAS",boldbord)
        #         worksheet.merge_range(x+14,5,x+15,5, "CANTIDAD",boldbord)
        #         worksheet.merge_range(x+14,6,x+15,6, "COSTO UNITARIO",boldbord)
        #         worksheet.merge_range(x+14,7,x+15,7, "COSTO TOTAL",boldbord)
        #         worksheet.merge_range(x+13,8,x+13,10, "SALIDAS",boldbord)
        #         worksheet.merge_range(x+14,8,x+15,8, "CANTIDAD",boldbord)
        #         worksheet.merge_range(x+14,9,x+15,9, "COSTO UNITARIO",boldbord)
        #         worksheet.merge_range(x+14,10,x+15,10, "COSTO TOTAL",boldbord)
        #         worksheet.merge_range(x+13,11,x+13,13, "SALDO FINAL",boldbord)
        #         worksheet.merge_range(x+14,11,x+15,11, "CANTIDAD",boldbord)
        #         worksheet.merge_range(x+14,12,x+15,12, "COSTO UNITARIO",boldbord)
        #         worksheet.merge_range(x+14,13,x+15,13, "COSTO TOTAL",boldbord)

        #         x += 16
                
        #         total = 0

        #         for item in list_data:

        #             total += item['in_qty'] - item['out_qty']

        #             worksheet.write(x, 0, item['date'], bord if total >= 0 else bord_red)
        #             worksheet.write(x, 1, item['type_document'], bord if total >= 0 else bord_red)
        #             worksheet.write(x, 2, item['serie'], bord if total >= 0 else bord_red)
        #             worksheet.write(x, 3, item['number'], (bord if total >= 0 else bord2_red) if item['number'][:13] != _('Initial Balance') else bord2)
        #             worksheet.write(x, 4, item['type_operation'], bord if total >= 0 else bord_red)
        #             worksheet.write(x, 5, item['in_qty'], numberdos if total >= 0 else numberdos_red)
        #             worksheet.write(x, 6, float_round(item['in_cost'], 8), numberocho if total >= 0 else numberocho_red)
        #             worksheet.write(x, 8, item['out_qty'], numberdos if total >= 0 else numberdos_red)
        #             worksheet.write(x, 9, float_round(item['out_cost'], 8), numberocho if total >= 0 else numberocho_red)
        #             worksheet.write_formula('H' + str(x+1), '=F' + str(x+1) + ' * G' + str(x+1), numberdos if total >= 0 else numberdos_red)
        #             worksheet.write_formula('K' + str(x+1), '=I' + str(x+1) + ' * J' + str(x+1), numberdos if total >= 0 else numberdos_red)
        #             if x == 16:
        #                 worksheet.write_formula('L' + str(x+1), '=F' + str(x+1) + ' - I' + str(x+1), numberdos if total >= 0 else numberdos_red)
        #                 worksheet.write_formula('N' + str(x+1), '=H' + str(x+1) + ' - K' + str(x+1), numberdos if total >= 0 else numberdos_red)
        #             else:
        #                 worksheet.write_formula('L' + str(x+1), '=F' + str(x+1) + ' - I' + str(x+1) + ' + L' + str(x), numberdos if total >= 0 else numberdos_red)
        #                 worksheet.write_formula('N' + str(x+1), '=H' + str(x+1) + ' - K' + str(x+1) + ' + N' + str(x), numberdos if total >= 0 else numberdos_red)
        #             if total != 0:
        #                 worksheet.write_formula('M' + str(x+1), '=N' + str(x+1) + ' / L' + str(x+1), numberocho if total >= 0 else numberocho_red)
        #             else:
        #                 worksheet.write_formula('M' + str(x+1), '=0', numberocho if total >= 0 else numberocho_red)

        #             x += 1
        