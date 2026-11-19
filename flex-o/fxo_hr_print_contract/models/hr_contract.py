# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from subprocess import Popen, PIPE

class hr_contract(models.Model):
	_inherit = 'hr.contract'

	template_id = fields.Many2one('hr.contract.template', string='Plantilla de Contrato')

	def send_contract_email(self):
		for rec in self:
			template = self.env.ref('fxo_hr_print_contract.report_contract_employee')
			email_values = {
				'email_to': rec.employee_id.work_email,
			}
			template.send_mail(rec.id, force_send=True, email_values=email_values)

class hr_job(models.Model):
	_inherit = 'hr.job'

	description_contract = fields.Text("Texto en el contrato", help= "En este campo se pone la descripción del puesto que saldrá en el contrato por ejemplo si el puesto es  Operario de limpieza en este campo se pondría: de mantenimiento y fumigación en sus diferentes ambientes") 

class hr_contract_template(models.Model):
	_name = 'hr.contract.template'

	name = fields.Char('Nombre')
	code = fields.Char('Codigo')
	description = fields.Html(string='Descripcion')