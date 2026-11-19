# -*- encoding: utf-8 -*-

from odoo import models, fields, api , exceptions


class sale_order(models.Model):
    _inherit = 'sale.order'

    partner_order_id = fields.Many2one('res.partner', 'Contacto', domain=[('is_company', '=', False)])

    @api.onchange('partner_id')
    def onchange_partner_id_(self):
        if self.partner_id:
            if self.partner_id.child_ids:
                self.partner_order_id = self.partner_id.child_ids[0].id
