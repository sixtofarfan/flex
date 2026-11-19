# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr


_logger = logging.getLogger(__name__)

class Partner(models.Model):
	_inherit = 'res.partner'

	kmz = fields.Binary(string='KMZ')
	type_via = fields.Many2one(comodel_name='einvoice.catalog.04', string='Tipo de Via')
	name_via = fields.Char(string='Nombre Via')
	number_new = fields.Char(string='Numero')
	number_via = fields.Selection([
		('nro', 'NRO'),
		('mz', 'MZ'),
		('km', 'KM'),
	], string='Tipo Numero Via')
	property_type = fields.Selection(string='Tipo de Inmueble', selection=[
		('Edificio', 'Edificio'), 
		('Residencia', 'Residencia'),
		('Quinta', 'Quinta'),
		('Casa','Casa'),
		('Otro','Otro')
		])
	property_name = fields.Char(string='Nombre de Inmueble')
	floor = fields.Char(string='Piso')
	interior = fields.Selection([
		('interior', 'Interior'),
		('lot', 'Lote'),
		('dpto', 'Dpto'),
		('of', 'oficina'),
	], string='Tipo Interior Via')
	interior_valor = fields.Char(string='Interior Via')
	poblacion = fields.Selection([('ZI', 'zi')], string='Tipo Poblacion Via')
	poblation = fields.Many2one('einvoice.catalog.03', string='Tipo Poblacion Via')
	poblacion_valor = fields.Char(string='Referencia')
	local = fields.Char(string='Local / Apartamento')
	apple = fields.Char(string='Manzana')
	lot = fields.Char(string='Lote')
	type_zone = fields.Many2one(comodel_name='einvoice.catalog.03', string='Tipo de Zona')
	name_zone = fields.Char(string='Nombre de Zona')


	@api.onchange(
		'type_via', 'name_via', 'number_via', 'number_new', 'floor', 
		'interior', 'interior_valor', 'poblation', 'poblacion_valor',
		'state_id', 'province_id', 'district_id'
	)
	def set_street_new(self):
		if self.type != 'contact':
			street_val = '{type_via} {name_via} {number_via} {number_new}'.format(
				type_via = self.type_via.descriptio if self.type_via else '',
				name_via = self.name_via if self.name_via else '',
				number_via = dict(self._fields['number_via'].selection).get(self.number_via) if self.number_via else '',
				number_new = self.number_new if self.number_new else '',
			)
			if street_val.split():
				street_ext = '{floor} {interior} {interior_valor} {poblation} {poblacion_valor} {state_id} - {province_id} - {district_id}'.format(
					floor = self.floor if self.floor else '',
					interior = dict(self._fields['interior'].selection).get(self.interior) if self.interior else '',
					interior_valor = self.interior_valor if self.interior_valor else '',
					poblation = self.poblation.desc if self.poblation else '',
					poblacion_valor = self.poblacion_valor if self.poblacion_valor else '',
					state_id = self.state_id.name if self.state_id else '',
					province_id = self.province_id.name if self.province_id else '',
					district_id = self.district_id.name if self.district_id else '',
				)
				street = ' '.join(street_val.split() + street_ext.split())
				self.street = street