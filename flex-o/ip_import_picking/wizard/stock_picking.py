# -*- coding: utf-8 -*-
import binascii
import logging
import tempfile
import xlrd
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    from io import StringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')

class ImportStockPicking(models.TransientModel):
    _name = "import.stock.picking"
    _description = "Import Stock Picking"

    file = fields.Binary(string="File", required=True)
    import_file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select', default='csv')
    picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type', required=True)
    location_id = fields.Many2one('stock.location', "Source Location", required=True,)
    location_dest_id = fields.Many2one('stock.location', "Destination Location", required=True)
    import_option = fields.Selection([
        ('name', 'Name'),
        ('barcode', 'Barcode'),
        ('code', 'Internal Reference'),
        ], default='name', string='Import By ')

    @api.onchange('picking_type_id')
    def onchange_picking_type_id(self):
        res = {}
        if self.picking_type_id:
            self.location_id = self.picking_type_id.default_location_src_id.id
            self.location_dest_id = self.picking_type_id.default_location_dest_id.id
        return res

    def create_stock_picking(self, values):
        pickingObj = self.env['stock.picking']
        picking_id = pickingObj.search([('name', '=', values.get('name'))])
        if picking_id:
            if picking_id.partner_id.name == values.get('partner_id'):
                lines = self.import_stock_picking_line(values, picking_id)
                return lines
            else:
                raise Warning(_('Customer name is different for "%s" .\n Please define same.') % values.get('name'))
        else:
            partner_id = self.check_partner(values.get('partner_id'))
            picking_id = pickingObj.create({
                'name': values.get('name'),
                'partner_id': partner_id.id,
                'origin': values.get('origin'),
                'picking_type_id': self.picking_type_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
            })
            return self.import_stock_picking_line(values, picking_id)

    def import_stock_picking_line(self, values, picking_id):
        ProductObj = self.env['product.product']
        product_uom = self.env['uom.uom'].search([('name', '=', values.get('uom'))])
        if not product_uom:
            raise Warning(_(' "%s" Product UOM category is not available.') % values.get('uom'))
        if self.import_option == 'name':
            product_id = ProductObj.search([('name', '=', values.get('product_id'))])
        elif self.import_option == 'barcode':
            product_id = ProductObj.search([('barcode', '=', values.get('product_id'))])
        else:
            product_id = ProductObj.search([('default_code', '=', values.get('product_id'))])
        if not product_id:
            raise Warning(_(' Product "%s" not available. Please check for the same in sheet.') % (values.get('product_id')))
        for product in product_id:
            return self.env['stock.move'].create({
                'product_id': product.id,
                'name': values.get('description'),
                'product_uom': product_uom.id,
                'product_uom_qty': values.get('product_uom_qty'),
                'picking_type_id': self.picking_type_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'picking_id': picking_id.id,
                'price_unit_it': values.get('price_unit_it'),

            })

    def check_partner(self, name):
        partner_id = self.env['res.partner'].search([('name', '=', name)])
        if not partner_id:
            raise Warning(_(' "%s" Customer are not available.') % name)
        return partner_id

    def ship_picking_date(self, date):
        return datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)

    def import_stock_picking(self):
        if self.import_file_option == 'csv':
            keys = ['name', 'partner_id', 'origin', 'product_id', 'description', 'product_uom_qty', 'uom', 'date', 'price_unit_it']
            data = base64.b64decode(self.file)
            file_input = StringIO(data.decode("utf-8"))
            file_input.seek(0)
            reader_info = []
            reader = csv.reader(file_input, delimiter=',')
            try:
                reader_info.extend(reader)
            except Exception:
                raise Warning(_("Not a valid file!"))
            values = {}
            for i in range(len(reader_info)):
                field = map(str, reader_info[i])
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        res = self.create_stock_picking(values)
        else:
            fx = tempfile.NamedTemporaryFile(suffix=".xlsx")
            fx.write(binascii.a2b_base64(self.file))
            fx.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fx.name)
            sheet = workbook.sheet_by_index(0)
            for row_no in range(sheet.nrows):
                if row_no <= 0:
                    field = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    picking_line = list(map(lambda row: str(row.value), sheet.row(row_no)))
                    datetime_xlt = datetime(*xlrd.xldate_as_tuple(int(float(picking_line[7])), workbook.datemode))
                    string_dt = datetime_xlt.date().strftime('%Y-%m-%d')
                    values.update({
                        'name': picking_line[0],
                        'partner_id': picking_line[1],
                        'origin': picking_line[2],
                        'product_id': picking_line[3],
                        'description': picking_line[4],
                        'product_uom_qty': picking_line[5],
                        'uom': picking_line[6],
                        'date': string_dt,
                        'price_unit_it': picking_line[8],
                    })
                    res = self.create_stock_picking(values)
        return res
