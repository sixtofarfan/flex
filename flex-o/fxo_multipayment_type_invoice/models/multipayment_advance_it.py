# -*- coding: utf-8 -*-
from odoo import fields, models


class MultipaymentAdvanceIt(models.Model):
    _inherit = 'multipayment.advance.it'

    def crear_asiento(self):
        res = super(MultipaymentAdvanceIt, self).crear_asiento()
        # The entry of the payment gets the invoice type of the paid documents
        # (the first one when they differ, as in the exchange of bills)
        for rec in self:
            types = [t for t in rec.invoice_ids.mapped('type_invoice') if t]
            if rec.asiento_id and types:
                rec.asiento_id.type_invoice = types[0]
        return res


class MultipaymentAdvanceItLine(models.Model):
    _inherit = 'multipayment.advance.it.line'

    # Invoice type of the paid document (invoice or bill)
    type_invoice = fields.Selection(related='invoice_id.type_invoice', string='Invoice Type', readonly=True)
