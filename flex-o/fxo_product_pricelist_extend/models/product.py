# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr

_logger = logging.getLogger(__name__)


class Pricelist(models.Model):
    _inherit = 'product.pricelist'

    country_id = fields.Many2one('res.country', string='Country')
    state_id = fields.Many2many('res.country.state', string='State')
    province_ids = fields.Many2many('res.country.state', 'pricelist_province_id', 'province_id', string='Province')
    district_ids = fields.Many2many('res.country.state', 'pricelist_district_id', 'district_id', string='District')

    def add_province_ids(self):
        action = self.env.ref('fxo_product_pricelist_extend.action_view_product_pricelist_wizard').read()[0]
        context = {
            'default_pricelist_province_id': self.id
        }
        action['context'] = context
        return action

    def add_district_ids(self):
        action = self.env.ref('fxo_product_pricelist_extend.action_view_product_pricelist_wizard_district').read()[0]
        context = {
            'default_pricelist_province_id': self.id
        }
        action['context'] = context
        return action


class CountryState(models.Model):
    _inherit = 'res.country.state'

    pricelist_province_id = fields.Many2one(comodel_name='product.pricelist', string='Pricelist province')
    pricelist_district_id = fields.Many2one(comodel_name='product.pricelist', string='Pricelist district')
    pricelist_ids = fields.Many2many('product.pricelist', string='Pricelist States')

    def add_province_ids(self):
        action = self.env.ref('fxo_product_pricelist_extend.action_view_product_pricelist_wizard').read()[0]
        # ids = self._context['active_id']
        # context = {
        #     'default_state_id':self.id,
        #     'default_pricelist_province_id':ids
        #     }
        # action['context'] = context
        return action

    def add_district_ids(self):
        action = self.env.ref('fxo_product_pricelist_extend.action_view_product_pricelist_wizard_district').read()[0]
        ids = self.env.context['uid']
        context = {
            'default_province_id': self.id,
            'default_pricelist_province_id': ids
        }
        action['context'] = context
        return action
