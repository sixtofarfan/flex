# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr


_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self,vals):
        t = super(ResPartner,self).create(vals)
        t.onchange_state_id()
        t.onchange_province_id()
        t.onchange_district_id()
        t.write({})
        return t

    def write(self,vals):
        t = super(ResPartner,self).write(vals)
        for partner in self:
            new_property = partner.property_product_pricelist

            if partner.state_id.id:
                pricelist = self.env['product.pricelist'].search([
                    ('state_id','in',partner.state_id.id)
                ])
                if len(pricelist) > 0:
                    new_property = pricelist[0].id

            if partner.province_id.id:
                pricelist = self.env['product.pricelist'].search([
                    ('province_ids','in',partner.province_id.id)
                ])
                if len(pricelist) > 0:
                    new_property = pricelist[0].id

            if partner.district_id.id:
                pricelist = self.env['product.pricelist'].search([
                    ('district_ids','in',partner.district_id.id)
                ])
                if len(pricelist) > 0:
                    new_property = pricelist[0].id

            pls = self.env['product.pricelist'].search(
                [('country_group_ids.country_ids.code', '=', partner.country_id and partner.country_id.code or False)],
                limit=1
            )
            default_for_country = pls and pls[0]
            actual = self.env['ir.property'].get('property_product_pricelist', 'res.partner', 'res.partner,%s' % partner.id)
            # update at each change country, and so erase old pricelist
            if new_property or (actual and default_for_country and default_for_country.id != actual.id):
                # keep the company of the current user before sudo
                self.env['ir.property'].with_context(force_company=self._context.get('force_company', self.env.company.id)).sudo().set_multi(
                    'property_product_pricelist',
                    partner._name,
                    {partner.id: new_property or default_for_country.id},
                    default_value=default_for_country.id
                )
        return t


    @api.onchange('state_id')
    def onchange_state_id(self):
        if self.state_id.id:
            pricelist = self.env['product.pricelist'].search([
                ('state_id','in',self.state_id.id)
            ])
            if len(pricelist) > 0:
                self.property_product_pricelist = pricelist[0].id
    
    @api.onchange('province_id')
    def onchange_province_id(self):
        if self.province_id.id:
            pricelist = self.env['product.pricelist'].search([
                ('province_ids','in',self.province_id.id)
            ])
            if len(pricelist) > 0:
                self.property_product_pricelist = pricelist[0].id
        
    @api.onchange('district_id')
    def onchange_district_id(self):
        if self.district_id.id:
            pricelist = self.env['product.pricelist'].search([
                ('district_ids','in',self.district_id.id)
            ])
            if len(pricelist) > 0:
                self.property_product_pricelist = pricelist[0].id