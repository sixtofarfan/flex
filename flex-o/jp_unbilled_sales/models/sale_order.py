from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    unbilled_sale = fields.Boolean(string='Unbilled Sales', compute='_get_is_unbilled_sale', store=True, default=True)
    undelivered_sale = fields.Boolean(string='Undelivered sales', compute='_get_is_undelivered_sale', store=True, default=True,)

    @api.depends('order_line.product_uom_qty','order_line.qty_invoiced')
    def _get_is_unbilled_sale(self):
        for sale in self:
            for line in sale.order_line:
                if line.product_uom_qty > line.qty_invoiced:
                    sale.unbilled_sale = True
                else:
                    sale.unbilled_sale = False
    
    @api.depends('order_line.product_uom_qty', 'order_line.qty_delivered')
    def _get_is_undelivered_sale(self):
        for sale in self:
            for line in sale.order_line:
                if line.product_uom_qty > line.qty_delivered:
                    sale.undelivered_sale = True
                else:
                    sale.undelivered_sale = False
