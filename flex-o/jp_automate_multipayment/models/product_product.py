# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    type_operation = fields.Many2one('type.operation', string='Type of Operation')
    type_good_service = fields.Many2one('einvoice.catalog.54', string='Goods and Services')
    detraction_bool = fields.Boolean(default=False, compute='_check_detraction_bool')

    @api.depends('type_operation', 'type_good_service')
    def _check_detraction_bool(self):
        for record in self:
            record.detraction_bool = False if not record.type_operation and not record.type_good_service else True
            for variant in record.product_variant_ids:
                if not variant.type_operation:
                    variant.type_operation = record.type_operation
                if not variant.type_good_service:
                    variant.type_good_service = record.type_good_service


class ProductProduct(models.Model):
    _inherit = 'product.product'

    type_operation = fields.Many2one(related='product_tmpl_id.type_operation', string='Type of Operation', store=True)
    type_good_service = fields.Many2one(related='product_tmpl_id.type_good_service', string='Goods and Services', store=True)
    detraction_bool = fields.Boolean(default=False, compute='_check_detraction_bool')

    @api.depends('type_operation', 'type_good_service')
    def _check_detraction_bool(self):
        for record in self:
            record.detraction_bool = False if not record.type_operation and not record.type_good_service else True
