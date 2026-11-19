# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"

    purchase_discount_product_id = fields.Many2one('product.product', string='Purchase Discount Product')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_discount_product_id = fields.Many2one('product.product', string='Purchase Discount Product')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            purchase_discount_product_id=self.env.user.company_id.purchase_discount_product_id and self.env.user.company_id.purchase_discount_product_id.id or False,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if not self.env.user._is_admin():
            raise AccessError(_("Only administrators can change the settings"))

        self.env.user.company_id.purchase_discount_product_id = self.purchase_discount_product_id.id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: