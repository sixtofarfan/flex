# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_round
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import tempfile
import binascii
import xlrd
from datetime import date, datetime

class ImportBillLines(models.Model):
	_inherit = 'import.bill.lines'
	
	order_id = fields.Many2one('sale.order', string='Routing Order	')


class ImportLines(models.TransientModel):
	_inherit = "import.lines.wizard"
	
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
				if len(line) == 14:
					order = False
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
					if line[13] != '':
						if type(line[13] == str):
							pass
							order = self.env['sale.order'].search([
								('name','=',line[13]),
								#('company_id','=',self.env.user.company_id.id)
							])

							self.env.user.company_id
						else:
							pass
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
								'order_id': order.id if order else False,
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


class ImportBillForm(models.Model):
	_inherit = 'account.import.bill.form'

	def process(self):
		if self.partner_id:
			if any(line.acceptor_id != self.partner_id.name for line in self.bill_ids):
				raise UserError(_('If you selected a partner, every line should be the same partner.'))
		vals=[]
		account_move_ids=[]
		msg = ''
		# account_move_id = self.env['account.move'].create({
		#     'name': self.name,
		#     'currency_id': self.currency_id.id,
		#     'partner_id': self.partner_id.id if self.partner_id else False,
		#     'date': self.exchange_date,
		#     'invoice_date': self.exchange_date,
		#     'journal_id': self.journal_id.id,
		#     'glosa': self.gloss,
		#     'type': 'bill',
		# })
		if self.portfolio:
			form_id = self.env['account.bill.form'].create({
				# 'account_move': account_move_id.id,
				'exchange_date': self.exchange_date,
				'journal_id': self.journal_id.id,
				'bank_position': self.bank_position,
				'currency_id': self.currency_id.id,
				'exchange_rate': self.exchange_rate,
				'state':'imported',
				'gloss': self.gloss,
				'type_form': self._context.get('type_import'),
			})
			self.bill_form_id = form_id
		else:
			form_id = self.env['account.send.bank'].create({
				# 'account_move': account_move_id.id,
				'send_date': self.exchange_date,
				'journal_id': self.journal_id.id,
				'bank_position': self.bank_position,
				'currency_id': self.currency_id.id,
				'exchange_rate': self.exchange_rate,
				'gloss': self.gloss,
				'state':'imported',
			})
			self.send_form_id = form_id

		# Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
		# para crear los asientos
		type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])

		for line in self.bill_ids:
			if line.responsable_id:
				responsable_id = self.env['res.partner'].search([('name', '=', line.responsable_id)])
				if not responsable_id:
					msg += 'The responsable partner ' + line.responsable_id + ' doesn\'t exist in the database\n'
			if line.acceptor_id:
				acceptor_id = self.env['res.partner'].search([('name', '=', line.acceptor_id)])
				if not acceptor_id:
					msg += 'The acceptor partner ' + line.acceptor_id + ' doesn\'t exist in the database\n'
			if line.guarantee_id:
				guarantee_id = self.env['res.partner'].search([('name', '=', line.guarantee_id)])
				if not guarantee_id:
					msg += 'The guarantee partner ' + line.guarantee_id + ' doesn\'t exist in the database\n'
			if line.account_id:
				account_id = self.env['account.account'].search([('code', '=', line.account_id)])
				if not account_id:
					msg += 'The account ' + line.account_id + ' doesn\'t exist in the chart of accounts\n'
			if line.bill_number:
				bill_id = self.env['account.bill'].search([\
					('bill_number', '=', line.bill_number),\
					('account_id', '=', account_id.id),\
					('acceptor_id', '=', acceptor_id.id),\
					('bill_date_issue', '=', line.bill_date_issue),\
					('bill_date_due', '=', line.bill_date_due),\
					('bill_currency_id', '=', self.currency_id.id),\
					('bill_amount_total', '=', line.bill_amount_total),\
					])
				if bill_id:
					msg += 'The bill ' + line.bill_number + ' already exist\n'
			if msg:
				raise UserError(msg)

			# Un asiento por cada letra importada que estarán en el formulario
			# de importación
			vals_aml=[]
			account_move_id = self.env['account.move'].create({
				'name': _('Bill import %s') %line.bill_number + ' - [' + str(line.id) + ']', # self.name,
				'currency_id': self.currency_id.id,
				'partner_id': self.partner_id.id if self.partner_id else False,
				'date': self.exchange_date,
				'invoice_date': line.bill_date_issue,
				'journal_id': self.journal_id.id,
				'glosa': self.gloss,
				'currency_rate': line.exchange_rate,
				'type': 'bill',
			})
			
			val = {
				'bill_number': line.bill_number,
				'bank_number': line.bank_number,
				'account_id': account_id.id,
				'responsable_id': responsable_id.id if self.env.context['type_import'] == '1' else self.env.company.partner_id.id,
				'acceptor_id': acceptor_id.id if self.env.context['type_import'] == '1' else self.env.company.partner_id.id,
				'guarantee_id': guarantee_id.id if line.guarantee_id else False,
				'bill_date_issue': line.bill_date_issue,
				'bill_date_due': line.bill_date_due,
				'bill_currency_id': self.currency_id.id,
				'bill_amount_total': line.bill_amount_total,
				'exchange_rate': line.exchange_rate,
				'bill_amount_total_signed': line.bill_amount_total_signed,
				'state_of_bill': self.state_of_bill,
				'order_id':line.order_id.id,
				'type_bill': 'receivable' if self._context.get('type_import') == '1' else 'payable',
			}
			if self.portfolio:
				val.update({'bill_form_id': form_id.id})
			else:
				val.update({'send_form_id': form_id.id})
			vals.append(val)
			val = {
				'ref': self.name,
				'move_id': account_move_id.id,
				'partner_id': acceptor_id.id,
				'type_document_id': type_document_id.id,
				'nro_comp': line.bill_number,
				'exchange_rate': line.exchange_rate,
				'name': line.bill_number,
				'date': self.exchange_date,
				'journal_id': self.journal_id.id,
				'company_id': self.company_id.id,
				'order_id':line.order_id.id,
				'currency_id': self.currency_id.id if self.currency_id != self.env.company.currency_id else False,
				'company_currency_id': self.company_currency_id.id,
				'account_id': self.journal_id.default_debit_account_id.id,
				'amount_currency': line.bill_amount_total * (1.0 if self._context.get('type_import') == '1' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0,
				'tc': line.exchange_rate,
				'balance': float_round(line.bill_amount_total * (line.exchange_rate if line.exchange_rate > 0 else 1),2) * (1.0 if self._context.get('type_import') == '1' else -1.0),
				'debit': float_round(line.bill_amount_total * (line.exchange_rate if line.exchange_rate > 0 else 1),2) if self._context.get('type_import') == '1' else 0,
				'credit': 0 if self._context.get('type_import') == '1' else float_round(line.bill_amount_total * line.exchange_rate,2),
				'date_maturity': line.bill_date_due,
				}
			if self.portfolio:
				val.update({'bill_form_id': form_id.id})
			else:
				val.update({'send_form_id': form_id.id})
			vals_aml.append(val)
			val = {
				'ref': self.name,
				'move_id': account_move_id.id,
				'partner_id': acceptor_id.id,
				'type_document_id': type_document_id.id,
				'nro_comp': line.bill_number,
				'exchange_rate': line.exchange_rate,
				'name': _('Opening balance for bills'),
				'date': self.exchange_date,
				'journal_id': self.journal_id.id,
				'company_id': self.company_id.id,
				'currency_id': self.currency_id.id if self.currency_id != self.env.company.currency_id else False,
				'company_currency_id': self.company_currency_id.id,
				'account_id': self.bridge_account_id.id,
				'amount_currency': line.bill_amount_total * (-1.0 if self._context.get('type_import') == '1' else 1.0) if self.company_currency_id.id != self.currency_id.id else 0,
				'tc': line.exchange_rate,
				'balance': float_round(line.bill_amount_total * (line.exchange_rate if line.exchange_rate > 0 else 1),2) * (-1.0 if self._context.get('type_import') == '1' else 1.0),
				'credit': float_round(line.bill_amount_total * (line.exchange_rate if line.exchange_rate > 0 else 1),2) if self._context.get('type_import') == '1' else 0,
				'debit': 0 if self._context.get('type_import') == '1' else float_round(line.bill_amount_total * line.exchange_rate,2),
				'date_maturity': line.bill_date_due,
				'order_id':line.order_id.id,
				}
			if self.portfolio:
				val.update({'bill_form_id': form_id.id})
			else:
				val.update({'send_form_id': form_id.id})
			vals_aml.append(val)
			# Si es un desembolso creamos dos lineas mas con la responsabilidad para poder conciliar
			# al momento de pagar, pero deben tener un tipo de cambio de cierre deudor
			if self.state_of_bill == 'disbursed':
				val = {
					'partner_id': acceptor_id.id,
					'type_document_id': type_document_id.id,
					'nro_comp': line.bill_number,
					'exchange_rate': self.closure_rate,
					'move_id':account_move_id.id,
					'name': _('Bank Responsabillity ' + line.bill_number),
					'date': self.exchange_date,
					'journal_id': self.journal_id.id,
					'currency_id': self.currency_id.id if self.currency_id != self.env.company.currency_id else False,
					'company_id': self.company_id.id,
					'company_currency_id': self.company_currency_id.id,
					'account_id': self.journal_id.default_credit_account_id.id,
					'amount_currency': line.bill_amount_total * (-1 if self._context.get('type_import') == '1' else 1) if self.company_currency_id.id != self.currency_id.id else 0,
					'tc': self.closure_rate,
					'balance': float_round(line.bill_amount_total * (self.closure_rate if self.closure_rate > 0 else 1),2) * (-1 if self._context.get('type_import') == '1' else 1),
					'credit': float_round(line.bill_amount_total * (self.closure_rate if self.closure_rate > 0 else 1),2) if self._context.get('type_import') == '1' else 0,
					'debit': 0 if self._context.get('type_import') == '1' else float_round(line.bill_amount_total * self.closure_rate,2),
					'date_maturity': line.bill_date_due,
					'order_id':line.order_id.id,
				}
				vals_aml.append(val)
				val = {
					'partner_id': acceptor_id.id,
					'type_document_id': type_document_id.id,
					'nro_comp': line.bill_number,
					'exchange_rate': self.closure_rate,
					'move_id':account_move_id.id,
					'name': _('Bank Responsabillity ' + line.bill_number),
					'date': self.exchange_date,
					'journal_id': self.journal_id.id,
					'currency_id': self.currency_id.id if self.currency_id != self.env.company.currency_id else False,
					'company_id': self.company_id.id,
					'company_currency_id': self.company_currency_id.id,
					'account_id': self.journal_id.default_credit_account_id.id,
					'amount_currency': line.bill_amount_total * (1 if self._context.get('type_import') == '1' else -1) if self.company_currency_id.id != self.currency_id.id else 0,
					'tc': self.closure_rate,
					'balance': float_round(line.bill_amount_total * (self.closure_rate if self.closure_rate > 0 else 1),2) * (1 if self._context.get('type_import') == '1' else -1),
					'debit': float_round(line.bill_amount_total * (self.closure_rate if self.closure_rate > 0 else 1),2) if self._context.get('type_import') == '1' else 0,
					'credit': 0 if self._context.get('type_import') == '1' else float_round(line.bill_amount_total * self.closure_rate,2),
					'date_maturity': line.bill_date_due,
					'order_id':line.order_id.id,
				}
				vals_aml.append(val)
			self.env['account.move.line'].create(vals_aml)

			account_move_id.post()
			account_move_ids.append(account_move_id.id)
		bill_ids = self.env['account.bill'].create(vals)
		self.account_move_ids = [(6,0, account_move_ids)]
		# self.account_move_ids.post()
		if self.bill_form_id:
			self.bill_form_id.bill_ids = [(6,0, bill_ids.ids)]
		else:
			self.send_form_id.bill_ids = [(6,0, bill_ids.ids)]
		self.state = 'done'

	def download_template(self):
		return {
				'type' : 'ir.actions.act_url',
				'url': '/web/binary/fxo_download_template_import_bills?model=account.advanced.bill.form&id=%s'%(self.id),
				'target': 'new',
				}