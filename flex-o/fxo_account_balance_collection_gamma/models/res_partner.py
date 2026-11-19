# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'
	
	property_payment_term_id = fields.Many2one(store=True)