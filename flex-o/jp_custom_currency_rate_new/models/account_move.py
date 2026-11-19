# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime
from odoo.exceptions import Warning
from odoo.tools import float_round

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # tc_per = fields.Boolean(string='Usar Tc Personalizado',copy=False,default=False)
    
    # def 

    @api.onchange('invoice_date','date','tc_per','currency_rate','currency_id','serie_id')
    def _onchange_tc_per(self):
        move_date = self.invoice_date if self.is_invoice(include_receipts=True) else self.date
        if not self.tc_per:
            currency_rate = self.env['res.currency.rate'].search([('name','=',move_date),('currency_id','=',self.currency_id.id),('company_id','=',self.company_id.id)],limit=1)
            self.currency_rate = currency_rate.sell_rate if currency_rate else 1
        #     if not currency_rate:
        #         raise Warning(_('Currency rate not found for %s') %move_date.strftime("%d/%m/%Y"))
        #     if any(line.currency_id != self.env.company.currency_id and line.currency_id for line in self.line_ids):
        #         currency_id = self.line_ids.filtered(lambda l: l.currency_id != self.env.company.currency_id)[0].currency_id
        #     else:
        #         currency_id = self.currency_id
        #     if not self.tc_per and currency_id and currency_id != self.env.company.currency_id:
        #         self.currency_rate = currency_id._get_conversion_rate(currency_id, self.env.company.currency_id, self.env.company, (self.invoice_date if self.type != 'entry' else self.date) or datetime.datetime.now())
        #     else:
        #         if not self.tc_per and currency_id == self.env.company.currency_id or not currency_id:
        #             self.currency_rate = 1
        #     if currency_id != self.env.company.currency_id:
        #         for line in self.line_ids:
        #             line.tc = self.currency_rate if line.currency_id == currency_id and line.currency_id else 1
        #     else:
        #         for line in self.line_ids:
        #             line.tc = 1   
        # for line in self.line_ids:
        #     if line.currency_id and line.currency_id != self.env.company.currency_id:
        #         line.debit = float_round(line.amount_currency, 2) * line.tc  if line.debit > 0 else 0
        #         line.credit = float_round(abs(line.amount_currency), 2) * line.tc if line.credit > 0 else 0
        for l in self.line_ids:
            l.tc = self.currency_rate
        self._onchange_currency()

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        return res

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     res = super(AccountMoveLine, self)._onchange_product_id()
    #     if self.move_id.currency_id != self.env.company.currency_id:
    #         if self.move_id.tc_per:
    #             for line in self:
    #                 price_unit = self._get_computed_price_unit()
    #                 line.price_unit = price_unit * (1 / self.move_id.currency_rate)
    #     return res
    
    # @api.onchange('product_uom_id')
    # def _onchange_uom_id(self):
    #     res = super(AccountMoveLine, self)._onchange_uom_id()
    #     if self.move_id.currency_id != self.env.company.currency_id:
    #         if self.move_id.tc_per:
    #             for line in self:
    #                 price_unit = self._get_computed_price_unit()
    #                 line.price_unit = price_unit * (1 / self.move_id.currency_rate)
    #     return res
    
    # @api.model
    # def _get_fields_onchange_subtotal_model(self, price_subtotal, move_type, currency, company, date):
    #     res = super(AccountMoveLine, self)._get_fields_onchange_subtotal_model(price_subtotal, move_type, currency, company, date)
    #     if self.move_id.currency_id != self.move_id.company_currency_id:
    #         if self.move_id.tc_per:
    #             if res['debit'] > 0:
    #                 res['debit'] = float_round(res['amount_currency'], 2) / (1 / self.move_id.currency_rate)
    #             else:
    #                 res['credit'] = float_round(abs(res['amount_currency']), 2) / (1 / self.move_id.currency_rate)
    #             self.tc = self.move_id.currency_rate
    #         else:
    #             if self.currency_id:
    #                 self.tc = self.currency_id._get_conversion_rate(self.move_id.currency_id, self.env.company.currency_id, self.env.company, self.move_id.invoice_date or datetime.datetime.now())
    #     return res
    
    @api.onchange('amount_currency')
    def _onchange_amount_currency(self):
        res = super(AccountMoveLine, self)._onchange_amount_currency()
        currency_rate = self.move_id.currency_rate
        if self.move_id.currency_id != self.move_id.company_currency_id and not self.move_id.is_invoice(include_receipts=True):
            if self.move_id.tc_per:
                # self.tc = self.move_id.currency_rate
                currency_rate = self.move_id.currency_rate
            else:
                currency_rate = self.currency_id._get_conversion_rate(self.move_id.currency_id, self.env.company.currency_id, self.env.company, self.move_id.date or datetime.datetime.now())
            self.move_id.currency_rate = currency_rate
            self.debit = float_round(self.amount_currency * currency_rate, 2) if self.amount_currency > 0 else 0
            self.credit = float_round(abs(self.amount_currency) * currency_rate, 2) if self.amount_currency < 0 else 0
        for line in self.move_id.line_ids:
            line.tc = currency_rate
        return res
    
    # @api.onchange('tc')
    # def _onchange_tc(self):
    #     if abs(self.amount_currency) > 0:
    #         self.debit = float_round(self.amount_currency, 2) * self.tc if self.debit > 0 else 0
    #         self.credit = float_round(abs(self.amount_currency), 2) * self.tc if self.credit > 0 else 0
    
    # def _recompute_debit_credit_from_amount_currency(self):
    #     res = super(AccountMoveLine, self)._recompute_debit_credit_from_amount_currency()
    #     if self.move_id.tc_per:
    #         for line in self:
    #             company_currency = line.account_id.company_id.currency_id
    #             balance = float_round(line.amount_currency, 2)
    #             if line.currency_id and company_currency and line.currency_id != company_currency:
    #                 balance = balance * line.move_id.currency_rate
    #                 line.debit = balance > 0 and balance or 0.0
    #                 line.credit = balance < 0 and -balance or 0.0
    #     return res

    @api.model
    def _get_fields_onchange_subtotal_model(self, price_subtotal, move_type, currency, company, date):
        res = super(AccountMoveLine, self)._get_fields_onchange_subtotal_model(price_subtotal, move_type, currency, company, date)
        if currency and currency != company.currency_id:
            if move_type in self.move_id.get_outbound_types():
                sign = 1
            elif move_type in self.move_id.get_inbound_types():
                sign = -1
            else:
                sign = 1
            price_subtotal *= sign
            sub_total = price_subtotal * self.move_id.currency_rate
            if self.currency_id:
                balance = self.currency_id.round(sub_total)
            else:
                balance = company.currency_id.round(sub_total)
            res['amount_currency'] = price_subtotal
            res['debit'] = balance > 0.0 and balance or 0.0
            res['credit'] = balance < 0.0 and -balance or 0.0
            self.tc = self.move_id.currency_rate
        return res

    def _recompute_debit_credit_from_amount_currency(self):
        res = super(AccountMoveLine, self)._recompute_debit_credit_from_amount_currency()
        for line in self:
            # Recompute the debit/credit based on amount_currency/currency_id and date.

            company_currency = line.account_id.company_id.currency_id
            balance = line.amount_currency
            if line.currency_id and company_currency and line.currency_id != company_currency:
                balance *= line.tc #line.currency_id._convert(balance, company_currency, line.account_id.company_id, line.move_id.date or fields.Date.today())
                line.debit = balance > 0 and balance or 0.0
                line.credit = balance < 0 and -balance or 0.0
        return res