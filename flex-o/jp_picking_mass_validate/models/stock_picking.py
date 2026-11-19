# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_confirm_mass(self):
        if any(p.state not in ('draft','confirmed') for p in self):
            raise UserError(_('You can only validate draft and confirmed pickings.'))
        for picking in self:
            # If still in draft => confirm and assign
            if picking.state in ('draft','confirmed'):
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty

    def button_validate_mass(self):
        if any(p.state != 'assigned' for p in self):
            raise UserError(_('You can only validate assigned pickings.'))
        for picking in self:
            picking.action_done()
    
    def do_unreserve_mass(self):        
        active_ids = self.env.context.get('active_ids', [])
        pickings = self.env['stock.picking'].search([('id','in',active_ids)])
        for picking in pickings:
            picking.move_lines._do_unreserve()
            picking.package_level_ids.filtered(lambda p: not p.move_ids).unlink()