from odoo import models, fields, api, _

class AceptationWizard(models.TransientModel):
	_name = 'aceptation.wizard'

	aceptation_date = fields.Date(string='Fecha de Aceptacion', default=fields.Date.today())

	def process_wizard(self):
		print('params', self._context.get('active_model'))
		BillForm = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
		if BillForm:
			BillForm.aceptation_date = self.aceptation_date
			return BillForm.process()