# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrContract(models.Model):
	_inherit = 'hr.contract'

	salary_rule_ids = fields.Many2many('hr.salary.rule', 'contract_sr_rel', string='Conceptos')
	product_id = fields.Many2one('product.product', string='Producto')
	journal_id = fields.Many2one('account.journal', string='Diario')
	type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo Documento')
	serie_id = fields.Many2one('it.invoice.serie', string='Serie')