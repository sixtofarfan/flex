# -*- coding: utf-8 -*-
from odoo  import models, fields, api
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	ref_code = fields.Char(string='Codigo Referencia')