# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MainParameter(models.Model):
	_inherit = 'main.parameter'

	concilation_line_ids = fields.One2many('concilation.line', 'main_parameter_id')
	advance_concile_code = fields.Char(string='Codigo Conciliacion Anticipo Proveedores')

class ConcilationLine(models.Model):
	_name = 'concilation.line'
	_description = 'Concilation Line'

	main_parameter_id = fields.Many2one('main.parameter', ondelete='cascade')
	name = fields.Char(string='Concepto')
	code = fields.Char(string='Codigo')
	concept_ids = fields.Many2many('concilation.concept', 'concilation_line_concept_default_rel', string='Filtros')
	currency_id = fields.Many2one('res.currency', string='Moneda')
	account_id = fields.Many2one('account.account', string='Cuenta')
	is_advance = fields.Boolean(string='Es un Anticipo', default=False)
	partner_bank = fields.Boolean(string='Partner Banco', default=False)

class ConcilationConcept(models.Model):
	_name = 'concilation.concept'
	_description = 'Concilation Concept'

	name = fields.Char(string='Filtro')