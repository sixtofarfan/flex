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

    @api.constrains('state_id','province_id','district_id')
    def fxo_set_delivery_partner(self):
        self.search_delivery()

    @api.onchange('state_id','province_id','district_id')
    def fxo_onchange_delivery(self):
        self.search_delivery()

    def search_delivery(self):
        delivery = self.env['delivery.carrier'].search([ 
            ('district_id','in',[self.district_id.id] ),
        ])
        if len(delivery)  > 0 :
            self.property_delivery_carrier_id = delivery[0].id
        else :
            delivery = self.env['delivery.carrier'].search([ 
                ('province_id','in',[self.province_id.id] ),
            ])
            if len(delivery)  > 0 :
                self.property_delivery_carrier_id = delivery[0].id
            else:
                delivery = self.env['delivery.carrier'].search([ 
                    ('state_ids','in',[self.state_id.id] ),
                ])
                if len(delivery)  > 0 :
                    self.property_delivery_carrier_id = delivery[0].id
