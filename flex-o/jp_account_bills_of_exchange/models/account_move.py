from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from json import dumps
import json

class AccountMove(models.Model):
    _inherit = 'account.move'

    bill_form_id = fields.Many2one(comodel_name='account.bill.form', string='Bill Form', copy=False)
    refinancing_form_id = fields.Many2one(comodel_name='account.refinancing.form', string='Refinancing Form', copy=False)
    import_form_id = fields.Many2one(comodel_name='account.import.bill.form', string='Import Form', copy=False)
    exchange_amount = fields.Monetary(string='Exchange Amount', currency_field='currency_id', copy=False)
    exchange_amount_signed = fields.Monetary(string='Exchange Amount Signed', currency_field='company_currency_id', copy=False)
    invoice_has_outstanding_bills = fields.Boolean(groups="account.group_account_invoice",
        compute='_compute_bills_widget_to_reconcile_info', default=False)
    type = fields.Selection(selection_add=[('bill', 'Bill of exchange')])

    def _get_move_display_name(self, show_ref=False):
        ''' Helper to get the display name of an invoice depending of its type.
        :param show_ref:    A flag indicating of the display name must include or not the journal entry reference.
        :return:            A string representing the invoice.
        '''
        self.ensure_one()
        draft_name = ''
        if self.state == 'draft':
            draft_name += {
                'out_invoice': _('Draft Invoice'),
                'out_refund': _('Draft Credit Note'),
                'in_invoice': _('Draft Bill'),
                'in_refund': _('Draft Vendor Credit Note'),
                'out_receipt': _('Draft Sales Receipt'),
                'in_receipt': _('Draft Purchase Receipt'),
                'entry': _('Draft Entry'),
                'bill': _('Draft Boe'),
            }[self.type]
            if not self.name or self.name == '/':
                draft_name += ' (* %s)' % str(self.id)
            else:
                draft_name += ' ' + self.name
        return (draft_name or self.name) + (show_ref and self.ref and ' (%s%s)' % (self.ref[:50], '...' if len(self.ref) > 50 else '') or '')
    
    def _compute_bills_widget_to_reconcile_info(self):
        for move in self:
            move.invoice_has_outstanding_bills = False
            if move.state != 'posted' or move.invoice_payment_state != 'not_paid' or not move.is_invoice(include_receipts=True):
                continue
            domain = [('bill_form_id.invoice_ids', 'in', self.id),]
            if move.is_inbound():
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
            lines = self.env['account.move.line'].search(domain)
            if len(lines) != 0:
                move.invoice_has_outstanding_bills = True
            # else:
            #     move.invoice_has_outstanding_bills = False

    # TODO Quitamos esta funcion porque sino los usuarios pueden cancelar la factura
    # con letras de un formulario de canje que aun no ha sido conciliado.

    # # TODO No es necesario reescribir la funcion
    # # Reescribimos la funcion para que tb se puedan aplicar letras a las facturas
    # def _compute_payments_widget_to_reconcile_info(self):
    #     res = super(AccountMove, self)._compute_payments_widget_to_reconcile_info()
    #     for move in self:
    #         # move.invoice_outstanding_credits_debits_widget = json.dumps(False)

    #         if move.state != 'posted' or move.invoice_payment_state != 'not_paid' or not move.is_invoice(include_receipts=True):
    #             continue
    #         # pay_term_line_ids = move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))

    #         domain = [('bill_form_id.invoice_ids', 'in', self.id),]

    #         if move.is_inbound():
    #             domain.extend([('credit', '>', 0), ('debit', '=', 0)])
    #             type_payment = _('Outstanding credits')
    #         else:
    #             domain.extend([('credit', '=', 0), ('debit', '>', 0)])
    #             type_payment = _('Outstanding debits')
    #         info = {'content': []}
    #         lines = self.env['account.move.line'].search(domain)
    #         currency_id = move.currency_id
    #         if len(lines) != 0:
    #             move.invoice_has_outstanding = False
    #             for line in lines:
    #                 # get the outstanding residual value in invoice currency
    #                 if line.currency_id and line.currency_id == move.currency_id:
    #                     amount_to_show = abs(line.amount_residual_currency)
    #                 else:
    #                     currency = line.company_id.currency_id
    #                     amount_to_show = currency._convert(abs(line.amount_residual), move.currency_id, move.company_id,
    #                                                        line.date or fields.fields.Date.context_today)
    #                 if float_is_zero(amount_to_show, precision_rounding=move.currency_id.rounding):
    #                     continue
    #                 info['content'].append({
    #                     'journal_name': line.ref or line.move_id.name,
    #                     'amount': amount_to_show,
    #                     'currency': currency_id.symbol,
    #                     'id': line.id,
    #                     'position': currency_id.position,
    #                     'digits': [69, move.currency_id.decimal_places],
    #                     'payment_date': fields.Date.to_string(line.date),
    #                 })
    #             a = move.invoice_outstanding_credits_debits_widget
    #             b = info
    #             if a != 'false':
    #                 text_to_dump = json.dumps(info)
    #                 text_to_dump = text_to_dump[text_to_dump.find('[{')+1:text_to_dump.find(']}')]
    #                 move.invoice_outstanding_credits_debits_widget = a[:a.find('], "move_id"')] + ', ' + text_to_dump +  a[a.find('], "move_id"'):]
    #             else:
    #                 info = {'title': type_payment, 'outstanding': True, 'content': b['content'], 'move_id': move.id}
    #                 move.invoice_outstanding_credits_debits_widget = json.dumps(info)
    #             move.invoice_has_outstanding = True
    #     return res

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    bill_form_id = fields.Many2one(comodel_name='account.bill.form', string='Bills of Exchange Form')
    refinancing_form_id = fields.Many2one(comodel_name='account.refinancing.form', string='Refinancing Form')
    send_form_id = fields.Many2one(comodel_name='account.send.bank', string='Send Form')
    bill_id = fields.Many2one(comodel_name='account.bill', string='ID of Bill of Exchange')
    protest_payment_id = fields.Many2one(comodel_name='account.protest.payment', string='Protest Payment')
    bank_disburse_id = fields.Many2one(comodel_name='account.bank.disbursement', string='Bank Disbursement')
    exchange_bill_id = fields.Many2one(comodel_name='account.bill', string='Bill of Exchange', help='This fields is for getting the exchange rate of the bill when sending to bank.')
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1)

    def unlink(self):
        if self.bill_id:
            self.bill_id.state_of_bill = self.bill_id.last_state
        return super(AccountMoveLine, self).unlink()