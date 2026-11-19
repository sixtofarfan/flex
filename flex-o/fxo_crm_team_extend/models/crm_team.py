# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr


_logger = logging.getLogger(__name__)

class CrmTeam(models.Model):
    _inherit = 'crm.team'
    
    type_team = fields.Selection(string='Type', selection=[('sale', 'Sale'), ('debt_collector', 'Debt Collector')],default='sale')
    destination_sales_team = fields.Many2many('crm.team','id_origin','id_dest', string='Teams')
    expiration_days = fields.Integer(string='Days')
    assign_method = fields.Selection(string='Allocation method', selection=[
        ('automatic', 'Automatic'), 
        ('random', 'Random'),
        ('handbook', 'Handbook')])  