# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# from odoo import api, fields, models, _
# import json
# import requests

# from odoo.exceptions import UserError, ValidationError


# class AccountFullReconcile(models.Model):
# 	_inherit = "account.full.reconcile"
# 	id_loges = fields.Char(string='Id Loges')
	
# 	@api.model
# 	def create(self, vals):
# 		t = super(AccountFullReconcile, self).create(vals)
# 		status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
# 		url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
# 		if status_api == "True":
# 			print("Aplicaciones")
# 			headers = {'Content-type': 'application/json'}
# 			datos =  {
# 						"company_belonging": t.reconciled_line_ids[0].company_id.id,
# 						"date_registry_odoo": str(t.create_date),
# 						"exchange_movement": t.exchange_move_id.name if t.exchange_move_id.name else "",
# 						"number_identy": t.name,
# 						"reconciled_accounting_notes": "",
# 						"date_modify_odoo": str(t.create_date),
# 						"id_odoo": t.id
# 					}
# 			r = requests.post(str(url_api) + 'api/1.0/synchronization/from.odoo/application/', data =json.dumps(datos) , headers=headers)
# 			try:
# 				validate = r.json()
# 				if validate['status_code'] != 201:
# 					t.id_loges = validate['data']['id_loges'] 
# 					raise UserError(r.text)
# 			except Exception as err:
# 				raise UserError(r.text)	
# 		return t
