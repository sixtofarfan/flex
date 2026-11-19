# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MainParameter(models.Model):
	_inherit = 'main.parameter'

	tax_line_ids = fields.One2many('parameter.tax.line', 'parameter_id')

class ParameterTaxLine(models.Model):
	_name = 'parameter.tax.line'
	_description = 'Parameter Tax Line'

	parameter_id = fields.Many2one('main.parameter', ondelete='cascade')
	tax_id = fields.Many2one('account.tax', string='Impuesto')
	journal_id = fields.Many2one('account.journal', string='Diario')
	type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo de Documento')