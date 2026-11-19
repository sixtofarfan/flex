from odoo import models, _
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import base64
import codecs
import datetime
import pytz
import os
from . import get_value
from odoo.tools import float_round

class KardexXlsx(models.AbstractModel):
    _name = 'report.kardex'
    _description = 'Report Kardex'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):

        # Formato de celdas
        worksheet = workbook.add_worksheet("Kardex")
        bold = workbook.add_format({'bold': True})
        bold.set_font_size(8)
        # normal = workbook.add_format()
        boldbord = workbook.add_format({'bold': True})
        boldbord.set_border(style=2)
        boldbord.set_align('center')
        boldbord.set_align('vcenter')
        boldbord.set_text_wrap()
        boldbord.set_font_size(8)
        boldbord.set_bg_color('#DCE6F1')
        especial1 = workbook.add_format({'bold': True})
        especial1.set_align('left')
        especial1.set_align('vcenter')
        especial1.set_text_wrap()
        especial1.set_font_size(15)
        numbertres = workbook.add_format({'num_format':'0.000'})
        numberdos = workbook.add_format({'num_format':'#,##0.00'})
        numberseis = workbook.add_format({'num_format':'#,##0.000000'})
        numberseis.set_font_size(8)
        numberocho = workbook.add_format({'num_format':'#,##0.00000000'})
        numberocho.set_font_size(8)
        bord = workbook.add_format()
        bord.set_border(style=1)
        bord.set_font_size(8)
        bord2 = workbook.add_format()
        bord2.set_border(style=1)
        bord2.set_font_size(8)
        bord2.set_font_color('blue')
        numberdos.set_border(style=1)
        numberdos.set_font_size(8)
        numbertres.set_border(style=1)
        numberseis.set_border(style=1)
        numberocho.set_border(style=1)
        numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})
        numberdosbold.set_font_size(8)

        # Para los negativos
        bord_red = workbook.add_format({'font_color': '#FF0000'})
        bord_red.set_border(style=1)
        bord_red.set_font_size(8)
        bord2_red = workbook.add_format({'font_color': '#FF0000'})
        bord2_red.set_border(style=1)
        bord2_red.set_font_size(8)
        numberdos_red = workbook.add_format({'num_format':'#,##0.00', 'font_color': '#FF0000'})
        numberdos_red.set_font_size(8)
        numberdos_red.set_border(style=1)
        numberocho_red = workbook.add_format({'num_format':'#,##0.00000000', 'font_color': '#FF0000'})
        numberocho_red.set_font_size(8)
        numberocho_red.set_border(style=1)

        x= 0
        # tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        # tam_letra = 1.2

		# Crear diccionario Kardex
        ck = get_value.ComputeKardex()
        location_ids = wizard.location_ids #self.env['stock.location'].search([('usage','=','internal')])
        product_ids = wizard.product_ids.sorted(lambda p: p.name) #self.env['product.product'].search([('id','in', wizard.product_ids)])
        for location in location_ids:
            for product in product_ids:
                list_data = ck.create_kardex_dict(product.id, wizard.locked_period, location.id, wizard.end_date.strftime('%Y-%m-%d 23:59:59'), self.env, self.env.company)
                if not list_data:
                    continue
                if x > 0:
                    x += 3
                # Encabezado
                worksheet.merge_range(x+0,0,x+0,20,'FORMATO 13.1: "REGISTRO DE INVENTARIO PERMANENTE VALORIZADO - DETALLE DEL INVENTARIO VALORIZADO"',especial1)
                if str(wizard.initial_date)[5:7] == str(wizard.end_date)[5:7]:
                    period = str(wizard.initial_date)[5:7] + '-' + str(wizard.initial_date)[:4]
                else:
                    period = str(wizard.initial_date)[5:7] + '-' + str(wizard.initial_date)[:4] + ' al ' + str(wizard.end_date)[:4] + '-' + str(wizard.end_date)[5:7]
                worksheet.write(x+2,0,'PERIODO: ' + period,bold)
                worksheet.write(x+3,0,'RUC: ' + self.env.user.company_id.partner_id.vat if self.env.user.company_id.partner_id.vat else 'Vat number not configured in company.',bold)
                worksheet.write(x+4,0,'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: ' + self.env.user.company_id.partner_id.name,bold)
                worksheet.write(x+5,0,'ESTABLECIMIENTO (1): ' + location.name) #+ wh_names if self.alllocations == False else 'ESTABLECIMIENTO (1): TODOS',bold)
                worksheet.write(x+6,0,'CÓDIGO DE LA EXISTENCIA: ' + product.default_code if product.default_code else 'CÓDIGO DE LA EXISTENCIA: Sin código de producto',bold)
                worksheet.write(x+7,0,'TIPO (TABLA 5): ' + product.categ_id.existence_type_id.name if product.categ_id.existence_type_id else 'No tiene tipo de existencia en la categoría',bold)
                worksheet.write(x+8,0,'DESCRIPCIÓN: ' + product.name,bold)
                worksheet.write(x+9,0,'CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): ' + product.uom_id.sunat_code if product.uom_id.sunat_code else 'CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): ' + product.uom_id.name, bold) #'El producto no tiene unidad de medida de kardex',bold)
                worksheet.write(x+10,0,'MÉTODO DE VALUACIÓN: ' + dict(product.categ_id._fields['property_cost_method']._description_selection(self.env)).get(product.categ_id.property_cost_method),bold)
                worksheet.merge_range(x+13,0,x+14,3, u"DOCUMENTO DE TRASLADO, COMPROBANTE DE PAGO, DOCUMENTO INTERNO O SIMILAR",boldbord)
                worksheet.write(x+15,0, u"FECHA",boldbord)
                worksheet.write(x+15,1, u"TIPO (TABLA 10)",boldbord)
                worksheet.write(x+15,2, u"SERIE",boldbord)
                worksheet.write(x+15,3, u"NUMERO",boldbord)
                worksheet.merge_range(x+13,4,x+15,4, u"TIPO DE OPERACIÓN (TABLA 12)",boldbord)
                worksheet.merge_range(x+13,5,x+13,7, "ENTRADAS",boldbord)
                worksheet.merge_range(x+14,5,x+15,5, "CANTIDAD",boldbord)
                worksheet.merge_range(x+14,6,x+15,6, "COSTO UNITARIO",boldbord)
                worksheet.merge_range(x+14,7,x+15,7, "COSTO TOTAL",boldbord)
                worksheet.merge_range(x+13,8,x+13,10, "SALIDAS",boldbord)
                worksheet.merge_range(x+14,8,x+15,8, "CANTIDAD",boldbord)
                worksheet.merge_range(x+14,9,x+15,9, "COSTO UNITARIO",boldbord)
                worksheet.merge_range(x+14,10,x+15,10, "COSTO TOTAL",boldbord)
                worksheet.merge_range(x+13,11,x+13,13, "SALDO FINAL",boldbord)
                worksheet.merge_range(x+14,11,x+15,11, "CANTIDAD",boldbord)
                worksheet.merge_range(x+14,12,x+15,12, "COSTO UNITARIO",boldbord)
                worksheet.merge_range(x+14,13,x+15,13, "COSTO TOTAL",boldbord)

                x += 16
                
                total = 0

                for item in list_data:

                    total += item['in_qty'] - item['out_qty']
                    total = round(total, 4)
                    
                    worksheet.write(x, 0, item['date'], bord if total >= 0 else bord_red)
                    worksheet.write(x, 1, item['type_document'], bord if total >= 0 else bord_red)
                    worksheet.write(x, 2, item['serie'], bord if total >= 0 else bord_red)
                    worksheet.write(x, 3, item['number'], (bord if total >= 0 else bord2_red) if item['number'][:13] != _('Initial Balance') else bord2)
                    worksheet.write(x, 4, item['type_operation'], bord if total >= 0 else bord_red)
                    worksheet.write(x, 5, item['in_qty'], numberdos if total >= 0 else numberdos_red)
                    worksheet.write(x, 6, float_round(item['in_cost'], 8), numberocho if total >= 0 and (item['in_cost'] > 0 and item['in_qty'] > 0 or item['out_qty'] > 0) else numberocho_red)
                    worksheet.write(x, 8, item['out_qty'], numberdos if total >= 0 else numberdos_red)
                    # worksheet.write(x, 9, float_round(item['out_cost'], 8), numberocho if total >= 0 else numberocho_red)
                    if item['out_qty'] > 0:
                        worksheet.write_formula('J' + str(x+1), '=M' + str(x), numberocho if total >= 0 else numberocho_red)
                    else:
                        worksheet.write(x, 9, 0, numberdos if total >= 0 else numberdos_red)
                    worksheet.write_formula('H' + str(x+1), '=F' + str(x+1) + ' * G' + str(x+1), numberdos if total >= 0 else numberdos_red)
                    worksheet.write_formula('K' + str(x+1), '=I' + str(x+1) + ' * J' + str(x+1), numberdos if total >= 0 else numberdos_red)
                    if x == 16:
                        worksheet.write_formula('L' + str(x+1), '=F' + str(x+1) + ' - I' + str(x+1), numberdos if total >= 0 else numberdos_red)
                        worksheet.write_formula('N' + str(x+1), '=H' + str(x+1) + ' - K' + str(x+1), numberdos if total >= 0 else numberdos_red)
                    else:
                        worksheet.write_formula('L' + str(x+1), '=F' + str(x+1) + ' - I' + str(x+1) + ' + L' + str(x), numberdos if total >= 0 else numberdos_red)
                        worksheet.write_formula('N' + str(x+1), '=H' + str(x+1) + ' - K' + str(x+1) + ' + N' + str(x), numberdos if total >= 0 else numberdos_red)
                    if total != 0:
                        worksheet.write_formula('M' + str(x+1), '=N' + str(x+1) + ' / L' + str(x+1), numberocho if total >= 0 else numberocho_red)
                    else:
                        worksheet.write_formula('M' + str(x+1), '=0', numberocho if total >= 0 else numberocho_red)

                    x += 1
