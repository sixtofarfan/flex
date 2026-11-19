# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class SaleConfirm(models.TransientModel):
    """
    This wizard will confirm the all the selected draft invoices
    """

    _name = "sale.order.confirm"
    _description = "Confirm the selected invoices"


    def invoice_confirm(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['sale.order'].browse(active_ids):
            if record.state == 'draft':
                record.action_confirm()
        return {'type': 'ir.actions.act_window_close'}
