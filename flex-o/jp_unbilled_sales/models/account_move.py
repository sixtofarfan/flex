from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    undelivered_invoices = fields.Boolean(string='Undelivered invoices', compute='_get_undelivered_invoices', store=True, default=True,)
    advanced_invoices = fields.Boolean(string='Advanced invoices', compute='_get_advanceded_invoices', store=True, default=True,)

    @api.depends('invoice_line_ids','picking_ids')
    def _get_undelivered_invoices(self):
        for inv in self:
            if inv.type == 'out_invoice':
                for invoice_line in inv.invoice_line_ids:
                    if invoice_line.sale_line_ids:
                        if sum(invoice_line.sale_line_ids.mapped('qty_delivered')) < invoice_line.quantity:
                            inv.undelivered_invoices = True
                        else:
                            inv.undelivered_invoices = False

    @api.depends('invoice_line_ids','picking_ids')
    def _get_advanceded_invoices(self):
        for inv in self:
            if inv.type == 'out_invoice' and inv.picking_ids:
                if any(picking.kardex_date.date() > (inv.invoice_date or inv.date) for picking in inv.picking_ids):
                    inv.advanced_invoices = True
                else:
                    inv.advanced_invoices = False