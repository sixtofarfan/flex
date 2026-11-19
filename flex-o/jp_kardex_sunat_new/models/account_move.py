from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    # picking_ids = fields.Many2many('stock.picking','Pickings')
    picking_ids = fields.One2many('stock.picking', 'invoice_id', string='Pickings')
    sale_order_ids = fields.Many2many('sale.order', string='Origin Sale Orders', compute='_get_sale_order_from_lines')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search(['|',('ref', '=', name),('name','=',name)] + args, limit=limit)
        if not recs:
            recs = self.search(['|',('ref', operator, name),('name',operator,name)] + args, limit=limit)
        return recs.name_get()

    def _get_sale_order_from_lines(self):
        sale_order_ids = self.env['sale.order']
        for invoice in self:
            for line in invoice.invoice_line_ids:
                for sale_line in line.sale_line_ids:
                    sale_order_ids += sale_line.order_id
        self.sale_order_ids = sale_order_ids

    def button_annul(self):
        res = super(AccountMove, self).button_annul()
        self.picking_ids = False
        return res

    @api.onchange('picking_ids','transit_move_line_id')
    def _onchange_picking_ids(self):
        if self.vendor_landed_cost_id:
            raise UserError(_('You can\'t change the transit move because this invoice is in landed cost %s') %self.vendor_landed_cost_id.name)
        else:
            self.vendor_landed_cost_id._onchange_vendor_bill_ids()
        for picking in self.picking_ids:
            picking.invoice_id = self
            # picking._onchange_invoice_id()
            sm = self.env['stock.move'].search([('picking_id','=', picking.ids)])
            am = self
            if picking.invoice_id:
                for move in sm:
                    aml = self.env['account.move.line'].search([('move_id','=', self.ids),('product_id','=', move.product_id.id),('price_unit','>',0)])
                    svl = self.env['stock.valuation.layer'].search([('stock_move_id','=',move.id),('stock_landed_cost_id','=', False),('quantity','>',0)]).sorted(lambda l: l.create_date, reverse=True)
                    if svl:
                        svl = svl[0]
                    if aml:
                        aml = aml[0]
                    svl = self.env['stock.valuation.layer'].search([('stock_move_id','=',move.id),('stock_landed_cost_id','=', False),('quantity','>',0)])
                    if am.currency_id != self.env.user.company_id.currency_id:
                        if am.tc_per:
                            svl.unit_cost = aml.price_unit * am.currency_rate if not am.transit_move_line_id else am.transit_move_line_id.tc
                        else:
                            rate = am.currency_rate if not am.transit_move_line_id else am.transit_move_line_id.tc #am.currency_id._get_conversion_rate(am.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, am.invoice_date)
                            svl.unit_cost = aml.price_unit * rate
                    else:
                        svl.unit_cost = aml.price_unit
                    move.price_unit = svl.unit_cost
                    svl.value = svl.quantity * svl.unit_cost
            else:
                for move in sm:
                    svl = self.env['stock.valuation.layer'].search([('stock_move_id','=',move.id),('stock_landed_cost_id','=', False),('quantity','>',0)]).sorted(lambda l: l.create_date, reverse=True)
                    if svl:
                        svl = svl[0]
                    if move.purchase_line_id:
                        if move.purchase_line_id.currency_id != self.env.user.company_id.currency_id:
                            if move.picking_id.use_kardex_date:
                                rate = move.purchase_line_id.currency_id._get_conversion_rate(move.purchase_line_id.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, move.picking_id.kardex_date)
                            else:
                                rate = move.purchase_line_id.currency_id._get_conversion_rate(move.purchase_line_id.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, move.picking_id.scheduled_date)
                            svl.unit_cost = (move.purchase_line_id.price_total / move.purchase_line_id.product_qty) * rate
                        else:
                            svl.unit_cost = (move.purchase_line_id.price_total / move.purchase_line_id.product_qty)
                    else:
                        if move.origin_returned_move_id:
                            svl_origin = self.env['stock.valuation.layer'].search([('stock_move_id','=',move.origin_returned_move_id.id),('stock_landed_cost_id','=', False)])
                            svl.unit_cost = svl_origin.unit_cost
                    move.price_unit = svl.unit_cost
                    svl.value = svl.quantity * svl.unit_cost