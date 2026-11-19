# -*- coding: utf-8 -*-

from odoo import models, fields, api

DAYS = [
        ('0', 'Monday'), 
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
        ]

class SaleSubcriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    date_start  = fields.Date(related='analytic_account_id.date_start')
    recurring_next_date = fields.Date(related='analytic_account_id.recurring_next_date')
    category_id = fields.Many2one(related='product_id.categ_id')

class SaleSubcription(models.Model):
    _inherit = "sale.subscription"

    scheduling_id = fields.One2many(comodel_name='sale.subscription.order.scheduling', inverse_name='subscription_id', string='scheduling')
    additional_id = fields.One2many(comodel_name='sale.subscription.order.additional', inverse_name='subscription_id', string='Additional Product')
    address_id    = fields.One2many(comodel_name='sale.subscription.address', inverse_name='subscription_id', string='Optional Address')
    note_order = fields.Char(string='Note')
    

class SaleSubcriptionScheduling(models.Model):
    _name = "sale.subscription.order.scheduling"

    subscription_id = fields.Many2one(comodel_name='sale.subscription', string='Subscription')
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    product_replance_id = fields.Many2one(comodel_name='product.product', string='Product Replace')
    qty = fields.Float(string='Qty')

class SaleSubcriptionAdditionalProduct(models.Model):
    _name = "sale.subscription.order.additional"

    name = fields.Many2one(comodel_name='product.product', string='Product')
    qty = fields.Float(string='Qty')
    day = fields.Selection(string='Day', selection=DAYS)
    subscription_id = fields.Many2one(comodel_name='sale.subscription', string='Subscription')

class SaleSubcriptionAddress(models.Model):
    _name = "sale.subscription.address"

    day = fields.Selection(string='Day', selection=DAYS)
    address_id = fields.Many2one(comodel_name='res.partner', string='Address')
    partner_id = fields.Many2one(related='subscription_id.partner_id')
    subscription_id = fields.Many2one(comodel_name='sale.subscription', string='Subscription')