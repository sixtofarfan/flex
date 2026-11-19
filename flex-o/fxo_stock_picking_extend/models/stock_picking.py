# -*- coding: utf-8 -*-

from odoo import api, fields, models

class Stock_Picking(models.Model):
    _inherit = 'stock.picking'

    marca = fields.Char('Marca')
    placa = fields.Char('Placa')
    nro_const = fields.Char('Numero de constancia de inscripcion', size=12)
    licencia = fields.Char('Licencia de Conducir N°(5)', size=12)
    nombre = fields.Char('Nombre')
    ruc = fields.Char('Ruc', size=100)
    tipo = fields.Char('Tipo', size=12)
    nro_comp = fields.Char('Numero de comprobante', size=12)
    nro_guia = fields.Char('Numero de guia', size=12)
    fecha_traslado = fields.Datetime(string='Fecha de traslado')

    punto_partida = fields.Char('Punto de partida', size=100)
    punto_llegada = fields.Char('Punto de llegada', size=100)

    # Nuevos campos para escojer puntos de partida y llegada
    punto_partida_id = fields.Many2one('res.partner', string='Punto de partida')
    punto_llegada_id = fields.Many2one('res.partner', string='Punto de llegada')

    # Pestaña Personalización Peruana
    fleete_id = fields.Many2one(comodel_name='fleet.vehicle', string='Unidad')
    driver_id = fields.Many2one(comodel_name='res.partner', string='Conductor')
    pe_carrier_id = fields.Many2one(comodel_name="res.partner", string="Transportista")
    commitment_date = fields.Datetime(related='sale_id.commitment_date')


    # @api.model
    # def _get_pe_transport_mode(self):
    #     return self.env['pe.datas'].get_selection("PE.CPE.CATALOG18")

    @api.depends('numberg')
    def refres_numg(self):
        if self.state == 'done':
            return
        self.numberg = False
        if self.state not in ['done', 'cancel']:
            if self.picking_type_id.code == 'internal' or self.picking_type_id.code == 'outgoing':
                if self.serie_guia:
                    res = self.makecurrentsequecenumber(self.serie_guia)
                    # self.pe_guide_number = res[0]
                    # self.pe_number = res[0]
                    self.numberg = res[0]

    @api.depends('numberg')
    @api.onchange('picking_type_id')
    def _picking_type_change(self):
        self.numberg = False
        if self.picking_type_id.code == 'internal' or self.picking_type_id.code == 'outgoing':
            if self.picking_type_id.seria_guia:
                if not self.serie_guia:
                    self.serie_guia = self.picking_type_id.seria_guia
                    res = self.makecurrentsequecenumber(self.serie_guia)
                    # self.pe_guide_number = res[0]
                    # self.pe_number = res[0]
                    self.numberg = res[0]

    @api.onchange('punto_partida_id')
    def _punto_partida_id_change(self):
        self.punto_partida = self.punto_partida_id.street

    @api.onchange('punto_llegada_id')
    def _punto_llegada_id_change(self):
        self.punto_llegada = self.punto_llegada_id.street

    # @api.depends('pe_guide_number')
    # @api.onchange('serie_guia')
    # def _serie_guia_change(self):
    #     self.pe_is_eguide = self.serie_guia.pe_is_eguide

    @api.onchange('pe_carrier_id')
    def pe_carrier_id_change(self):
        if self.state == 'done':
            return
        self.nombre = self.pe_carrier_id.name if self.pe_carrier_id.name else False
        self.ruc = self.pe_carrier_id.vat if self.pe_carrier_id.vat else False

    @api.onchange('fleete_id')
    def fleete_id_change(self):
        if self.state == 'done':
            return
        self.marca = self.fleete_id.model_id.brand_id.name + '/' + self.fleete_id.model_id.name if self.fleete_id.model_id.brand_id.name or self.fleete_id.model_id.name else False
        self.placa = self.fleete_id.license_plate if self.fleete_id.license_plate else False
        self.driver_id = self.fleete_id.driver_id if self.fleete_id.driver_id else False

    @api.onchange('driver_id')
    def driver_id_change(self):
        if self.state == 'done':
            return
        self.licencia = self.driver_id.pe_driver_license if self.driver_id.pe_driver_license else False

    def calc_state_invoice(self):
        if self.invoice_id:
            dic_state = {'draft': 'Borrador', 'proforma': 'Pro-forma', 'proforma2': 'Pro-forma', 'open': 'Abierto',
                            'paid': 'Pagado', 'cancel': 'Cancelado','annul': 'Anulado'}
            self.state_invoice = dic_state[self.invoice_id.state]
        else:
            self.state_invoice = ''

    @api.model
    def create(self, vals):
        t = super(Stock_Picking, self).create(vals)
        if t.picking_type_id.warehouse_id.id and t.picking_type_id.warehouse_id.partner_id.id and t.picking_type_id.warehouse_id.partner_id.street:
            t.punto_partida = t.picking_type_id.warehouse_id.partner_id.street
            t.punto_partida_id = t.picking_type_id.warehouse_id.partner_id.id
        p = self.env['sale.order'].search([('name','=',vals['origin'])])
        if p.partner_shipping_id:
            t.punto_llegada = p.partner_shipping_id.street
            t.punto_llegada_id = p.partner_shipping_id
        elif t.partner_id.id and t.partner_id.street:
            t.punto_llegada = t.partner_id.street
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            t.punto_llegada_id = addr['delivery']
        return t