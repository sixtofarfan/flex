# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime

class account_payment(models.Model):
    _inherit = "account.payment"

    @api.onchange('payment_date','currency_id')
    def _get_currency_rate(self):
        res = super(account_payment, self)._get_currency_rate()
        if self.currency_id != self.env.company.currency_id:
            if not self.is_personalized_change:
                cu_rate = self.env['res.currency.rate'].search([('name','=',self.payment_date),('company_id','=',self.company_id.id)],limit=1)
                if cu_rate:
                    self.type_change = cu_rate.rate
                    self.aux_type_change = cu_rate.rate
        else:
            self.type_change = 1
        return res

    def _prepare_payment_moves(self):
        res = super(account_payment, self)._prepare_payment_moves()
        if self.is_personalized_change or self.custom_rate:
            for payment in res:
                list_moves = list(payment['line_ids'])
                for move in list_moves:
                    list_lines = move[2]
                    if self.currency_id != self.env.user.company_id.currency_id:
                        list_lines['credit'] = abs(list_lines['amount_currency']) / (1 / self.type_change) if abs(list_lines['credit']) > 0 else  0
                        list_lines['debit'] = list_lines['amount_currency'] / (1 / self.type_change) if list_lines['debit'] > 0 else  0
                        list_lines['tc'] = self.type_change
                    else:
                        if self.destination_journal_id.currency_id != self.env.user.company_id.currency_id or self.journal_id.currency_id != self.env.user.company_id.currency_id:
                            account_currency = self.env['account.account'].search([('id','=',list_lines['account_id'])]).currency_id
                            if list_lines['credit'] > 0:
                                list_lines['amount_currency'] = (list_lines['credit'] / self.type_change) * -1 if abs(list_lines['amount_currency']) > 0 and account_currency != self.env.user.company_id.currency_id else 0
                            else:
                                list_lines['amount_currency'] = list_lines['debit'] / self.type_change if list_lines['amount_currency'] > 0 and account_currency != self.env.user.company_id.currency_id else 0
                            list_lines['tc'] = self.type_change if abs(list_lines['amount_currency']) > 0 else 1
            
        else:
            rate = 1
            for payment in res:
                list_moves = list(payment['line_ids'])
                for move in list_moves:
                    list_lines = move[2]
                    if self.currency_id != self.env.user.company_id.currency_id:
                        rate = self.currency_id._get_conversion_rate(self.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, self.payment_date or datetime.datetime.now())
                    if self.destination_journal_id.currency_id and self.destination_journal_id.currency_id != self.env.user.company_id.currency_id:
                        rate = self.currency_id._get_conversion_rate(self.destination_journal_id.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, self.payment_date or datetime.datetime.now())
                    if self.journal_id.currency_id and self.journal_id.currency_id != self.env.user.company_id.currency_id:
                        rate = self.currency_id._get_conversion_rate(self.journal_id.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, self.payment_date or datetime.datetime.now())
                    list_lines['tc'] = rate if abs(list_lines['amount_currency']) > 0 else 1
            self.type_change = rate
        return res

    def post(self):
        res = super(account_payment, self).post()
        for pay in self:
            for line in pay.move_line_ids:
                line.tc = pay.type_change
        return res

    @api.model
    def create(self,vals):
        if 'type_change' in vals:
            vals.update({'aux_type_change': vals['type_change']})
        res = super(account_payment, self).create(vals)
        return res
