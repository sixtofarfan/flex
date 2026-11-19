# -*- coding: utf-8 -*-

from odoo import models, fields, api
BILLING_TYPE = [('0','Nubefact'),('1','Odoo Facturacion')]

class MainParameter(models.Model):
	_inherit = 'main.parameter'