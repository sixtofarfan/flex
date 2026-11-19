# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MaturityAnalysisBook(models.Model):
	_inherit = 'maturity.analysis.book'

	credit_limit = fields.Float(string='Limite de Credito')
	pay_term = fields.Char(string='Termino de Pago')