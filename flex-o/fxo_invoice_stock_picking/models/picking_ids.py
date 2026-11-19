from odoo import api, models, fields


class picking_ids(models.Model):

    _inherit = 'account.move'

    picking_ids = fields.One2many('stock.picking', compute='_get_picking_ids', store=False, string='Invoice associated to picking')

    def _get_picking_ids(self):
        for item in self:
            item.picking_ids += self.env['stock.picking'].search([
                ('invoice_id', '=', item.id), ('state', '=', 'done')
            ])
