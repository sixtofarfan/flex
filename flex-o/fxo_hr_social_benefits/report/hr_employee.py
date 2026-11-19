# -*- coding: utf-8 -*-

import time

import odoo.addons.decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError

from jinja2 import Template
import subprocess
import sys

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	import arrow
except:
	install('arrow')

class template_work_voucher(models.AbstractModel):
	_name = 'report.fxo_hr_social_benefits.template_work_voucher'

	@api.model
	def _get_report_values(self, docids, data=None):
		docs = self.env['hr.employee'].browse(docids)
		return {
			'doc_ids': docs.ids,
			'doc_model': 'hr.employee',
			'data': data,
			'docs': docs,
			'conversion': self._conversion,
		}

	def _conversion(self, code):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.work_voucher_template_id:
			raise UserError('No se puede generar un reporte si no se ha definido una Plantilla para Certificado de Trabajo en Parametros')
		jinga_html_template = Template(MainParameter.work_voucher_template_id.description)

		row = self.env['hr.employee'].browse(code)
		if row.emp_date_start:
			date_start = '{0} de {1} del {2}'.format(
				row.emp_date_start.day,
				MainParameter.get_month_name(row.emp_date_start.month),
				row.emp_date_start.year,
				)
		else:
			date_start = ''
		last_contract = row.contract_id
		if last_contract.date_end:
			date_end = '{0} de {1} del {2}'.format(
				last_contract.date_end.day,
				MainParameter.get_month_name(last_contract.date_end.month),
				last_contract.date_end.year,
				)
		else:
			date_end = ''
		fields = {
			'nombre': row.name if row.name else '',
			'nro_documento': row.identification_id if row.identification_id else '',
			'ocupacion': row.job_id.name if row.job_id else '',
			'direccion': row.address if row.address else '',
			'tipo_documento': row.type_document_id.name if row.type_document_id else '',
			'fecha_ingreso': date_start,
			'fecha_fin': date_end,
			'puesto': row.job_id.name if row.job_id else '',
		}

		return jinga_html_template.render(**fields)