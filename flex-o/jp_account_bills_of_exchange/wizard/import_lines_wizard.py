# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import tempfile
import binascii
import xlrd
from datetime import date, datetime

class ImportLines(models.TransientModel):
	_name = "import.lines.wizard"
	_description = "Import Lines Wizard"
	
	excel_file = fields.Binary(string='Excel File')

	def import_lines(self):
		active_id = self.env.context.get('active_id')
		if not active_id:
			return ''

		return {
			'name': _('Import Lines'),
			'res_model': 'import.lines.wizard',
			'view_mode': 'form',
			'view_id': self.env.ref('jp_account_bills_of_exchange.view_import_lines_wizard').id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def import_lines_wizard(self):
		active_id = self.env.context.get('active_id')
		import_form_id = self.env[self.env.context.get('active_model')].search([('id','=',active_id)])
		if not active_id:
			return ''
			
		if not self.excel_file:
			raise UserError('Tiene que cargar un archivo.')
		
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.excel_file))
			fp.seek(0)
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)

		except:
			raise Warning(_("Invalid File!"))
		
		import_form_id.clear_lines()
		# import_form_id.bill_ids.unlink()

		lineas = []
		values = None
		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 12:
					if line[6] != '':
						if type(line[6] == str):
							a1= line[6]
							a1_as_datetime = datetime.strptime(a1, '%d/%m/%Y')
						else:
							a1 = int(float(line[6]))
							a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						bill_date_issue = a1_as_datetime.date().strftime('%Y-%m-%d')
					if line[7] != '':
						if type(line[7] == str):
							a1= line[7]
							a1_as_datetime = datetime.strptime(a1, '%d/%m/%Y')
						else:
							a1 = int(float(line[7]))
							a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						bill_date_due = a1_as_datetime.date().strftime('%Y-%m-%d')
					values = (0,0,{'bill_number': line[0],
								'bank_number': line[1],
								'account_id': import_form_id.journal_id.default_debit_account_id.code,
								'responsable_id':line[2],
								'acceptor_id':line[3],
								'creditor_id':line[4],
								'guarantee_id':line[5],
								'bill_date_issue':bill_date_issue,
								'bill_date_due':bill_date_due,
								'bill_currency_id':line[8] if line[8] else self.env.company.currency_id.name,
								'bill_amount_total':line[9],
								'exchange_rate':line[10],
								'bill_amount_total_signed':line[11],
								'state_of_bill': import_form_id.state_of_bill,
								'type_bill': 'receivable' if self.env.context['type_import'] == '1' else 'payable',
								})
				elif len(line) > 12:
					raise UserError(_('Your file has more columns than expected.'))
				else:
					raise UserError(_('Your file has less columns than expected.'))
				
				if line[8] == import_form_id.currency_id.name:
					lineas.append(values)
		if lineas:
			import_form_id.write({'bill_ids': lineas})

        # Registrar el pago y la fecha
        # active_id = self.env.context.get('active_id')
        # bill_id = self.env['account.bill'].search([('id','=',active_id)])
        # bill_id.payment_date = self.payment_date
        # bill_id.payment_amount = self.payment_amount
        # bill_id.with_context(active_ids=self.ids, 
        #     active_model='pay.bill.wizard', 
        #     active_id=self.id,
        #     payment_journal=self.journal_id,
        #     payment_date=self.payment_date,
        #     payment_currency_id=self.currency_id,
        #     payment_amount=self.payment_amount,
        #     exchange_rate=self.exchange_rate,
        #     ).pay_bill()
