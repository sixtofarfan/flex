# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr


_logger = logging.getLogger(__name__)

class DeliveryOrder(models.Model):
    _inherit = 'delivery.carrier'
    
    province_id =  fields.Many2many('res.country.state', 'delivery_province_id', 'province_id', 'delivery_id', 'Provincia')
    district_id =  fields.Many2many('res.country.state', 'delivery_disctrict_id', 'district_id', 'delivery_id', 'Districto')
    show_web = fields.Boolean(string='Retiro En tienda')
    
    
    
    