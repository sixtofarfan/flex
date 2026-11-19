# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountReconciliation(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    @api.model
    def process_bank_statement_line(self, st_line_ids, data):
        res = super(AccountReconciliation, self).process_bank_statement_line(st_line_ids, data)
        for move_id in res['moves']:
            bill_id = self.env['account.bill']
            am = self.env['account.move'].search([('id', '=', move_id)])
            for aml in am.line_ids:
                for line_id in aml.full_reconcile_id.reconciled_line_ids:
                    if line_id.bill_form_id:
                        type_bill = 'receivable' if line_id.debit > 0 else 'payable'
                        bill_id = self.env['account.bill'].search([('bill_number', '=', line_id.name),('type_bill','=',type_bill)])
            if bill_id:
                if bill_id.account_move and bill_id.state_of_bill not in ('paid','protested',):
                    raise UserError(_('You can\'t reconcile this bill because it\'s %s') %bill_id.state_of_bill)
                bill_id.account_move = am
                for aml in am.line_ids:
                    aml.bill_id = bill_id
                bill_id.last_state = bill_id.state_of_bill
                bill_id.state_of_bill = 'paid'
                bill_id.payment_date = am.date
        return res
