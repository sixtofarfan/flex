# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime
from calendar import monthrange
from odoo.tools import UserError

values = {}

class KardexWizard(models.TransientModel):
	_name = "kardex.wizard"
	_description = 'Kardex Wizard'

	initial_date = fields.Date('Initial Date', default=date.today().replace(day=1))
	end_date = fields.Date('End Date', default=date.today().replace(day=monthrange(date.today().year, date.today().month)[1]))
	locked_period = fields.Char(string='Period', default=str(monthrange(date.today().year, date.today().month)[1]) + '-' + str(date.today().month))
	product_ids = fields.Many2many('product.product', string='Products')
	location_ids = fields.Many2many('stock.location', string='Locations')
	all_products = fields.Boolean('All Productos',default=True)
	all_locations = fields.Boolean('All Locations',default=True)

	@api.onchange('all_locations')
	def _onchange_all_locations(self):
		if self.all_locations:
			self.location_ids = self.env['stock.location'].search([('usage','=','internal')])
		else:
			self.location_ids = False

	@api.onchange('initial_date')
	def _onchange_initial_date(self):
		self.locked_period = str(self.initial_date.year) + '-' + str(self.initial_date.month).zfill(2)

	def get_kardex(self):
		if self.initial_date.month != self.end_date.month:
			raise UserError(_('Initial date and final date must be in the same period.'))
		if self.end_date < self.initial_date:
			raise UserError(_('End date should be greather than initial date.'))
		if self.env.context.get('active_id'):
			self.product_ids = self.env['product.product'].search([('id','=',self.env.context.get('active_id'))])
		if not self.product_ids:
			self.product_ids = self.env['product.product'].search([])
		if not self.location_ids:
			self.location_ids = self.env['stock.location'].search([('usage','=','internal')])
		return self.env.ref('jp_kardex_sunat.report_kardex_sunat_xlsx').report_action(self)
