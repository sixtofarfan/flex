# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ 
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for picking in self:
            if picking.picking_type_id.code == 'outgoing':
                for line in picking.move_line_ids_without_package:
                    if picking.serie_guia and line.location_id.serie_guia_id and line.location_id.serie_guia_id != picking.serie_guia:
                        raise UserError(_('The guide serie %s selected does not correspond to the location %s in product %s. Please check the location guide serie and try again.') %(picking.serie_guia.name,line.location_id.name,line.product_id.name))
        return res
    
    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        for picking in self:
            if picking.picking_type_id.code == 'outgoing':
                for line in picking.move_line_ids_without_package:
                    if picking.serie_guia and line.location_id.serie_guia_id and line.location_id.serie_guia_id != picking.serie_guia:
                        raise UserError(_('The guide serie %s selected does not correspond to the location %s in product %s. Please check the location guide serie and try again.') %(picking.serie_guia.name,line.location_id.name,line.product_id.name))
        return res