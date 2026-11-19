# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    proteins = fields.Float(string='Proteins', default=0)
    carohydrates = fields.Float(string='Carohydrates', default=0)
    fats = fields.Float(string='Fats', default=0)
    calories = fields.Float(compute='_compute_calories', string='Calories')

    @api.model
    def _compute_calories(self):
        for item in self:
            item.calories = (item.proteins * 4) + (item.carohydrates * 4) + (item.fats * 9)





class ProductProduct(models.Model):
    _inherit = "product.product"

    proteins = fields.Float(related='product_tmpl_id.proteins')
    carohydrates = fields.Float(related='product_tmpl_id.carohydrates')
    fats = fields.Float(related='product_tmpl_id.fats')
    calories = fields.Float(related='product_tmpl_id.calories')

    days = fields.Integer(string='Days',
                          compute='_compute_field_days',
                          help="Only to generate Orders by contracts")

    @api.model
    def _compute_field_days(self):
        for item in self:
            for line in item.product_template_attribute_value_ids:
                item.days += line.product_attribute_value_id.days


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    days = fields.Integer(string='Days', help="Only to generate Orders by contracts")
