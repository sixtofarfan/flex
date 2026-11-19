# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
import tempfile
import binascii
import xlrd
import io
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning , UserError
from odoo import models, fields, exceptions, api, _

import logging
_logger = logging.getLogger(__name__)

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


TYPE2JOURNAL = {
	'out_invoice': 'sale',
	'in_invoice': 'purchase',
	'out_refund': 'sale',
	'in_refund': 'purchase',
}

class AccountMove(models.Model):
	_inherit = "account.move"



	custom_seq = fields.Boolean('Custom Sequence')
	system_seq = fields.Boolean('System Sequence')
	invoice_name = fields.Char('Invoice Name')


class gen_inv(models.TransientModel):
	_name = "gen.invoice"

	file = fields.Binary('File')
	account_opt = fields.Selection([('default', 'Use Account From Configuration product/Property'), ('custom', 'Use Account From Excel/CSV')], string='Account Option', required=True, default='default')
	type = fields.Selection([('in', 'Customer'), ('out', 'Supplier'),('cus_credit_note','Customer Credit Note'),('ven_credit_note','Vendor Credit Note')], string='Type', required=True, default='in')
	sequence_opt = fields.Selection([('custom', 'Use Excel/CSV Sequence Number'), ('system', 'Use System Default Sequence Number')], string='Sequence Option',default='custom')
	import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')
	sample_option = fields.Selection([('csv', 'CSV'),('xls', 'XLS')],string='Sample Type',default='csv')
	down_samp_file = fields.Boolean(string='Download Sample Files')
	stage = fields.Selection(
		[('draft', 'Import Draft Invoice'), ('confirm', 'Validate Invoice Automatically With Import')],
		string="Invoice Stage Option", default='draft')
	import_prod_option = fields.Selection([('name', 'Name'),('code', 'Code'),('barcode', 'Barcode')],string='Import Product By ',default='name')
	journal_id = fields.Many2one('account.journal',string='Diario',required=True)

	def make_invoice(self, values):
		invoice_obj = self.env['account.move']
		if self.sequence_opt == "custom":
			if self.type == "in":
				invoice_search = invoice_obj.search([
					('name', '=', values.get('invoice')),
					('type', '=', 'out_invoice'),
					('custom_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			elif self.type == 'out':
				invoice_search = invoice_obj.search([
					('name', '=', values.get('invoice')),
					('type', '=', 'in_invoice'),
					('custom_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			elif self.type == 'cus_credit_note':
				invoice_search = invoice_obj.search([
					('name', '=', values.get('invoice')),
					('type', '=', 'out_refund'),
					('custom_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			else:
				invoice_search = invoice_obj.search([
					('name', '=', values.get('invoice')),
					('type', '=', 'in_refund'),
					('custom_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
		else:
			if self.type == "in":
				invoice_search = invoice_obj.search([
					('invoice_name', '=', values.get('invoice')),
					('type', '=', 'out_invoice'),
					('system_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			elif self.type == 'out':
				invoice_search = invoice_obj.search([
					('invoice_name', '=', values.get('invoice')),
					('type', '=', 'in_invoice'),
					('system_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			elif self.type == 'cus_credit_note':
				invoice_search = invoice_obj.search([
					('invoice_name', '=', values.get('invoice')),
					('type', '=', 'out_refund'),
					('system_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
			else:
				invoice_search = invoice_obj.search([
					('invoice_name', '=', values.get('invoice')),
					('type', '=', 'in_refund'),
					('system_seq','=',True),
					('company_id','=',self.env.company.id)
				],limit=1)
		request_id = self.find_payment_request(values.get('request_id'))
		order_id = self.find_order(values.get('order_id'))
		values['request_id'] = request_id.id if request_id else None
		values['order_id'] = order_id.id if order_id else None
		if invoice_search:
			if invoice_search.partner_id.vat != str(values.get('customer')):
				raise Warning(_('Customer name is different for "%s" .\n Please define same.') % values.get('invoice'))

			if  invoice_search.currency_id.name != values.get('currency'):
				raise Warning(_('Currency is different for "%s" .\n Please define same.') % values.get('invoice'))

			if  invoice_search.invoice_user_id.name != values.get('salesperson'):
				raise Warning(_('User(Salesperson) is different for "%s" .\n Please define same.') % values.get('invoice'))

			if invoice_search.type_document_id.code != str(values.get('td')):
				raise Warning(_('Type Document is different for "%s" .\n Please define same.') % values.get('invoice'))

			if invoice_search.ref != str(values.get('nro_comprobante')):
				raise Warning(_('Invoice Number is different for "%s" .\n Please define same.') % values.get('invoice'))

			if invoice_search.glosa != values.get('glosa'):
				raise Warning(_('Glosa is different for "%s" .\n Please define same.') % values.get('invoice'))

			if invoice_search.state != 'draft':
				raise Warning(_('Invoice "%s" is not in Draft state.') % invoice_search.name)

			self.make_invoice_line(values, invoice_search)
			return invoice_search

		else:
			if str(values.get('customer')) == '':
				raise Warning(_('Please assign a Partner.'))
			else:
				partner_id = self.find_partner(str(values.get('customer')))
			currency_id = self.find_currency(values.get('currency'))
			salesperson_id = self.find_sales_person(values.get('salesperson'))
			collection_id = self.find_collection_person(values.get('collection_id'))
			invoice_payment_term_id = self.find_invoice_payment_term(values.get('invoice_payment_term_id'))
			journal_id = self.find_journal(values.get('journal_id'))
			if values.get('date') == '':
				raise Warning(_('Please assign a date'))
			else:
				inv_date = self.find_invoice_date(values.get('date'))
			if values.get('date_due') == '':
				raise Warning(_('Please assign a date due'))
			else:
				inv_date_due = self.find_invoice_date(values.get('date_due'))

			if str(values.get('td')) == '':
				raise Warning(_('Please assign a Type Document.'))
			else:
				type_document_id = self.find_type_document(str(values.get('td')))

			if str(values.get('nro_comprobante')) == '':
				raise Warning(_('Please assign a Invoice Number.'))

			if str(values.get('glosa')) == '':
				raise Warning(_('Please assign a Glosa.'))

			if self.type == "in":
				type_inv = "out_invoice"
				if partner_id.property_account_receivable_id:
					account_id = partner_id.property_account_receivable_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_receivable_id')])
					account_id = account_search.value_reference
					if not account_id:
						raise UserError(_('Please define Customer account.'))
					account_id = account_id.split(",")[1]
					account_id = self.env['account.account'].browse(account_id)

			elif self.type == "out":
				type_inv = "in_invoice"
				if partner_id.property_account_payable_id:
					account_id = partner_id.property_account_payable_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_payable_id')])
					account_id = account_search.value_reference
					if not account_id:
						raise UserError(_('Please define Vendor account.'))
					account_id = account_id.split(",")[1]
					account_id = self.env['account.account'].browse(account_id)

			elif self.type == "cus_credit_note":
				type_inv = "out_refund"
				if partner_id.property_account_receivable_id:
					account_id = partner_id.property_account_receivable_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_receivable_id')])
					account_id = account_search.value_reference
					if not account_id:
						raise UserError(_('Please define Customer account.'))
					account_id = account_id.split(",")[1]
					account_id = self.env['account.account'].browse(account_id)
			else:
				type_inv = "in_refund"
				if partner_id.property_account_payable_id:
					account_id = partner_id.property_account_payable_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_payable_id')])
					account_id = account_search.value_reference
					if not account_id:
						raise UserError(_('Please define Vendor account.'))
					account_id = account_id.split(",")[1]
					account_id = self.env['account.account'].browse(account_id)
			inv_id = invoice_obj.create({
				'name': values.get('invoice') if self.sequence_opt == 'custom' else '/',
				'partner_id' : partner_id.id,
				'currency_id' : currency_id.id,
				'invoice_user_id':salesperson_id.id,
				'collection_id': collection_id.id,
				'custom_seq': True if self.sequence_opt == 'custom' else False,
				'system_seq': True if self.sequence_opt == 'system' else False,
				'type' : type_inv,
				'date':values.get('date'),
				'invoice_date_due': inv_date_due,
				'invoice_date':values.get('date_invoice'),
				'journal_id' : self.journal_id.id if not journal_id else journal_id.id,
				'invoice_name' : values.get('invoice'),
				'type_document_id' : type_document_id.id,
				'ref' : str(values.get('nro_comprobante')),
				'glosa': str(values.get('glosa')),
				'company_id' : self.env.company.id,
				'type_invoice': str(values.get('type_invoice')),
				'invoice_payment_term_id': invoice_payment_term_id.id,
				'currency_rate': float(values.get('currency_rate') if values.get('currency_rate') else 1),
			})
			if inv_id.currency_rate == 1 and inv_id.currency_id.name == 'USD':
				inv_id._get_currency_rate()
			self.make_invoice_line(values, inv_id)
			return inv_id

	def make_invoice_line(self, values, inv_id):
		product_obj = self.env['product.product']

		if self.import_prod_option == 'barcode':
			product_search = product_obj.search([('barcode', '=', values['product'])])
		elif self.import_prod_option == 'code':
			product_search = product_obj.search([('default_code', '=',values['product'])])
		else:
			product_search = product_obj.search([('name', '=',values['product'])])

		product_uom = self.env['uom.uom'].search([('name', '=', values.get('uom'))])
		if not product_uom:
			raise Warning(_(' "%s" Product UOM category is not available.') % values.get('uom'))

		if product_search:
			product_id = product_search
		else:
			if self.import_prod_option == 'name':
				product_id = product_obj.create({
													'name':values.get('product'),
													'lst_price':values.get('price'),
													'uom_id':product_uom.id,
												 })
			else:
				raise Warning(_('%s product is not found" .\n If you want to create product then first select Import Product By Name option .') % values.get('product'))

		tax_ids = []
		if inv_id.type == 'out_invoice':
			if values.get('tax'):
				if ';' in  values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)

				elif ',' in  values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)
				else:
					tax_names = values.get('tax').split(',')
					tax= self.env['account.tax'].search([('name', '=', tax_names),('type_tax_use','=','sale')])
					if not tax:
						raise Warning(_('"%s" Tax not in your system') % tax_names)
					tax_ids.append(tax.id)
		elif inv_id.type == 'in_invoice':
			if values.get('tax'):
				if ';' in values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)

				elif ',' in values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)
				else:
					tax_names = values.get('tax').split(',')
					tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
					if not tax:
						raise Warning(_('"%s" Tax not in your system') % tax_names)
					tax_ids.append(tax.id)
		elif inv_id.type == 'out_refund':
			if values.get('tax'):
				if ';' in  values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)

				elif ',' in  values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)
				else:
					tax_names = values.get('tax').split(',')
					tax= self.env['account.tax'].search([('name', '=', tax_names),('type_tax_use','=','sale')])
					if not tax:
						raise Warning(_('"%s" Tax not in your system') % tax_names)
					tax_ids.append(tax.id)
		else:
			if values.get('tax'):
				if ';' in values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)

				elif ',' in values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
						if not tax:
							raise Warning(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)
				else:
					tax_names = values.get('tax').split(',')
					tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
					if not tax:
						raise Warning(_('"%s" Tax not in your system') % tax_names)
					tax_ids.append(tax.id)

		if self.account_opt == 'default':
			if inv_id.type == 'out_invoice':
				if product_id.property_account_income_id:
					account = product_id.property_account_income_id
				elif product_id.categ_id.property_account_income_categ_id:
					account = product_id.categ_id.property_account_income_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_income_categ_id')])
					account = account_search[0].value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(int(account))
			if inv_id.type == 'in_invoice':
				if product_id.property_account_expense_id:
					account = product_id.property_account_expense_id
				elif product_id.categ_id.property_account_expense_categ_id:
					account = product_id.categ_id.property_account_expense_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id')])
					account = account_search[0].value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(int(account))

			if inv_id.type == 'out_refund':
				if product_id.property_account_income_id:
					account = product_id.property_account_income_id
				elif product_id.categ_id.property_account_income_categ_id:
					account = product_id.categ_id.property_account_income_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_income_categ_id')])
					account = account_search[0].value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(int(account))
			if inv_id.type == 'in_refund':
				if product_id.property_account_expense_id:
					account = product_id.property_account_expense_id
				elif product_id.categ_id.property_account_expense_categ_id:
					account = product_id.categ_id.property_account_expense_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id')])
					account = account_search[0].value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(int(account))

		else:
			if values.get('account') == '':
				raise Warning(_(' You can not left blank account field if you select Excel/CSV Account Option'))
			else:
				if self.import_option == 'csv':
					account_id = self.env['account.account'].search([('code','=',values.get('account'))])
				else:
					acc = values.get('account').split('.')
					account_id = self.env['account.account'].search([('code','=',acc[0])])
				if account_id:
					account = account_id
				else:
					raise Warning(_(' "%s" Account is not available.') % values.get('account'))

		vals = {
			'product_id' : product_id.id,
			'quantity' : values.get('quantity'),
			'price_unit' :values.get('price'),
			'discount':values.get('discount'),
			'name' : values.get('description'),
			'account_id' : account.id,
			'analytic_account_id':( self.env['account.analytic.account'].search([('name','=',values.get('analytic_account_id') )])[0].id if len(self.env['account.analytic.account'].search([('name','=',values.get('analytic_account_id') )]))>0 else  self.env['account.analytic.account'].create({'name':values.get('analytic_account_id')} )   ) if values.get('analytic_account_id') and values.get('analytic_account_id') != '' else False,
			'product_uom_id' : product_uom.id,
			'company_id' : self.env.company.id,
			'request_id': values.get('request_id'),
			'order_id': values.get('order_id'),
			'tc': float(values.get('currency_rate') if values.get('currency_rate') else 1),
		}
		if tax_ids:
			vals.update({'tax_ids':([(6,0,tax_ids)])})

		inv_id.write({'invoice_line_ids' :([(0,0,vals)]) })
		inv_id.write({'code_import_invoice': values.get("import_id")})

		return inv_id


	def find_currency(self, name):
		currency_obj = self.env['res.currency']
		currency_search = currency_obj.search([('name', '=', name)],limit=1)
		if currency_search:
			return currency_search
		else:
			raise Warning(_(' "%s" Currency are not available.') % name)


	def find_sales_person(self, name):
		sals_person_obj = self.env['res.users']
		partner_search = sals_person_obj.search([('name', '=', name)],limit=1)
		if partner_search:
			return partner_search
		else:
			raise Warning(_('Not Valid Salesperson Name "%s"') % name)

	def find_collection_person(self, name):
		collection_obj = self.env['res.users']
		partner_search = collection_obj.search([('name', '=', name)], limit=1)
		if partner_search:
			return partner_search
		else:
			raise Warning(_('Not Valid debt collector Name "%s"') % name)

	def find_invoice_payment_term(self, code):
		payment_term_obj = self.env['account.payment.term']
		payment_term_search = payment_term_obj.search([('code', '=', code)], limit=1)
		if payment_term_search:
			return payment_term_search
		else:
			raise Warning(_('Not Valid payment term Code "%s"') % code)

	def find_journal(self, code):
		journal_obj = self.env['account.journal']
		journal_search = journal_obj.search([('code', '=', code)], limit=1)
		if journal_search:
			return journal_search
		else:
			raise Warning(_('Not Valid journal Code "%s"') % code)

	def find_payment_request(self, name):
		if name:
			request_obj = self.env['fxo.payment.request']
			request_search = request_obj.search([('name', '=', name)], limit=1)
			if request_search:
				return request_search
			else:
				raise Warning(_('Not Valid payment request Name "%s"') % name)
		else:
			return None

	def find_order(self, name):
		if name:
			order_obj = self.env['sale.order']
			order_search = order_obj.search([('name', '=', name)], limit=1)
			if order_search:
				return order_search
			else:
				raise Warning(_('Not Valid sale order Name "%s"') % name)
		else:
			None

	def find_partner(self, name):
		partner_obj = self.env['res.partner']
		partner_search = partner_obj.search([('vat', '=', str(name))],limit=1)
		if partner_search:
			return partner_search
		else:
			raise Warning(_('No existe un Partner con el Nro de Documento "%s"') % name)

	def find_type_document(self,name):
		type_document_search = self.env['einvoice.catalog.01'].search([('code','=',str(name))],limit=1)
		if type_document_search:
			return type_document_search
		else:
			raise Warning(_('No existe un Tipo de Comprobante con el Codigo"%s"') % name)

	def find_invoice_date(self, date):
		DATETIME_FORMAT = "%Y-%m-%d"
		i_date = datetime.strptime(date, DATETIME_FORMAT).date()
		return i_date


	def import_csv(self):
		"""Load Inventory data from the CSV file."""
		if self.import_option == 'csv':
			if self.account_opt == 'default':
				keys = [
					'invoice', 'customer', 'currency', 'product', 'quantity', 'uom', 'description', 'price', 'discount', 'salesperson', 'tax', 'date',
					'date_invoice','date_due', 'td', 'nro_comprobante', 'glosa', 'analytic_account_id', 'collection_id', 'type_invoice', 'invoice_payment_term_id', 'journal_id',
					'currency_rate', 'request_id', 'order_id'
				]
			else:
				keys = [
					'invoice', 'customer', 'currency', 'product','account', 'quantity', 'uom', 'description', 'price','discount','salesperson','tax','date',
					'date_invoice','date_due', 'td', 'nro_comprobante', 'glosa', 'analytic_account_id', 'collection_id', 'type_invoice', 'invoice_payment_term_id', 'journal_id',
					'currency_rate', 'request_id', 'order_id'
				]

			try:
				csv_data = base64.b64decode(self.file)
				data_file = io.StringIO(csv_data.decode("utf-8"))
				data_file.seek(0)
				file_reader = []
				csv_reader = csv.reader(data_file, delimiter=',')
				file_reader.extend(csv_reader)
			except Exception:
				raise exceptions.Warning(_("Please select an CSV/XLS file or You have selected invalid file"))
			values = {}
			invoice_ids=[]
			for i in range(len(file_reader)):
				field = list(map(str, file_reader[i]))
				if self.account_opt == 'default':
					if len(field) > 24:
						raise Warning(_('Your File has extra column please refer sample file'))
					elif len(field) < 24:
						raise Warning(_('Your File has less column please refer sample file'))
				else:
					if len(field) > 25:
						raise Warning(_('Your File has extra column please refer sample file'))
					elif len(field) < 25:
						raise Warning(_('Your File has less column please refer sample file'))

				values = dict(zip(keys, field))
				if values:
					if i == 0:
						continue
					else:
						values.update({'type':self.type,'option':self.import_option,'seq_opt':self.sequence_opt})
						res = self.make_invoice(values)
						invoice_ids.append(res)

			if self.stage == 'confirm':
				for res in invoice_ids:
					if res.state in ['draft']:
						res.action_post()

		else:
			try:
				fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
				fp.write(binascii.a2b_base64(self.file))
				fp.seek(0)
				values = {}
				invoice_ids=[]
				workbook = xlrd.open_workbook(fp.name)
				sheet = workbook.sheet_by_index(0)
			except Exception:
				raise exceptions.Warning(_("Please select an CSV/XLS file or You have selected invalid file"))

			import_id = self.env['delete.account.move.import'].create({
						'date': fields.Date.context_today(self),
						'company_id':self.env.company.id
					})

			for row_no in range(sheet.nrows):
				val = {}
				if row_no <= 0:
					continue
				else:
					line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
					if self.account_opt == 'default':
						if len(line) == 25:
							if line[11] == '':
								raise Warning(_('Please assign a date'))
							else:
								a1 = int(float(line[11]))
								a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
								date_string = a1_as_datetime.date().strftime('%Y-%m-%d')

							if line[12] == '':
								raise Warning(_('Please assign a date invoice'))
							else:
								a2 = int(float(line[12]))
								a2_as_datetime = datetime(*xlrd.xldate_as_tuple(a2, workbook.datemode))
								date_due = a2_as_datetime.date().strftime('%Y-%m-%d')

							if line[13] == '':
								raise Warning(_('Please assign a date due'))
							else:
								a3 = int(float(line[13]))

								a3_as_datetime = datetime(*xlrd.xldate_as_tuple(a3, workbook.datemode))
								date_invoice = a3_as_datetime.date().strftime('%Y-%m-%d')

							values.update( {'invoice':line[0],
											'customer': str(line[1]),
											'currency': line[2],
											'product': line[3].split('.')[0],
											'quantity': line[4],
											'uom': line[5],
											'description': line[6],
											'price': line[7],
											'discount':line[8],
											'salesperson': line[9],
											'tax': line[10],
											'date': date_string,
											'date_due': date_due,
											'date_invoice':date_invoice,
											'seq_opt':self.sequence_opt,
											'td': str(line[14]),
											'nro_comprobante': str(line[15]),
											'glosa': str(line[16]),
											'analytic_account_id': str(line[17]),
											'collection_id': line[18],
											'type_invoice': line[19],
											'invoice_payment_term_id': line[20],
											'journal_id': line[21],
											'currency_rate': line[22],
											'request_id': line[23],
											'order_id': line[24],
											'import_id':import_id.id
											})
						elif len(line) > 24:
							raise Warning(_('Your File has extra column please refer sample file'))
						else:
							raise Warning(_('Your File has less column please refer sample file'))
					else:
						if len(line) == 25:
							if line[12] == '':
								raise Warning(_('Please assign a date'))
							else:
								a1 = int(float(line[12]))
								a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
								date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
							if line[13] == '':
								raise Warning(_('Please assign a date due'))
							else:
								a1 = int(float(line[13]))
								a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
								date_due = a1_as_datetime.date().strftime('%Y-%m-%d')
							values.update( {'invoice':line[0],
											'customer': str(line[1]),
											'currency': line[2],
											'product': line[3].split('.')[0],
											'account': line[4],
											'quantity': line[5],
											'uom': line[6],
											'description': line[7],
											'price': line[8],
											'discount':line[9],
											'salesperson': line[10],
											'tax': line[11],
											'date': date_string,
											'date_due': date_due,
											'seq_opt':self.sequence_opt,
											'td': str(line[14]),
											'nro_comprobante': str(line[15]),
											'glosa': str(line[16]),
											'analytic_account_id': str(line[17]),
											'collection_id': line[18],
											'type_invoice': line[19],
											'invoice_payment_term_id': line[20],
											'journal_id': line[21],
											'currency_rate': line[22],
											'request_id': line[23],
											'order_id': line[24],
											'import_id':import_id.id
											})
						elif len(line) > 25:
							raise Warning(_('Your File has extra column please refer sample file'))
						else:
							raise Warning(_('Your File has less column please refer sample file'))
					res = self.make_invoice(values)
					invoice_ids.append(res)

			if self.stage == 'confirm':
				for res in invoice_ids:
					if res.state in ['draft']:
						res.action_post()

			return res


	def download_auto(self):

		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_document?model=gen.invoice&id=%s'%(self.id),
			 'target': 'new',
			 }

