# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from dateutil.relativedelta import relativedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

    fees_calculated = fields.Boolean(string='Are fees calculated?', default=False, copy=False)
    fees_qty = fields.Integer(string='Fees quantity')
    days_range = fields.Integer(string='Days range between fees')
    undefined = fields.Boolean(string='Undefined', related='invoice_payment_term_id.undefined')

    def action_post(self):
        if self.undefined and self.fees_qty != len(self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))):
            # raise UserError(_('You have to calculate fees first for the payment term.'))
            return self.env['bill.wizard'].with_context(active_ids=self.ids, active_model='account.move', active_id=self.id if self != self._origin else self._origin.id).get_wizard()
        # elif :
        #     self.fees_calculated = False
        #     self._recompute_payment_terms_lines()
        return super(AccountMove, self).action_post()
    
    def compute_fees(self, value):
    # def compute(self, value, date_ref=False, currency=None):
        # self.ensure_one()
        if self.invoice_payment_term_id:
            date_ref = self.invoice_date or fields.Date.today()
        else:
            date_ref = self.invoice_date_due or self.invoice_date or fields.Date.today()
        # fees_qty = self.fees_qty
        # days_range = self.days_range
        fees_qty = self.env.context.get('fees_qty')
        days_range = self.env.context.get('days_range')
        amount = value
        result = []
        currency = self.currency_id
        next_date = fields.Date.from_string(date_ref)
        for i in range(fees_qty):
            amt = currency.round(value / fees_qty)
            next_date += relativedelta(days=days_range)
            result.append((fields.Date.to_string(next_date), amt))
            amount -= amt
            i+=1
        amount = sum(amt for _, amt in result)
        dist = currency.round(value - amount)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            # result.append((last_date, dist))
            last_amount = result and result[-1][1]
            result.pop()
            result.append((last_date, last_amount + dist))
            # result[-1][1] = result[-1][1] + dist
        return result

    def _recompute_payment_terms_lines(self):
        ''' Compute the dynamic payment term lines of the journal entry.'''
        self.ensure_one()
        in_draft_mode = self != self._origin
        today = fields.Date.context_today(self)
        self = self.with_context(force_company=self.journal_id.company_id.id)

        def _get_payment_terms_computation_date(self):
            ''' Get the date from invoice that will be used to compute the payment terms.
            :param self:    The current account.move record.
            :return:        A datetime.date object.
            '''
            if self.invoice_payment_term_id:
                return self.invoice_date or today
            else:
                return self.invoice_date_due or self.invoice_date or today

        def _get_payment_terms_account(self, payment_terms_lines):
            ''' Get the account from invoice that will be set as receivable / payable account.
            :param self:                    The current account.move record.
            :param payment_terms_lines:     The current payment terms lines.
            :return:                        An account.account record.
            '''
            if payment_terms_lines:
                # Retrieve account from previous payment terms lines in order to allow the user to set a custom one.
                return payment_terms_lines[0].account_id
            elif self.partner_id:
                # Retrieve account from partner.
                if self.is_sale_document(include_receipts=True):
                    return self.partner_id.property_account_receivable_id
                else:
                    return self.partner_id.property_account_payable_id
            else:
                # Search new account.
                domain = [
                    ('company_id', '=', self.company_id.id),
                    ('internal_type', '=', 'receivable' if self.type in ('out_invoice', 'out_refund', 'out_receipt') else 'payable'),
                ]
                return self.env['account.account'].search(domain, limit=1)

        def _compute_payment_terms(self, date, total_balance, total_amount_currency):
            ''' Compute the payment terms.
            :param self:                    The current account.move record.
            :param date:                    The date computed by '_get_payment_terms_computation_date'.
            :param total_balance:           The invoice's total in company's currency.
            :param total_amount_currency:   The invoice's total in invoice's currency.
            :return:                        A list <to_pay_company_currency, to_pay_invoice_currency, due_date>.
            '''
            if self.invoice_payment_term_id:
                to_compute = self.invoice_payment_term_id.compute(total_balance, date_ref=date, currency=self.company_id.currency_id)
                if not self.fees_calculated and self.env.context.get('fees_qty'):
                # if not self.fees_calculated and self.fees_qty:
                    to_compute = self.compute_fees(total_balance)
                if self.currency_id != self.company_id.currency_id:
                    # Multi-currencies.
                    to_compute_currency = self.invoice_payment_term_id.compute(total_amount_currency, date_ref=date, currency=self.currency_id)
                    if not self.fees_calculated and self.env.context.get('fees_qty'):
                    # if not self.fees_calculated and self.fees_qty:
                        to_compute_currency = self.compute_fees(total_amount_currency)
                        # to_compute = self.compute_fees(total_balance)
                    return [(b[0], b[1], ac[1]) for b, ac in zip(to_compute, to_compute_currency)]
                else:
                    # Single-currency.
                    return [(b[0], b[1], 0.0) for b in to_compute]
            else:
                return [(fields.Date.to_string(date), total_balance, total_amount_currency)]

        def _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute):
            ''' Process the result of the '_compute_payment_terms' method and creates/updates corresponding invoice lines.
            :param self:                    The current account.move record.
            :param existing_terms_lines:    The current payment terms lines.
            :param account:                 The account.account record returned by '_get_payment_terms_account'.
            :param to_compute:              The list returned by '_compute_payment_terms'.
            '''
            # As we try to update existing lines, sort them by due date.
            existing_terms_lines = existing_terms_lines.sorted(lambda line: line.date_maturity or today)
            existing_terms_lines_index = 0

            # Recompute amls: update existing line or create new one for each payment term.
            new_terms_lines = self.env['account.move.line']
            for date_maturity, balance, amount_currency in to_compute:
                currency = self.journal_id.company_id.currency_id
                if currency and currency.is_zero(balance) and len(to_compute) > 1:
                    continue

                if existing_terms_lines_index < len(existing_terms_lines):
                    # Update existing line.
                    candidate = existing_terms_lines[existing_terms_lines_index]
                    existing_terms_lines_index += 1
                    candidate.update({
                        'date_maturity': date_maturity,
                        'amount_currency': -amount_currency,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                    })
                else:
                    # Create new line.
                    create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                    candidate = create_method({
                        'name': self.invoice_payment_ref or self.ref or '',
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'quantity': 1.0,
                        'amount_currency': -amount_currency,
                        'date_maturity': date_maturity,
                        'move_id': self.id,
                        'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
                        'account_id': account.id,
                        'partner_id': self.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True,
                        'tc': self.currency_rate
                    })
                new_terms_lines += candidate
                if in_draft_mode:
                    candidate._onchange_amount_currency()
                    candidate._onchange_balance()
            return new_terms_lines

        existing_terms_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        others_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
        company_currency_id = (self.company_id or self.env.company).currency_id
        total_balance = sum(others_lines.mapped(lambda l: company_currency_id.round(l.balance)))
        total_amount_currency = sum(others_lines.mapped('amount_currency'))

        if not others_lines:
            self.line_ids -= existing_terms_lines
            return

        computation_date = _get_payment_terms_computation_date(self)
        account = _get_payment_terms_account(self, existing_terms_lines)
        to_compute = _compute_payment_terms(self, computation_date, total_balance, total_amount_currency)
        new_terms_lines = _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute)

        # Remove old terms lines that are no longer needed.
        self.line_ids -= existing_terms_lines - new_terms_lines

        if new_terms_lines:
            self.invoice_payment_ref = new_terms_lines[-1].name or ''
            self.invoice_date_due = new_terms_lines[-1].date_maturity
        self.fees_calculated = False

    @api.onchange('fees_qty','days_range','invoice_payment_term_id')
    def _onchange_fees_qty(self):
        if self.undefined and self.fees_qty > 0 and self.days_range > 0:
            # self._recompute_payment_terms_lines()
            self.fees_calculated = False
            self.with_context(active_ids=self.ids, 
                fees_calculated=True, 
                fees_qty=self.fees_qty,
                days_range=self.days_range,
                check_move_validity=False,
                )._recompute_payment_terms_lines()
            self.fees_calculated = True
        if not self.undefined:
            self.fees_qty = False
            self.days_range = False
            self.fees_calculated = False

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        self.fees_calculated = False
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.fees_calculated = False