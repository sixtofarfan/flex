# -*- coding: utf-8 -*-

import time
from datetime import datetime
import tempfile
import binascii
import xlrd
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, _
import logging
_logger = logging.getLogger(__name__)
import io
try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')
try:
	import xlwt
except ImportError:
	_logger.debug('Cannot `import xlwt`.')
try:
	import cStringIO
except ImportError:
	_logger.debug('Cannot `import cStringIO`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')

class ImportStatementLineWizard(models.TransientModel):
	_inherit = 'import.statement.line.wizard'

	def importar(self):
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.document_file))
			fp.seek(0)
			values = {}
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)

		except:
			raise Warning(_("Archivo invalido!"))

		lineas = []

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 8:
					if line[0] == '':
						raise Warning(_('Por favor ingresa el campo Date'))
					else:
						a1 = int(float(line[0]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					values.update( {
						'date': date_string,
						'name': line[1],
						'partner_id': line[2],
						'ref': line[3],
						'catalog_payment_id': line[4],
						'amount': line[5],
						'order_id': line[6],
						'type': line[7],
					})
				elif len(line) > 8:
					raise Warning(_('Tu archivo tiene columnas mas columnas de lo esperado.'))
				else:
					raise Warning(_('Tu archivo tiene columnas menos columnas de lo esperado.'))

				lineas.append(self.create_lines_statement(values))
			
		self.statement_id.write({'line_ids': lineas})
		return {'type': 'ir.actions.act_window_close'}

	def create_lines_statement(self,values):
		if values.get("name") == "":
			raise Warning(_('El campo de name no puede estar vacío.') )

		catalog_payment_id = None
		partner_id = None
		order_id = None

		if values.get("catalog_payment_id"):
			s = str(values.get("catalog_payment_id"))
			code_no = s.rstrip('0').rstrip('.') if '.' in s else s
			catalog_payment_id = self.find_catalog_payment(code_no) if code_no else None

		if values.get("partner_id"):
			s = str(values.get("partner_id"))
			vat = s.rstrip('0').rstrip('.') if '.' in s else s
			partner_id = self.find_partner(vat) if vat else None

		if values.get("order_id"):
			s = str(values.get("order_id"))
			name = s.rstrip('0').rstrip('.') if '.' in s else s
			order_id = self.find_order(name) if name else None

		vals = (0,0,{
			'date': values.get("date"),
			'name': values.get("name"),
			'partner_id': partner_id.id if partner_id else None,
			'ref': values.get("ref"),
			'catalog_payment_id':catalog_payment_id.id if catalog_payment_id else None,
			'amount': values.get("amount"),
			'order_id': order_id.id if order_id else None,
			'type': values.get("type"),
			'company_id': self.statement_id.company_id.id,
		})
		return vals

	def find_order(self, name):
		order_obj = self.env['sale.order']
		order_search = order_obj.search([('name', '=', str(name))], limit=1)
		if order_search:
			return order_search
		else:
			raise Warning(_('No existe una Operacion con el nombre "%s"') % name)