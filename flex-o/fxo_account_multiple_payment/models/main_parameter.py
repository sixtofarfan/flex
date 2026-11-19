# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from calendar import *

class MainParameter(models.Model):
	_inherit = 'main.parameter'

	bbva_bank = fields.Many2one('res.bank', string='Banco BBVA')
	bcp_bank = fields.Many2one('res.bank', string='Banco BCP')
	interbank_bank = fields.Many2one('res.bank', string='Banco Interbank')
	scotiabank_bank = fields.Many2one('res.bank', string='Banco Scotiabank')