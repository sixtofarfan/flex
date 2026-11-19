# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class WkLocationTeam(models.Model):
	_name = 'wk.location.team'
	_description = 'Wk Location Team'

	user_id = fields.Many2one('res.users', string='Diseñador')
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, readonly=True)
	country_id = fields.Many2one('res.country', string='Pais', default=lambda self: self.env.company.country_id.id)
	state_ids = fields.Many2many('res.country.state', 'res_country_state_location_team', string='Departamentos')
	province_ids = fields.Many2many('res.country.state', 'res_country_province_location_team', string='Provincias')
	district_ids = fields.Many2many('res.country.state', 'res_country_district_location_team', string='Distritos')