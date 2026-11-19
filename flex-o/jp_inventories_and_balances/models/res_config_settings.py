# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
  
    table_34_sector_id = fields.Many2one(comodel_name='table.34.sector', string=_('PLE Inventories and Balances Sector'), related='company_id.table_34_sector_id', readonly=False)
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        table_34_sector_id = int(params.get_param('jp_inventories_and_balances.table_34_sector_id'))
        res.update(
            table_34_sector_id = table_34_sector_id,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "jp_inventories_and_balances.table_34_sector_id",
            self.table_34_sector_id.id)