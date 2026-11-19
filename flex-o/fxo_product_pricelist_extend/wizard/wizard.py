# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Pricelist(models.TransientModel):
    _name = "product.pricelist.wizard"
    _description = "Add Province"

    
    state_id = fields.Many2one(comodel_name='res.country.state', string='State')
    pricelist_province_id = fields.Many2one(comodel_name='product.pricelist', string='Pricelist')    
    province_ids = fields.Many2many(comodel_name='res.country.state', string='Province')
    def_state_id  =fields.Many2many(related='pricelist_province_id.state_id')
    
    def add_province_ids(self):
        ids = self._context['active_id']
        print(ids)
        for item in self.province_ids:
            if self.pricelist_province_id.province_ids in item :
                print(str(item.name) + " Ya registrada")
            else:
                self.pricelist_province_id.province_ids +=item
    

class Pricelist(models.TransientModel):
    _name = "product.pricelist.wizard.district"
    _description = "Add District"

    province_id = fields.Many2one(comodel_name='res.country.state', string='Province')
    pricelist_province_id = fields.Many2one(comodel_name='product.pricelist', string='Pricelist')    
    district_ids  = fields.Many2many(comodel_name='res.country.state', string='District')
    def_province_id  =fields.Many2many(related='pricelist_province_id.province_ids')

    def add_district_ids(self):
        ids = self._context['active_id']
        print(ids)
        for item in self.district_ids:
            if self.pricelist_province_id.district_ids in item :
                print(str(item.name) + " Ya registrada")
            else:
                self.pricelist_province_id.district_ids +=item
    
