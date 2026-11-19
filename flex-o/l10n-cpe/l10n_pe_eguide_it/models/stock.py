# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Picking(models.Model):
    _inherit = "stock.picking"

    def action_generate_eguide(self):
        res = super(Picking, self).action_generate_eguide()
        self.numberg = self.pe_guide_number
        return res

    @api.onchange('type_of_transport', 'carrier_id_it', 'vehicle_id', 'driver_id')
    def _onchange_type_of_transport(self):
        if self.type_of_transport and self.carrier_id_it and self.driver_id:
            if self.type_of_transport == '01':
                self.pe_carrier_id = self.carrier_id_it
            if self.type_of_transport == '02':
                self.pe_fleet_ids = [(0, 0, {'name': self.vehicle_id.license_plate, 'fleet_id': self.vehicle_id.id,'driver_id': self.driver_id.id})]
            self.pe_transport_mode = self.type_of_transport