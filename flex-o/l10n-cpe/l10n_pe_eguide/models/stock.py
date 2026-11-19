# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from pdf417gen.encoding import to_bytes, encode_high, encode_rows
from pdf417gen.util import chunks
from pdf417gen.compaction import compact_bytes
from pdf417gen import render_image
import tempfile
from base64 import encodestring
from odoo.exceptions import UserError
import re
from io import StringIO, BytesIO

try:
    import qrcode

    qr_mod = True
except:
    qr_mod = False


class Picking(models.Model):
    _inherit = "stock.picking"

    pe_voided_id = fields.Many2one("pe.eguide", "Guide canceled", copy=False)
    pe_guide_id = fields.Many2one("pe.eguide", "Guide Electronic", copy=False)
    pe_guide_number = fields.Char("Guide Number", default="/", copy=False)
    pe_is_realeted = fields.Boolean("Is Related", copy=False)
    pe_related_number = fields.Char("Related Number", copy=False)
    pe_related_code = fields.Selection(
        selection="_get_pe_related_code", string="Related Number Code", copy=False)
    supplier_id = fields.Many2one(
        comodel_name="res.partner", string="Supplier", copy=False)
    pe_transfer_code = fields.Selection(
        selection="_get_pe_transfer_code", string="Transfer code", default="01", copy=False)
    pe_gross_weight = fields.Float(
        "Gross Weigh", digits='Product Unit of Measure', copy=False)
    pe_unit_quantity = fields.Integer("Unit Quantity", copy=False)
    pe_transport_mode = fields.Selection(
        selection="_get_pe_transport_mode", string="Transport Mode", copy=False)
    pe_carrier_id = fields.Many2one(
        comodel_name="res.partner", string="Carrier", copy=False)
    pe_is_eguide = fields.Boolean("Is EGuide", copy=False)
    pe_is_programmed = fields.Boolean("Transfer Programmed", copy=False)
    pe_date_issue = fields.Date('Date Issue', copy=False)
    pe_fleet_ids = fields.One2many(
        comodel_name="pe.stock.fleet", inverse_name="picking_id", string="Fleet Private", copy=False)

    pe_digest = fields.Char("Digest", related="pe_guide_id.digest")
    pe_signature = fields.Text("Signature", related="pe_guide_id.signature")
    pe_response = fields.Char("Response", related="pe_guide_id.response")
    pe_note = fields.Text("Sunat Note", related="pe_guide_id.note")
    pe_error_code = fields.Selection(
        "_get_pe_error_code", string="Error Code", related="pe_guide_id.error_code", readonly=True)
    sunat_pdf417_code = fields.Binary(
        "Pdf 417 Code", compute="_get_pdf417_code")
    sunat_qr_code = fields.Binary("QR Code", compute="_compute_get_qr_code")
    pe_guide_state = fields.Selection([
        ('draft', 'Draft'),
        ('generate', 'Generated'),
        ('send', 'Send'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Guide Status', related="pe_guide_id.state")
    uom_gross_weight = fields.Selection([('KGM', 'KGM'), ('TNE', 'TNE')], string='Unidad de medida del Peso Bruto')
    punto_partida_id = fields.Many2one('res.partner', string='Punto de partida')
    partida_state_id = fields.Many2one('res.country.state', string='Departamento')
    partida_province_id = fields.Many2one('res.country.state', string='Provincia')
    partida_district_id = fields.Many2one('res.country.state', string='Distrito')
    partida_country_id = fields.Many2one('res.country', string='País')
    partida_establishment_code = fields.Char(string='Código de establecimiento', default='0000')

    punto_llegada_id = fields.Many2one('res.partner', string='Punto de llegada')
    llegada_state_id = fields.Many2one('res.country.state', string='Departamento')
    llegada_province_id = fields.Many2one('res.country.state', string='Provincia')
    llegada_district_id = fields.Many2one('res.country.state', string='Distrito')
    llegada_country_id = fields.Many2one('res.country', string='País')
    llegada_establishment_code = fields.Char(string='Código de establecimiento', default='0000')

    license_plate = fields.Char(string='Matrícula')
    number_driver_licence = fields.Char(string=u'Lic. de Conducir', size=20)

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        for i in self:
            if i.picking_type_id.warehouse_id.partner_id:
                i.punto_partida_id = i.picking_type_id.warehouse_id.partner_id.id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for i in self:
            if i.partner_id:
                i.punto_llegada_id = i.partner_id.id

    @api.onchange('punto_partida_id')
    def _punto_partida_id_change(self):
        self.punto_partida = self.punto_partida_id.street
        self.starting_point = self.punto_partida_id.street
        self.partida_state_id = self.punto_partida_id.state_id.id
        self.partida_province_id = self.punto_partida_id.province_id.id
        self.partida_district_id = self.punto_partida_id.district_id.id
        self.partida_country_id = self.punto_partida_id.country_id.id

    @api.onchange('punto_llegada_id')
    def _punto_llegada_id_change(self):
        self.punto_llegada = self.punto_llegada_id.street
        self.ending_point = self.punto_llegada_id.street
        self.llegada_state_id = self.punto_llegada_id.state_id.id
        self.llegada_province_id = self.punto_llegada_id.province_id.id
        self.llegada_district_id = self.punto_llegada_id.district_id.id
        self.llegada_country_id = self.punto_llegada_id.country_id.id

    @api.onchange('picking_type_id')
    def _onchange_partida_establishment_code(self):
        if self.picking_type_id.sequence_code == 'OUT':
            self.partida_establishment_code = self.picking_type_id.warehouse_id.establishment_code

    @api.onchange('picking_type_id')
    def _onchange_llegada_establishment_code(self):
        if self.picking_type_id.sequence_code == 'IN':
            self.llegada_establishment_code = self.picking_type_id.warehouse_id.establishment_code

    @api.onchange('vehicle_id')
    def _onchange_vehicle(self):
        for i in self:
            if i.vehicle_id:
                i.driver_id = i.vehicle_id.driver_id.id
                i.license_plate = i.vehicle_id.license_plate

    @api.onchange('driver_id')
    def _onchange_driver_id_number_driver_licence(self):
        for i in self:
            if i.driver_id:
                i.number_driver_licence = i.driver_id.number_driver_licence

    @api.model
    def create(self, vals):
        if 'picking_type_id' in vals:
            pt = self.env['stock.picking.type'].search([('id', '=', vals['picking_type_id'])])
            if pt.warehouse_id.partner_id:
                vals['punto_partida_id'] = pt.warehouse_id.partner_id.id
        if 'partner_id' in vals:
            rp = self.env['res.partner'].search([('id', '=', vals['partner_id'])])
            if rp:
                vals['punto_llegada_id'] = rp.id
        res = super(Picking, self).create(vals)
        res._punto_partida_id_change()
        res._punto_llegada_id_change()
        res._onchange_partida_establishment_code()
        res._onchange_llegada_establishment_code()
        res._onchange_vehicle()
        res._onchange_driver_id_number_driver_licence()
        return res

    @api.model
    def action_cancel_eguide(self):
        for picking_id in self:
            if picking_id.pe_guide_id and picking_id.pe_guide_id.state not in ["draft", "generate", "cancel"]:
                voided_id = self.env['pe.eguide'].get_eguide_async(
                    'low', picking_id)
                picking_id.pe_voided_id = voided_id.id

    @api.model
    def _get_pdf417_code(self):
        for picking_id in self:
            res = []
            if picking_id.pe_guide_number and picking_id.pe_is_eguide:
                res.append(picking_id.company_id.partner_id.vat)
                res.append('09')
                res.append(picking_id.pe_guide_number.split("-")[0] or '')
                res.append(picking_id.pe_guide_number.split("-")[1] or '')
                # res.append(str(picking_id.amount_tax))
                # res.append(str(picking_id.amount_total))
                res.append(str(picking_id.pe_date_issue))
                res.append(picking_id.partner_id.l10n_latam_identification_type_id.name or "-")
                res.append(picking_id.partner_id.vat or "-")
                res.append(picking_id.pe_digest or "")
                res.append(picking_id.pe_signature or "")
                res.append("")
                pdf417_string = '|'.join(res)
                data_bytes = compact_bytes(to_bytes(pdf417_string, 'utf-8'))
                code_words = encode_high(data_bytes, 10, 5)
                rows = list(chunks(code_words, 10))
                codes = list(encode_rows(rows, 10, 5))

                image = render_image(codes, scale=2, ratio=2, padding=7)
                tmpf = BytesIO()
                image.save(tmpf, 'png')
                # tmpf.seek(0)
                picking_id.sunat_pdf417_code = encodestring(tmpf.getvalue())

    def _compute_get_qr_code(self):
        for picking_id in self:
            res = []
            if picking_id.pe_guide_number and picking_id.pe_is_eguide:
                res = [
                    picking_id.company_id.vat or "-",
                    "9",
                    picking_id.pe_guide_number.split("-")[0] or '',
                    picking_id.pe_guide_number.split("-")[1] or '',
                    "0",
                    "0",
                    str(picking_id.pe_date_issue),
                    picking_id.partner_id.vat or "-",
                    picking_id.pe_digest or "",
                ]

                qr_string = '|'.join(res)
                qr = qrcode.QRCode(
                    version=1, error_correction=qrcode.constants.ERROR_CORRECT_Q)
                qr.add_data(qr_string)
                qr.make(fit=True)
                image = qr.make_image()
                tmpf = BytesIO()
                image.save(tmpf, 'png')
                picking_id.sunat_qr_code = encodestring(tmpf.getvalue())

    @api.model
    def _get_pe_error_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.ERROR")

    @api.model
    def do_new_transfer(self):
        res = super(Picking, self).do_new_transfer()
        self.pe_gross_weight = sum(
            [line.product_id.weight for line in self.pack_operation_ids])
        self.pe_unit_quantity = sum(
            [line.qty_done or line.product_qty for line in self.pack_operation_ids])
        return res

    @api.model
    def _get_pe_transport_mode(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG18")

    @api.model
    def _get_pe_related_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG21")

    @api.model
    def _get_pe_transfer_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG20")

    @api.model
    def validate_eguide(self):
        if not self.partner_id:
            raise UserError(_("Customer is required"))
        if self.partner_id.id == self.company_id.partner_id.id:
            raise UserError("Destinatario no debe ser igual al remitente")
        if not self.partner_id.parent_id.l10n_latam_identification_type_id and not self.partner_id.l10n_latam_identification_type_id:
            raise UserError(_("Customer type document is required"))
        if not self.partner_id.parent_id.vat and not self.partner_id.vat:
            raise UserError(_("Customer number document is required"))
        if not self.partner_id.street:
            raise UserError(_("Customer street is required for %s") %
                            (self.partner_id.name or ""))
        # if not self.partner_id.l10n_pe_district:
        if not self.partner_id.district_id:
            raise UserError(_("Customer district is required for %s") %
                            (self.partner_id.name or ""))

        if not self.pe_carrier_id.l10n_latam_identification_type_id and self.pe_transport_mode == "01":
            raise UserError(_("Carrier type document is required for %s") % (
                    self.pe_carrier_id.name or ""))
        # if not self.pe_carrier_id.vat and self.pe_transport_mode == "01":
        if not self.driver_id.vat:
            raise UserError(_("Carrier number document is required for %s") % (
                    self.driver_id.name or ""))
        if not self.picking_type_id.warehouse_id.partner_id or not self.picking_type_id.warehouse_id.partner_id.street:
            raise UserError(_("It is necessary to enter the warehouse address for %s") % (
                    self.picking_type_id.warehouse_id.partner_id.name or ""))
        if self.picking_type_id.warehouse_id.partner_id and not self.picking_type_id.warehouse_id.partner_id.district_id:
            raise UserError(_("It is necessary to enter the warehouse district for %s") % (
                    self.picking_type_id.warehouse_id.partner_id.name or ""))
        # if self.pe_transport_mode == "02" and len(self.pe_fleet_ids) > 0:
        # SFR
        # for line in self.pe_fleet_ids:
        # if not line.driver_id.l10n_latam_identification_type_id:
        #    raise UserError(_("Carrier type document is required for %s") % (
        #        line.driver_id.name or ""))
        # if not line.driver_id.vat:
        #    raise UserError(_("Carrier number document is required for %s") % (
        #        line.driver_id.name or ""))
        # elif self.pe_transport_mode == "02" and len(self.pe_fleet_ids) == 0:
        #    raise UserError(_("It is necessary to add a vehicle and driver"))

    def action_generate_eguide(self):
        for stock in self:
            if stock.pe_is_eguide:
                self.validate_eguide()
                self.pe_date_issue = fields.Date.context_today(self)
                if stock.pe_guide_number == '/':
                    if stock.picking_type_id.warehouse_id.eguide_sequence_id:
                        stock.pe_guide_number = stock.picking_type_id.warehouse_id.eguide_sequence_id.next_by_id()
                    else:
                        stock.pe_guide_number = self.env['ir.sequence'].next_by_code(
                            'pe.eguide.sync')
                if not re.match(r'^(T){1}[A-Z0-9]{3}\-\d+$', stock.pe_guide_number):
                    raise UserError("El numero de la guia ingresada no cumple con el estandar.\n"
                                    "Verificar la secuencia del Diario por jemplo T001- o TG01-. \n"
                                    "Para cambiar ir a Configuracion/Gestion de Almacenes/Almacenes")
                if not self.pe_guide_id:
                    pe_guide_id = self.env['pe.eguide'].create_from_stock(
                        stock)
                    stock.pe_guide_id = pe_guide_id.id
                else:
                    pe_guide_id = stock.pe_guide_id
                if stock.company_id.pe_is_sync:
                    pe_guide_id.generate_eguide()
                    pe_guide_id.action_send()
                    pe_guide_id.send_eguide_apirest()
                else:
                    pe_guide_id.generate_eguide()
                self.pe_number = stock.pe_guide_number
                self.numberg = stock.pe_guide_number
                self.pe_response = pe_guide_id.response
                self.pe_note = 'Ticket:' + pe_guide_id.ticket + ', Fecha recepción:' + str(
                    pe_guide_id.gre_reception_date)


class PeStockFleet(models.Model):
    _name = "pe.stock.fleet"
    _description = 'Stock Fleet'

    name = fields.Char("License Plate", required=True)
    fleet_id = fields.Many2one(comodel_name="fleet.vehicle", string="Vehicle")
    picking_id = fields.Many2one(
        comodel_name="stock.picking", string="Picking")
    driver_id = fields.Many2one(
        comodel_name="res.partner", string="Driver", required=True)
    is_main = fields.Boolean("Main")

    @api.onchange("fleet_id")
    def onchange_fleet_id(self):
        if self.fleet_id:
            self.name = self.fleet_id.license_plate
            self.driver_id = self.fleet_id.driver_id.id


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    eguide_sequence_id = fields.Many2one('ir.sequence', 'Eguide Sequence', )
    establishment_code = fields.Char(string='Código de establecimiento', default='0000')


class StockMove(models.Model):
    _inherit = 'stock.move'

    reason_transfer = fields.Many2one(related='picking_id.reason_transfer', string=u'Motivo de Traslado', store=True)
    reason_transfer_code = fields.Char(related='reason_transfer.code', string=u'Código', store=True)
    indicator_dam = fields.Char(string='DAM')
