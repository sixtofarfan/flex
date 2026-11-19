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

class template_cts_release(models.AbstractModel):
	_name = 'report.fxo_hr_social_benefits.template_cts_release'

	@api.model
	def _get_report_values(self, docids, data=None):
		docs = self.env['hr.cts.line'].browse(docids)
		return {
			'doc_ids': docs.ids,
			'doc_model': 'hr.cts.line',
			'data': data,
			'docs': docs,
			'conversion': self._conversion,
		}

	def _conversion(self, code):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.cts_release_template_id:
			raise UserError('No se puede generar un reporte si no se ha definido una Plantilla para Liberacion de CTS en Parametros')
		jinga_html_template = Template(MainParameter.cts_release_template_id.description)

		row = self.env['hr.cts.line'].browse(code)
		cts_account = row.employee_id.cts_bank_account_id
		if row.contract_id.date_end:
			date_end = '{0} de {1} del {2}'.format(
				row.contract_id.date_end.day,
				MainParameter.get_month_name(row.contract_id.date_end.month),
				row.contract_id.date_end.year,
				)
		else:
			date_end = ''
		fields = {
			'empleado': row.employee_id.name if row.employee_id else '',
			'dni': row.employee_id.identification_id if row.employee_id else '',
			'tipo_documento': row.employee_id.type_document_id.name if row.employee_id.type_document_id else '', 
			'total': str(row.total_cts) if row.total_cts else '0',
			'total_usd': str(row.cts_dollars) if row.cts_dollars else '0',
			'moneda': cts_account.currency_id.name,
			'fin_contrato': date_end,
			'banco_cts': cts_account.bank_id.name,
			'cuenta_cts': cts_account.acc_number, 
		}

		return jinga_html_template.render(**fields)