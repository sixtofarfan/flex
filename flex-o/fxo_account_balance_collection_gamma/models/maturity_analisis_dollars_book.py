# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MaturityAnalysisBook(models.Model):
    _name = 'maturity.analysis.dollars.book'
    _auto = False

    partner = fields.Char(string='Partner')
    collection = fields.Char(string='Cobrador')
    invoice_user_id = fields.Char(string='Invoice User')
    invoice_expo_user_id = fields.Char(string='Expo User')
    credit_limit = fields.Float(string='Limite de Credito')
    credit_limit2 = fields.Float(string='Limite de Credito 2', related='partner_id.credit_limit2')

    partner_id = fields.Many2one(comodel_name='res.partner', string=' Partner')
    total = fields.Float(string='Total General', digits=(12, 2), compute='get_total')
    whithout_debt = fields.Float(string='Total Deuda sin Vencer', digits=(12, 2))
    debt = fields.Float(string='Total Deuda Vencida', compute='get_debt')
    between_1_7 = fields.Float(string='1 - 7', digits=(12, 2))
    between_8_15 = fields.Float(string='8 - 15', digits=(12, 2))
    between_16_30 = fields.Float(string='16 - 30', digits=(12, 2))
    between_31_60 = fields.Float(string='31 - 60', digits=(12, 2))
    between_61_90 = fields.Float(string='61 - 90', digits=(12, 2))
    between_91_more = fields.Float(string='91 - Más', digits=(12, 2))
    payment_term_id = fields.Many2one(comodel_name='account.payment.term', string='Payment Term')

    def get_debt(self):
        for rec in self:
            rec.debt = rec.between_1_7 + rec.between_8_15 + rec.between_16_30 + rec.between_31_60 + rec.between_61_90 + rec.between_91_more

    def get_total(self):
        for rec in self:
            rec.total = rec.whithout_debt + rec.debt
