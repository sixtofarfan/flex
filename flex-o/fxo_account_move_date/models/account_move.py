# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date
from odoo.tools.misc import format_date
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('invoice_date')
    def _onchange_invoice_date(self):
        if self.invoice_date:
            if not self.invoice_payment_term_id:
                self.invoice_date_due = self.invoice_date
            # self.date = self.invoice_date
            self._onchange_currency()

    def _check_fiscalyear_lock_date(self):
        return True
