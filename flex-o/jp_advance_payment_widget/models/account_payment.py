# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class account_payment(models.Model):
    _inherit = 'account.payment'

    custom_rate = fields.Boolean(string='Custom rate')
    
    @api.depends('move_line_ids.matched_debit_ids', 'move_line_ids.matched_credit_ids')
    def _compute_reconciled_invoice_ids(self):
        res = super(account_payment, self)._compute_reconciled_invoice_ids()
        # Obtener las cuentas de anticipos dese los parametros principales
        # y con eso se pueden mostrar los anticipos para poder aplicar en
        # las facturas
        advance_payment_account_id = []
        mp = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        if self[0].payment_type == 'inbound':
            advance_payment_account_id.append(mp.customer_advance_account_nc.id)
            advance_payment_account_id.append(mp.customer_advance_account_fc.id)
            for account in mp.other_accounts_client.ids:
                advance_payment_account_id.append(account)
        elif self[0].payment_type == 'outbound':
            advance_payment_account_id.append(mp.supplier_advance_account_nc.id)
            advance_payment_account_id.append(mp.supplier_advance_account_fc.id)
            # advance_payment_account_id.append(mp.supplier_advance_account_receipt_nc)
            # advance_payment_account_id.append(mp.supplier_advance_account_receipt_fc)
            for account in mp.other_accounts_supplier.ids:
                advance_payment_account_id.append(account)
        for record in self:
            if (line.account_id.id in advance_payment_account_id for line in self.move_line_ids):
                reconciled_moves = record.move_line_ids.mapped('matched_debit_ids.debit_move_id.move_id')\
                    + record.move_line_ids.mapped('matched_credit_ids.credit_move_id.move_id')
                reconciled_ap_moves = reconciled_moves.line_ids.mapped('matched_debit_ids.debit_move_id.move_id')\
                    + reconciled_moves.line_ids.mapped('matched_credit_ids.credit_move_id.move_id')
                record.reconciled_invoice_ids = reconciled_moves.filtered(lambda move: move.is_invoice())\
                    + reconciled_ap_moves.filtered(lambda move: move.is_invoice())
                record.has_invoices = bool(record.reconciled_invoice_ids)
                record.reconciled_invoices_count = len(record.reconciled_invoice_ids)
        return res

    @api.onchange('currency_id','payment_date','journal_id','custom_rate')
    def _onchange_currency_id(self):
        if not self.custom_rate and self.currency_id != self.env.company.currency_id:
            self.type_change = self.currency_id._get_conversion_rate(self.currency_id, self.env.company.currency_id, self.env.company, self.payment_date or fields.Date.today())
        else:
            if not self.custom_rate:
                self.type_change = 1
