# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleReport(models.Model):
	_inherit = 'sale.report'

	salesman_id = fields.Many2one('res.partner', string='Codigo Vendedor')

	def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
		fields['salesman_id'] = ', rp.id as salesman_id'
		from_clause += 'left join res_partner rp on rp.id = s.salesman_id'
		groupby += ', rp.id' 
		return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)