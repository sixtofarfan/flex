# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class account_analytic_group(models.Model):
	_inherit = 'account.analytic.group'

	sequence_id = fields.Many2one('ir.sequence','Secuencia para Cuentas Analiticas')