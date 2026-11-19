# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
from datetime import *
from math import modf

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	def export_snl_plame(self):
		if len(self.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		first = datetime.strftime(self.date_end, '%Y-%m-%d')[:4]
		second = datetime.strftime(self.date_end, '%Y-%m-%d')[5:7]
		doc_name = '%s0601%s%s%s.snl' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

		f = open(doc_name, 'w+')
		for payslip_run in self.browse(self.ids):
			for slip in payslip_run.slip_ids:
				WD = slip.worked_days_line_ids.filtered(lambda l: l.wd_type_id in MainParameter.wd_dsub)
				f.write("%s|%s|%d|%d|\r\n" % (
							slip.employee_id.type_document_id.sunat_code,
							slip.employee_id.identification_id,
							sum(WD.mapped('number_of_days')),
							sum(WD.mapped('number_of_hours')),
						))
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('0601%s%s%s.snl' % (first, second, self.company_id.vat),base64.encodestring(b''.join(f.readlines())))
