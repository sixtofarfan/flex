from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import *
from odoo.tools import float_round
from . import amount_to_text_es
class BillForm(models.Model):
	_inherit = 'account.bill.form'

	order_id = fields.Many2one('sale.order', string='Routing Order')
	type_interest = fields.Selection([
		('simple', 'Simple'),
		('compound', 'Compuesto'),
	], string='Tipo de Interes', default='simple')
	interest = fields.Float(string='Interes', compute='get_interest')
	interest_percent = fields.Float(string='Tasa de Interes')
	type_time = fields.Selection([
		('monthly', 'Mensual'),
		('yearly', 'Anual'),
	], string='Tipo de Tasa', default='monthly')
	type_freight = fields.Selection([
		('letter', 'Por Letra'),
		('total', 'Total'),
	], string='Tipo de Portes', default='letter')
	freight_interest = fields.Float(string='Portes')
	interest_time = fields.Integer(string='Tiempo')
	igv = fields.Float(string='IGV')
	multi_range_bill = fields.Text(string='Rango Multiple de Dias entre Letras', 
		help='Rango de Dias para multiples letras deben estar separados por comas')
	aceptation_date = fields.Date(string='Fecha de Aceptacion')
	avoid_days = fields.Boolean(string='Evitar Sabados y Domingos', default=True)

	@api.onchange('type_freight', 'freight_interest', 'bills_qty')
	def get_freight(self):
		for rec in self:
			if rec.bills_qty > 0:
				for line in rec.bill_ids:
					line.freight_interest = float_round(rec.freight_interest/rec.bills_qty, 2) if rec.type_freight == 'total' else rec.freight_interest

	@api.depends('bill_ids')
	def get_interest(self):
		for rec in self:
			if rec.bill_ids:
				rec.interest = sum(rec.bill_ids.mapped('interest'))
			else:
				rec.interest = 0

	@api.depends('bill_ids')
	def get_igv(self):
		for rec in self:
			if rec.bill_ids:
				rec.igv = sum(rec.bill_ids.mapped('igv'))
			else:
				rec.igv = 0

	@api.onchange('order_id')
	def refill_bill_lines(self):
		if self.order_id:
			for bill in self.bill_ids:
				bill.order_id = self.order_id

	@api.onchange('bills_qty', 'range_bill')
	def get_default_multi_range(self):
		if self.range_bill and self.bills_qty and self.bills_qty > 1:
			multi_range = ','.join([str(self.days_due_first)] + [str(self.range_bill)] * (self.bills_qty - 1))
			self.multi_range_bill = multi_range
		elif self.range_bill and self.bills_qty and self.bills_qty == 1:
			self.multi_range_bill = self.days_due_first

	def change_bill_date(self, bill_date_due):
		if self.avoid_days:
			return super(BillForm, self).change_bill_date(bill_date_due)
		else:
			return bill_date_due

	def update_multi_range(self):
		ranges = self.multi_range_bill.split(',')
		if len(ranges) != len(self.bill_ids):
			raise UserError('La cantidad de rangos debe ser igual a la cantidad de letras actuales')
		for c, bill in enumerate(self.bill_ids):
			if c == 0:
				bill_date_due = bill.bill_date_issue + timedelta(days=int(ranges[c]))
			else:
				bill_date_due = bill_date_due + timedelta(days=int(ranges[c]))
			bill_date_due = self.change_bill_date(bill_date_due)
			bill.bill_date_due = bill_date_due

	def get_aceptation_wizard(self):
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'aceptation.wizard',
			'views': [(False, 'form')],
			'context': self._context,
			'target': 'new',
		}

	def update_bills(self):
		# Validaciones
		# Cantidad de letras
		if self.bills_qty <=0:
			raise UserError (_('Please enter bills quantity.'))
		# Fecha de la primera letra
		if self.days_due_first <=0:
			raise UserError (_('Please enter expiration days for first bill.'))
		# Rango 
		if self.range_bill <=0:
			raise UserError (_('Please enter range between bills.'))
		# Limpiar las antiguas y preparar las nuevas letras
		self.bill_ids.unlink()
		# if self.bill_ids:
		#     for bill in self.bill_ids:
		#         self.bill_ids = [(2, bill.id, False)]
		self.update_form()
		if self.total_invoices:
			# Obtener el tipo de cambio para la fecha de intercambio de letras
			self.onchange_currency_id()
			# Obtener el diario y las cuentas desde la configuración
			# if self.invoice_ids[0].type == 'out_invoice':
			#     # Obtener la cuenta de letras de cliente desde la configuración
			#     params = self.env['ir.config_parameter'].sudo()
			#     customer_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.customer_boe_journal_id'))
			#     self.journal_id = self.env['account.journal'].search([('id','=',customer_boe_journal_id)])
			# else:
			#     # Obtener la cuenta de letras de proveedor desde la configuración
			#     params = self.env['ir.config_parameter'].sudo()
			#     supplier_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.supplier_boe_journal_id'))
			#     self.journal_id = self.env['account.journal'].search([('id','=',supplier_boe_journal_id)])
			# if not self.journal_id:
			#     raise UserError('You must configure the Bill of Exchange Journal in settings.')
			if self.total_invoices > 0:
				bill_date_due = datetime.strptime(str(self.exchange_date), '%Y-%m-%d') + timedelta(days=(self.days_due_first))  
				# Cambia la fecha para evitar sabados, domingos y feriados.
				bill_date_due_changed = self.change_bill_date(bill_date_due)
				total_invoices = self.total_invoices - self.total_retention
				bill_amount = float_round((self.total_invoices - self.total_retention) / self.bills_qty,2)
				bill_amount_signed = float_round(bill_amount * self.exchange_rate, 2)
				interest_amount = round((self.interest) / self.bills_qty,2)
				aux = bill_amount
				result = []
				result.append((0, 0,
				{'bill_date_due':bill_date_due_changed,
				'bill_date_issue':self.exchange_date,
				'bill_form_id':self.id,
				'responsable_id':self.partner_id.id,
				'guarantee_id':self.guarantee_id.id,
				'acceptor_id':(self.acceptor_id.id if self.acceptor_id else self.partner_id.id) if self.invoice_ids[0].type == 'out_invoice' else self.env.company.partner_id.id,
				'bill_currency_id':self.currency_id.id,
				'bill_amount_total':bill_amount,
				'interest': interest_amount,
				'interest_time': self.days_due_first,
				'freight_interest': float_round(self.freight_interest/self.bills_qty, 2) if self.type_freight == 'total' else self.freight_interest,
				'bill_amount_total_signed':bill_amount * self.exchange_rate,
				'exchange_rate':self.exchange_rate,
				'account_id': self.journal_id.default_debit_account_id.id, # if self.invoice_ids[0].type == 'out_invoice' else self.journal_id.default_credit_account_id.id,
				'type_bill': 'receivable' if self.invoice_ids[0].type == 'out_invoice' else 'payable',
				'amount_text':amount_to_text_es.amount_to_text(bill_amount, self.currency_id.name),
				'order_id': self.order_id.id if self.order_id else None,
				}))
				for i in range(1, self.bills_qty):
					bill_date_due = bill_date_due + timedelta(days=(self.range_bill))
					# Cambia la fecha para evitar sabados, domingos y feriados.
					bill_date_due_changed = self.change_bill_date(bill_date_due) 
					if result[len(result)-1][2]['bill_date_due'] >= bill_date_due_changed:
						if result[len(result)-1][2]['bill_date_due'] == bill_date_due:
							bill_date_due_changed = self.with_context(foward=True).change_bill_date(result[len(result)-1][2]['bill_date_due'] + timedelta(days=(self.range_bill)))
							bill_date_due = bill_date_due_changed
						else:
							bill_date_due_changed = self.with_context(foward=True).change_bill_date(result[len(result)-1][2]['bill_date_due'] + timedelta(days=(1)))
					if i == self.bills_qty - 1:
						bill_amount = total_invoices - aux
					else:
						aux += bill_amount
					bill_amount_signed = float_round(bill_amount * self.exchange_rate, 2)
					result.append((0, 0,
					{'bill_date_due':bill_date_due_changed,
					'bill_date_issue':self.exchange_date,
					'bill_form_id':self.id,
					'responsable_id':self.partner_id.id,
					'guarantee_id':self.guarantee_id.id,
					'acceptor_id':(self.acceptor_id.id if self.acceptor_id else self.partner_id.id) if self.invoice_ids[0].type == 'out_invoice' else self.env.company.partner_id.id,
					'bill_currency_id':self.currency_id.id,
					'bill_amount_total':bill_amount,
					'interest': interest_amount,
					'interest_time': self.days_due_first,
					'freight_interest': float_round(self.freight_interest/self.bills_qty, 2) if self.type_freight == 'total' else self.freight_interest,
					'bill_amount_total_signed':bill_amount * self.exchange_rate,
					'exchange_rate':self.exchange_rate,
					'account_id':self.journal_id.default_debit_account_id.id, # if self.invoice_ids[0].type == 'out_invoice' else self.journal_id.default_credit_account_id.id,
					'type_bill': 'receivable' if self.invoice_ids[0].type == 'out_invoice' else 'payable',
					'amount_text':amount_to_text_es.amount_to_text(bill_amount, self.currency_id.name),
					'order_id': self.order_id.id if self.order_id else None,
					}))

				self.bill_ids = result
			for bill in self.bill_ids:
				bill.account_id = self.journal_id.default_debit_account_id
			self.update_sequence_final()