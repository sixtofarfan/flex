from odoo import models, fields, api, _
from datetime import *
from odoo.exceptions import UserError
from odoo.tools import float_round

class AdvancedBillForm(models.Model):
	_inherit = 'account.advanced.bill.form'

	order_id = fields.Many2one('sale.order', string='Routing Order')
	interest = fields.Float(string='Interes', compute='get_interest')
	interest_percent = fields.Float(string='Tasa de Interes')
	freight_interest = fields.Float(string='Portes')
	interest_time = fields.Integer(string='Tiempo')
	igv = fields.Float(string='IGV', compute='get_igv')
	type_interest = fields.Selection([
		('simple', 'Simple'),
		('compound', 'Compuesto'),
	], string='Tipo de Interes', default='simple')
	type_time = fields.Selection([
		('monthly', 'Mensual'),
		('yearly', 'Anual'),
	], string='Tipo de Tasa', default='monthly')
	type_freight = fields.Selection([
		('letter', 'Por Letra'),
		('total', 'Total'),
	], string='Tipo de Portes', default='letter')
	multi_range_bill = fields.Text(string='Rango Multiple de Dias entre Letras', 
		help='Rango de Dias para multiples letras deben estar separados por comas')
	aceptation_date = fields.Date(string='Fecha de Aceptacion', default=fields.Date.today())
	avoid_days = fields.Boolean(string='Evitar Sabados y Domingos', default=True)

	@api.onchange('type_freight', 'freight_interest', 'bills_qty')
	def get_freight(self):
		for rec in self:
			if rec.bills_qty > 0:
				for line in rec.bill_ids:
					line.freight_interest = float_round(rec.freight_interest/rec.bills_qty, 2) if rec.type_freight == 'total' else rec.freight_interest

	@api.onchange('bills_qty', 'range_bill')
	def get_default_multi_range(self):
		if self.range_bill and self.bills_qty and self.bills_qty > 1:
			multi_range = ','.join([str(self.days_due_first)] + [str(self.range_bill)] * (self.bills_qty - 1))
			self.multi_range_bill = multi_range
		elif self.range_bill and self.bills_qty and self.bills_qty == 1:
			self.multi_range_bill = self.days_due_first

	def change_bill_date(self, bill_date_due):
		if self.avoid_days:
			return super(AdvancedBillForm, self).change_bill_date(bill_date_due)
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
	@api.constrains('order_id','bill_form_id')
	def update_order_id_move(self):
		if self.order_id and self.bill_form_id :
			for bill in self.bill_form_id.account_move_line_ids:
				bill.order_id = self.order_id

	@api.onchange('order_id')
	def refill_bill_lines(self):
		if self.order_id:
			for bill in self.bill_ids:
				bill.order_id = self.order_id

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
		# self.update_form()
		if self.advanced_amount:
			# Obtener el tipo de cambio para la fecha de intercambio de letras
			self.onchange_currency_id()
			if self.advanced_amount > 0:
				bill_date_due = datetime.strptime(str(self.exchange_date), '%Y-%m-%d') + timedelta(days=(self.days_due_first))
				# Cambia la fecha para evitar sabados, domingos y feriados.
				bill_date_due_changed = self.change_bill_date(bill_date_due)
				advanced_amount = self.advanced_amount - self.total_retention
				bill_amount = round((self.advanced_amount - self.total_retention) / self.bills_qty,2)
				interest_amount = round((self.interest) / self.bills_qty,2)
				bill_amount_signed = round(round(bill_amount * self.exchange_rate,3), 2)
				aux = bill_amount
				result = []
				result.append((0, 0, {
					'bill_date_due':bill_date_due_changed,
					'bill_date_issue':self.exchange_date,
					# 'responsable_id':self.partner_id.name,
					'guarantee_id':self.guarantee_id.name,
					# 'acceptor_id':self.acceptor_id.name if self.acceptor_id else self.partner_id.name,
					'responsable_id': self.partner_id.name if self._context.get('type_import') == '1' else self.env.company.partner_id.name,
					'acceptor_id': (self.acceptor_id.name if self.acceptor_id else self.partner_id.name) if self._context.get('type_import') == '1' else self.env.company.partner_id.name,
					'bill_currency_id':self.currency_id.name,
					'capital': bill_amount,
					'bill_amount_total':bill_amount,
					'interest': interest_amount,
					'interest_time': self.days_due_first,
					'freight_interest': float_round(self.freight_interest/self.bills_qty, 2) if self.type_freight == 'total' else self.freight_interest,
					'bill_amount_total_signed': bill_amount_signed,
					'exchange_rate':self.exchange_rate,
					'account_id': self.journal_id.default_debit_account_id.code, # if self._context.get('type_import') == '1' else self.journal_id.default_credit_account_id.code,
					'type_bill': 'receivable' if self._context.get('type_import') == '1' else 'payable',
					'order_id': self.order_id.id if self.order_id else None,
				}))
				multi_range = self.multi_range_bill.split(',')
				aux2 = self.days_due_first
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
						bill_amount = advanced_amount - aux
					else:
						aux += bill_amount
					bill_amount_signed = round(round(bill_amount * self.exchange_rate,3),2)
					result.append((0, 0,
					{'bill_date_due':bill_date_due_changed,
					'bill_date_issue':self.exchange_date,
					# 'responsable_id':self.partner_id.name,
					'guarantee_id':self.guarantee_id.name,
					# 'acceptor_id':self.acceptor_id.name if self.acceptor_id else self.partner_id.name,
					'responsable_id': self.partner_id.name if self._context.get('type_import') == '1' else self.env.company.partner_id.name,
					'acceptor_id': (self.acceptor_id.name if self.acceptor_id else self.partner_id.name) if self._context.get('type_import') == '1' else self.env.company.partner_id.name,
					'bill_currency_id':self.currency_id.name,
					'capital': bill_amount,
					'bill_amount_total':bill_amount,
					'interest': interest_amount,
					'interest_time': int(multi_range[i]) + aux2,
					'freight_interest': float_round(self.freight_interest/self.bills_qty, 2) if self.type_freight == 'total' else self.freight_interest,
					'bill_amount_total_signed':bill_amount_signed,
					'exchange_rate':self.exchange_rate,
					'account_id':self.journal_id.default_debit_account_id.code, # if self._context.get('type_import') == '1' else self.journal_id.default_credit_account_id.code,
					'type_bill': 'receivable' if self._context.get('type_import') == '1' else 'payable',
					'order_id': self.order_id.id if self.order_id else None,
					}))
					aux2 += int(multi_range[i])

				self.bill_ids = result
			self.update_sequence_final()

	def get_aceptation_wizard(self):
		
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'aceptation.wizard',
			'views': [(False, 'form')],
			'context': self._context,
			'target': 'new',
		}

	def process(self):
		# if self.partner_id:
		#     if any(line.acceptor_id != self.partner_id.name for line in self.bill_ids):
		#         raise UserError(_('If you selected a partner, every line should be the same partner.'))
		vals=[]
		vals_aml=[]
		msg = ''
		account_move_id = self.env['account.move'].create({
			'name': self.name,
			'currency_id': self.currency_id.id,
			'partner_id': self.partner_id.id,
			'date': self.exchange_date,
			'currency_rate': self.exchange_rate,
			'invoice_date': self.exchange_date,
			'journal_id': self.journal_id.id,
			'glosa': self.gloss,
			'type': 'bill',
		})
		form_id = self.env['account.bill.form'].create({
			'account_move': account_move_id.id,
			'exchange_date': self.exchange_date,
			'journal_id': self.journal_id.id,
			'advanced_bill_form_id': self.id,
			'currency_id': self.currency_id.id,
			'exchange_rate': self.exchange_rate,
			'state':'advanced',
			'gloss': self.gloss,
			'type_form': self._context.get('type_import'),
			'partner_id': self.partner_id.id,
			'order_id': self.order_id.id,
			'interest_percent': self.interest_percent,
			'freight_interest': self.freight_interest,
			'interest_time': self.interest_time,
			'type_interest': self.type_interest,
			'type_time': self.type_time,
			'type_freight': self.type_freight,
			'bills_qty': self.bills_qty,
			'days_due_first': self.days_due_first,
			'range_bill': self.range_bill,
			'multi_range_bill': self.multi_range_bill,
			'aceptation_date': self.aceptation_date,
			'igv': self.igv,
		})
		self.bill_form_id = form_id
		if not self.bill_ids:
			raise UserError(_('There is no bill lines, update first enter them manually or import.'))
		for line in self.bill_ids:
			if line.responsable_id:
				responsable_id = self.env['res.partner'].search([('name', '=', line.responsable_id)])
				if not responsable_id:
					msg += 'The responsable partner ' + line.responsable_id + ' doesn\'t exist in the database\n'
			if line.acceptor_id:
				acceptor_id = self.env['res.partner'].search([('name', '=', line.acceptor_id)])
				if not acceptor_id:
					msg += 'The acceptor partner ' + line.acceptor_id + ' doesn\'t exist in the database\n'
			else:
				msg += 'The acceptor partner doesn\'t exist in the database\n'
			if line.guarantee_id:
				guarantee_id = self.env['res.partner'].search([('name', '=', line.guarantee_id)])
				if not guarantee_id:
					msg += 'The guarantee partner ' + line.guarantee_id + ' doesn\'t exist in the database\n'
			if line.account_id:
				account_id = self.env['account.account'].search([('code', '=', line.account_id), ('company_id', '=', self.env.company.id)])
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
			val = {
				'bill_number': line.bill_number,
				'bank_number': line.bank_number,
				'account_id': account_id.id,
				'responsable_id': responsable_id.id,
				'acceptor_id': acceptor_id.id,
				'guarantee_id': guarantee_id.id if line.guarantee_id else False,
				'bill_date_issue': line.bill_date_issue,
				'bill_date_due': line.bill_date_due,
				'bill_currency_id': self.currency_id.id,
				'capital': line.capital,
				'exchange_rate': line.exchange_rate,
				'state_of_bill': 'portfolio' if self._context.get('type_import') == '1' else 'accepted',
				'type_bill': 'receivable' if self._context.get('type_import') == '1' else 'payable',
				'is_advanced_payment': True,
				'order_id': line.order_id.id,
				'internal_ref': line.internal_ref,
				'interest_time': line.interest_time,
				'freight_interest': line.freight_interest,
			}
			val.update({'bill_form_id': form_id.id})
			vals.append(val)
			# Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
			type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
			if len(type_document_id) > 1:
				raise UserError('Se ha encontrado mas de un tipo de documento LE revise los tipos de documento del catalogo 01')
			val = {
				'bill_form_id': form_id.id,
				'ref': self.import_number,
				'move_id': account_move_id.id,
				'partner_id': self.partner_id.id,
				'type_document_id': type_document_id.id,
				'nro_comp': line.bill_number,
				'exchange_rate': line.exchange_rate,
				'name': line.bill_number,
				'date': line.bill_date_issue, #self.exchange_date,
				'journal_id': self.journal_id.id,
				'company_id': self.company_id.id,
				'currency_id': self.currency_id.id if self.currency_id != self.env.company.currency_id else False,
				'company_currency_id': self.company_currency_id.id,
				'account_id': self.journal_id.default_debit_account_id.id, 
				'amount_currency': line.bill_amount_total * (1.0 if self._context.get('type_import') == '1' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0,
				'tc': line.exchange_rate,
				'balance': float_round(line.bill_amount_total * (line.exchange_rate if line.exchange_rate > 0 else 1),2) * (1.0 if self._context.get('type_import') == '1' else -1.0),
				'debit': float_round(line.bill_amount_total * (line.exchange_rate if line.exchange_rate > 0 else 1),2) if self._context.get('type_import') == '1' else 0,
				'credit': 0 if self._context.get('type_import') == '1' else float_round(line.bill_amount_total * (line.exchange_rate if line.exchange_rate > 0 else 1),2),
				'date_maturity': line.bill_date_due,
				}
			vals_aml.append(val)
		if self.currency_id == self.env.company.currency_id:
			advanced_amount_signed = float_round(sum(self.bill_ids.mapped('bill_amount_total')), 2)
		else:
			advanced_amount_signed = float_round(sum(self.bill_ids.mapped('bill_amount_total_signed')), 2)
		# Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
		type_document_id = self.env['einvoice.catalog.01'].search([('code','=','00')])
		val = {
			'bill_form_id': form_id.id,
			'ref': self.import_number,
			'move_id': account_move_id.id,
			'partner_id': self.partner_id.id,
			'type_document_id': type_document_id.id,
			'nro_comp': self.import_number if self._context.get('type_import') == '1' else self.name, # self.name + (_(' Import N° ') + self.import_number if self.import_number else ''),#line.bill_number,
			'exchange_rate': line.exchange_rate,
			'name': _('Advanced bills') + (' for import N° ' + self.import_number if self.import_number else ''),
			'import_number': self.import_number,
			'date': self.exchange_date,
			'journal_id': self.journal_id.id,
			'company_id': self.company_id.id,
			'currency_id': self.currency_id.id if self.currency_id != self.env.company.currency_id else False,
			'company_currency_id': self.company_currency_id.id,
			'account_id': self.bridge_account_id.id,
			'amount_residual': advanced_amount_signed * (-1.0 if self._context.get('type_import') == '1' else 1.0),
			'amount_residual_currency': self.advanced_amount * (-1.0 if self._context.get('type_import') == '1' else 1.0),
			'amount_currency': self.advanced_amount * (-1.0 if self._context.get('type_import') == '1' else 1.0) if self.company_currency_id.id != self.currency_id.id else 0,
			'tc': line.exchange_rate,
			'balance': advanced_amount_signed * (-1.0 if self._context.get('type_import') == '1' else 1.0),
			'credit': advanced_amount_signed if self._context.get('type_import') == '1' else 0,
			'debit': 0 if self._context.get('type_import') == '1' else advanced_amount_signed,
			'date_maturity': self.exchange_date,
			}
		vals_aml.append(val)
		if self.currency_id != self.company_currency_id:
			# Diferencia por redondeo
			# Obtener el diario y las cuentas de redondeo desde la configuración
			params = self.env['ir.config_parameter'].sudo()
			round_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.round_boe_journal_id'))
			round_journal = self.env['account.journal'].search([('id','=',round_boe_journal_id)])
			#total_amount_currency = sum(item['debit'] if self._context.get('type_import') == '1' else item['credit'] for item in vals_aml)
			#total_debit = sum(item['amount_currency'] if item['credit'] else 0 for item in vals_aml) if self._context.get('type_import') == '1' else sum(item['amount_currency'] if item['debit'] else 0 for item in vals_aml)
			#difference = abs(total_amount_currency) - abs(float_round(total_debit * self.exchange_rate, 2))
			total_debit = sum(v['debit'] for v in vals_aml)
			total_credit = sum(v['credit'] for v in vals_aml)
			difference = total_credit - total_debit

			for i in range(8,1,-1):
				difference = round(difference,i)

			if float_round(difference,2) < 0:
				# Asiento de diferencia por redondeo ganancia
				val = {
					'bill_form_id': form_id.id,
					'name': _('Currency round difference'),
					'debit': 0,#float_round(abs(difference),2) if self._context.get('type_import') == '1' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
					'credit': float_round(abs(difference),2),#0.0 if self._context.get('type_import') == '1' else float_round(abs(difference),2), #if self.invoice_ids[0].type == 'out_invoice' else float_round(abs(total_debit - total_credit),2),
					'account_id': round_journal.default_debit_account_id.id if self._context.get('type_import') == '1' else round_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
					'move_id': account_move_id.id,
					'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
					'amount_currency': float_round(abs(difference) / self.exchange_rate,2) * (1.0 if self._context.get('type_import') == '1' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
					'balance': float_round(abs(difference),2) * (1.0 if self._context.get('type_import') == '1' else -1.0), # if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
					}
				vals_aml.append(val)
			if float_round(difference,2) > 0:
				# Asiento de diferencia por redondeo perdida
				val = {
					'bill_form_id': form_id.id,
					'name': _('Currency round difference'),
					'debit': float_round(abs(difference),2),#0.0 if self._context.get('type_import') == '1' else abs(float_round(difference,2)), #if self.invoice_ids[0].type == 'out_invoice' else abs(float_round(total_debit - total_credit,2)),
					'credit': 0,#abs(float_round(difference,2)) if self._context.get('type_import') == '1' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
					'account_id': round_journal.default_credit_account_id.id if self._context.get('type_import') == '1' else round_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
					'move_id': account_move_id.id,
					'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
					'amount_currency': float_round(abs(difference) / self.exchange_rate,2) * (-1 if self._context.get('type_import') == '1' else 1) if self.company_currency_id.id != self.currency_id.id else 0.00,
					'balance': float_round(abs(difference),2) * (-1 if self._context.get('type_import') == '1' else 1), # if self.company_currency_id.id != self.currency_id.id else 0.00,
					}
				vals_aml.append(val)
		self.env['account.move.line'].create(vals_aml)
		# Forzamos la fecha de las lineas de la letra
		# TODO al crear el asiento se cambia la fecha de la linea
		# por la fecha del asiento
		for line in account_move_id.line_ids:
			for bill in self.bill_ids:
				line.date = bill.bill_date_issue if line.name == bill.bill_number else self.exchange_date
		account_move_id.post()
		for line in account_move_id.line_ids:
			line.amount_residual = line.balance
			line.amount_residual_currency = line.amount_currency
		bill_ids = self.env['account.bill'].create(vals)
		self.bill_form_id.bill_ids = [(6,0, bill_ids.ids)]
		self.state = 'done'
		self.update_order_id_move()

class AdvancedBillLines(models.Model):
	_inherit = 'advanced.bill.lines'

	order_id = fields.Many2one('sale.order', string='Routing Order')
	internal_ref = fields.Char(related='order_id.internal_ref', string='Referencia Interna')
	interest = fields.Float(string='Interes', compute='get_interest')
	interest_time = fields.Integer(string='Tiempo')
	freight_interest = fields.Float(string='Portes')
	igv = fields.Float(string='IGV', compute='get_igv')
	capital = fields.Float(string='Capital')
	bill_amount_total = fields.Float(compute='get_advanced_amount')
	bill_amount_total_signed = fields.Float(compute='compute_total_signed')

	amount_text = fields.Text(string='Amount Text', compute='_get_amount_text')
	symbol = fields.Char(string='Simbolo', compute='_get_currency_symbol')

	@api.depends('bill_currency_id')
	def _get_currency_symbol(self):
		for rec in self:
			if rec.bill_currency_id:
				currency = self.env['res.currency'].search([('name', '=', rec.bill_currency_id)])
				rec.symbol = currency.symbol

	@api.depends('bill_amount_total')
	def _get_amount_text(self):
		for bill in self:
			bill_currency_id = self.env['res.currency'].search([('name', '=', bill.bill_currency_id)])
			if bill.bill_amount_total<2 and bill.bill_amount_total>=1:
				currency_name = bill_currency_id.singular_name or bill_currency_id.plural_name or bill_currency_id.name or ""
			else:
				currency_name = bill_currency_id.plural_name or bill_currency_id.name or ""
			fraction_name = bill_currency_id.fraction_name or ""
			amount_text = bill_currency_id.amount_to_text(bill.bill_amount_total)
			bill.amount_text = amount_text

	@api.depends('interest', 'freight_interest')
	def get_igv(self):
		for rec in self:
			rec.igv = (rec.interest + rec.freight_interest) * 0.18

	@api.depends('bill_amount_total', 'advanced_form_id.interest_percent', 'advanced_form_id.type_time', 'interest_time')
	def get_interest(self):
		ReportBase = self.env['report.base']
		for rec in self:
			if rec.advanced_form_id.type_time == 'yearly':
				rec.interest = ReportBase.custom_round(((1 + rec.advanced_form_id.interest_percent/100) ** (rec.interest_time/360) - 1) * rec.capital, 2)
			else:
				rec.interest = ReportBase.custom_round(((1 + rec.advanced_form_id.interest_percent/100) ** (rec.interest_time/30) - 1) * rec.capital, 2)

	@api.depends('capital', 'interest', 'advanced_form_id.type_freight', 'freight_interest', 'igv', 'advanced_form_id.bills_qty')
	def get_advanced_amount(self):
		self.get_interest()
		for rec in self:
			rec.bill_amount_total = rec.capital + rec.igv + rec.interest + rec.freight_interest
	
	@api.depends('bill_amount_total','exchange_rate')
	def compute_total_signed(self):
		for rec in self:
			if rec.bill_currency_id != rec.env.company.currency_id.name:
				rec.bill_amount_total_signed = rec.bill_amount_total * rec.exchange_rate
			else:
				rec.bill_amount_total_signed = rec.bill_amount_total
