from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
# from . import amount_to_text_es
from datetime import datetime, timedelta, date
# from pytz import timezone, UTC
from odoo.tools import float_round

class SendToBank(models.Model):
    _name = 'account.send.bank'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Send Bills to Bank'
    _order = 'send_date desc'

    name = fields.Char('Form number', copy=False, readonly=True, default=(lambda x: _('New')))
    journal_id = fields.Many2one('account.journal', string='Bill Journal', required = True, tracking=True)
    send_date = fields.Date(string='Send Date', default=fields.Date.context_today, required = True, tracking=True)
    gloss = fields.Char('Gloss')
    # Se puede agregar mas posiciones si el cliente lo solicita
    # Por ahora solo Cobranza, Descuento y Garantía
    bank_position = fields.Selection(string='Bank Position', selection=[('collection', 'Collection'), ('discount', 'Discount'), ('guarantee', 'Guarantee'),], tracking=True)
    bill_ids = fields.Many2many('account.bill', string='Bills of Exchange', tracking=True)
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.company),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, states={'draft': [('readonly', False)]},string='Currency',default=(lambda self: self.env.user.company_id.currency_id))
    state = fields.Selection(string='State of form', selection=[('draft', 'Draft'),('to_reconcile', 'To Reconcile'),('to_disburse', 'To Disburse'),('sent', 'Sent'),('disbursed', 'Disbursed'),('imported', 'Imported'),], default='draft', tracking=True)
    account_move_line_ids = fields.One2many('account.move.line', 'send_form_id', string='Account move lines')
    account_move = fields.Many2one('account.move', 'Account Move')
    custom_exchange_rate = fields.Boolean(string='Custom Exchange Rate')
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1, tracking=True)
    bank_disbursement_id = fields.Many2one('account.bank.disbursement', string='Bank Disbursement')
    is_discount = fields.Boolean(string='Is Discount?', default=False)
    # disbursement_date = fields.Date(string='Disbursement Date', default=False, tracking=True)
    # disbursement_amount = fields.Monetary(string='Disbursement Amount', currency_field='currency_id', default=0)
    # disbursement_interests = fields.Monetary(string='Bank Interests', currency_field='currency_id', default=0)
    # financial_expenses = fields.Monetary(string='Financial Expenses', currency_field='currency_id', default=0)
    bill_form_ids = fields.Many2many('account.bill.form', string='Bill Forms')
    bill_refinancing_form_ids = fields.Many2many('account.refinancing.form', string='Bill Refinancing Forms')
    interest_rate = fields.Float(string='Interest Rate (%)', digits=(12, 2))

    @api.onchange('gloss')
    def _onchange_gloss(self):
        self.account_move.glosa = self.gloss
        if self.bank_disbursement_id:
            self.bank_disbursement_id.account_move.glosa = self.gloss

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.bank_position = self.journal_id.bank_position

    def get_exchange_rate(self, amount, currency, company, date):
        return self.currency_id._convert(amount, currency, company, date, False)

    def get_rates(self, date):
        exchange_rate = self.exchange_rate
        if not self.custom_exchange_rate:
            if self.currency_id.id == self.company_currency_id.id:
                exchange_rate = 1
            else:
                exchange_rate = float_round(self.get_exchange_rate(1, self.company_id.currency_id, self.company_id, date or fields.Date.context_today),3)
        return exchange_rate

    @api.onchange('currency_id','send_date','custom_exchange_rate')
    def onchange_currency_id(self):
        if self.currency_id != self.env.user.company_id.currency_id:
            rates = self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id),('name','=',self.send_date or fields.Date.context_today)])
            if not rates:
                raise UserError(_('There is no exchange rate for that date. All the journal entries will be calculated with this rate %s') %self.exchange_rate)
        self.exchange_rate = self.get_rates(self.send_date)

    @api.onchange('bank_position')
    def onchange_bank_position(self):
        self.bank_disbursement_id = ''
        self.is_discount = False

    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('account.send.bank') or _('New')
        return super(SendToBank, self).create(values)

    def unlink(self):
        for send_form in self:
            if send_form.state != 'draft' and not self._context.get('force_delete'):
                raise UserError(_("You cannot delete a form in %s state.") %send_form.state)
            for bill in self.bill_ids:
                send_form.bill_ids = [(3, bill.id)]
        return super(SendToBank, self).unlink()

    def action_send_to_bank(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        bill_ids = self.env['account.bill'].search([('id','in',active_ids.ids)])
        currency_id = bill_ids[0].bill_currency_id
        if any(x.bill_currency_id != currency_id for x in bill_ids):
            raise UserError(_("You can only send bills with the same currency."))
        return {
            'name': _('Send to bank Form'),
            'res_model': 'account.send.bank.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jp_account_bills_of_exchange.view_send_to_bank_wizard').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def process(self):
        if any(x.state_of_bill != 'portfolio' for x in self.bill_ids):
            raise UserError(_("You can't send this bills because they are not in portfolio."))
        if not self.bank_position:
            raise UserError(_('Select a bank position.'))
        if self.state != 'draft':
            raise UserError(_('You can\'t process a form in %s state.' %self.state))
        #if self.interest_rate == 0:
        #    raise UserError(_('The Bank interest rate can\'t be 0.'))
        if self.bank_position == 'discount':
            self.is_discount = True
        # if self.bank_position in ['collection','guarantee']:
        val = {}
        vals = []
        val = {
            'name': self.name,
            'currency_id': self.currency_id.id,
            'currency_rate': self.exchange_rate,
            'date': self.send_date,
            'invoice_date': self.send_date,
            'journal_id': self.journal_id.id,
            'glosa': self.gloss,
            'type': 'bill',
        }
        if not self.account_move:
            self.account_move = self.env['account.move'].create(val)
        exchange_rate = self.exchange_rate #if self.custom_exchange_rate else self.get_rates(self.send_date)
        # Letra
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
        for bill in self.bill_ids:
            bill_amount = bill.bill_amount_total
            bill_amount_signed = float_round(bill.bill_amount_total * exchange_rate,2)
            val = {
                # 'ref': self.name,
                'send_form_id': self.id,
                'move_id': self.account_move.id,
                'partner_id': bill.acceptor_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': bill.bill_number,
                # Este campo es para mostrar el tipo de cambio de la letra sin mostrar 
                # los apuntes contables en lugar de utilizar el campo bill_id
                'exchange_bill_id': bill.id,
                'exchange_rate': exchange_rate,
                'name': bill.bill_number, #_('Bill in portfolio') + ' ' + bill.bill_number,
                'date': bill.bill_date_issue, #self.send_date,
                'journal_id': bill.bill_form_id.journal_id.id,
                'currency_id': bill.bill_currency_id.id if bill.company_currency_id.id != bill.bill_currency_id.id else False,
                'company_id': bill.company_id.id,
                'company_currency_id': bill.company_currency_id.id,
                'account_id': bill.account_id.id,
                'debit': 0,
                'amount_currency': bill_amount * -1 if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
                'tc': exchange_rate,
                'balance': bill_amount_signed * -1, # if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
                'credit': bill_amount_signed,
                'date_maturity': bill.bill_date_due,
            }
            vals.append(val)
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
        for bill in self.bill_ids:
            bill_amount = bill.bill_amount_total
            bill_amount_signed = float_round(bill.bill_amount_total * exchange_rate,2)
            val = {
                # 'ref': self.name,
                'send_form_id': self.id,
                'move_id': self.account_move.id,
                'partner_id': bill.acceptor_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': bill.bill_number,
                # Este campo es para mostrar el tipo de cambio de la letra sin mostrar 
                # los apuntes contables en lugar de utilizar el campo bill_id
                'exchange_bill_id': bill.id, 
                'exchange_rate': exchange_rate,
                'name': bill.bill_number, #_('Bill in') + ' ' + dict(self._fields['bank_position'].selection).get(self.bank_position) + ' ' +  bill.bill_number,
                'date': self.send_date,
                'journal_id': self.journal_id.id,
                'currency_id': bill.bill_currency_id.id if bill.company_currency_id.id != bill.bill_currency_id.id else False,
                'company_id': bill.company_id.id,
                'company_currency_id': bill.company_currency_id.id,
                'account_id': self.journal_id.default_debit_account_id.id,
                'debit': bill_amount_signed, #bill.bill_amount_total_signed, # if bill.company_currency_id.id == bill.bill_currency_id.id else float_round(bill.bill_amount_total * self.exchange_rate, 2),
                'amount_currency': bill_amount if bill.company_currency_id.id != bill.bill_currency_id.id else 0, #bill.bill_amount_total if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
                'balance': bill_amount_signed, #bill.bill_amount_total_signed, # if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
                'tc': exchange_rate,
                'credit': 0,
                'date_maturity': bill.bill_date_due,
            }
            vals.append(val)
        if self.company_currency_id.id != self.currency_id.id:
            # Diferencia por redondeo
            # Obtener el diario y las cuentas de redondeo desde la configuración
            params = self.env['ir.config_parameter'].sudo()
            round_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.round_boe_journal_id'))
            round_journal = self.env['account.journal'].search([('id','=',round_boe_journal_id)])
            # Primero las letras buscamos la diferencia de redondeo
            total_credit = 0
            total_amount = 0
            difference_bill = 0
            for item in vals:
                #exchange_rate = self.env['account.bill'].search([('id','=', item['exchange_bill_id'])]).exchange_rate
                total_credit += item['credit'] / exchange_rate
                # print(item['credit'] )
                # print(exchange_rate)
                # print(item['credit'] / exchange_rate)
                # print(total_credit)
                total_amount += item['amount_currency'] if item['credit'] else 0
            if float_round(total_credit,2) != abs(total_amount):
                difference_bill = float_round(abs(total_credit- abs(total_amount)),2)
                # difference_bill_signed = difference_bill * exchange_rate
            difference_bill_signed = float_round(difference_bill * exchange_rate,2)
            # Luego los envíos buscamos la diferencia de redondeo
            exchange_rate =  self.exchange_rate if self.custom_exchange_rate else self.get_rates(self.send_date)
            total_debit = 0
            total_amount = 0
            difference = 0
            for item in vals:
                total_debit += item['debit'] / exchange_rate
                total_amount += item['amount_currency'] if item['debit'] else 0
            if float_round(total_debit,2) != abs(total_amount):
                difference = float_round(abs(total_credit- abs(total_amount)),2)
            difference_signed = float_round(difference * exchange_rate,2)
            # if total_debit != total_amount:
            #     print((total_debit / exchange_rate))
            #     print((total_debit / exchange_rate) - total_amount)
            #     print(abs((total_debit / exchange_rate) - total_amount))
            #     # difference = abs(float_round((total_debit / exchange_rate),2) - total_amount)
            #     # difference_signed = float_round(difference * exchange_rate,2)
            #     difference_signed = abs(float_round(total_debit - total_amount * exchange_rate,2))
            #     difference = difference_signed / exchange_rate
            '''Si los ajustes por redondeo de las letras son iguales a los ajustes
               de los envíos al banco ya no se colocan en el asiento contable con
               el siguiente if'''
            if difference_bill_signed != difference_signed:
                if difference_bill_signed > difference_signed:
                    difference_bill_signed -= difference_signed
                    difference = 0
                else:
                    difference_signed-= difference_bill_signed
                    difference_bill = 0
                if float_round(difference_bill,2) > 0:
                    # Asiento de diferencia por redondeo ganancia
                    val = {
                        'name': _('Currency round difference'),
                        'send_form_id': self.id,
                        'exchange_rate': exchange_rate,
                        'debit': float_round(abs(difference_bill_signed),2), #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                        'credit': 0.0, #if self.invoice_ids[0].type == 'out_invoice' else float_round(abs(total_debit - total_credit),2),
                        'account_id': round_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                        'move_id': self.account_move.id,
                        'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                        'amount_currency': float_round(abs(difference_bill),2) if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0.00,
                        'tc': exchange_rate,
                        'balance': float_round(abs(difference_bill_signed),2), # if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0.00,
                        }
                    vals.append(val)
                if float_round(difference_bill,2) < 0:
                    # Asiento de diferencia por redondeo perdida
                    val = {
                        'name': _('Currency round difference'),
                        'send_form_id': self.id,
                        'exchange_rate': exchange_rate,
                        'debit': 0.0, #if self.invoice_ids[0].type == 'out_invoice' else abs(float_round(total_debit - total_credit,2)),
                        'credit': float_round(abs(difference_bill_signed),2), #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                        'account_id': round_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                        'move_id': self.account_move.id,
                        'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                        'amount_currency': float_round(abs(difference_bill),2) * -1 if self.company_currency_id.id != self.currency_id.id else 0.00,
                        'tc': exchange_rate,
                        # 'partner_id': aml.partner_id.id,
                        'balance': float_round(abs(difference_bill_signed),2) * -1, # if self.company_currency_id.id != self.currency_id.id else 0.00,
                        }
                    vals.append(val)
                if float_round(difference,2) < 0:
                    # Asiento de diferencia por redondeo ganancia
                    val = {
                        'name': _('Currency round difference'),
                        'send_form_id': self.id,
                        'exchange_rate': exchange_rate,
                        'debit': float_round(abs(difference_signed),2), #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                        'credit': 0.0, #if self.invoice_ids[0].type == 'out_invoice' else float_round(abs(total_debit - total_credit),2),
                        'account_id': round_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                        'move_id': self.account_move.id,
                        # 'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                        # 'amount_currency': float_round(abs(difference),2) if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0.00,
                        # 'tc': exchange_rate,
                        'balance': float_round(abs(difference_signed),2), # if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0.00,
                        }
                    vals.append(val)
                if float_round(difference,2) > 0:
                    # Asiento de diferencia por redondeo perdida
                    val = {
                        'name': _('Currency round difference'),
                        'send_form_id': self.id,
                        'exchange_rate': exchange_rate,
                        'debit': 0.0, #if self.invoice_ids[0].type == 'out_invoice' else abs(float_round(total_debit - total_credit,2)),
                        'credit': float_round(abs(difference_signed),2), #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                        'account_id': round_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                        'move_id': self.account_move.id,
                        # 'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                        # 'amount_currency': float_round(abs(difference),2) * -1 if self.company_currency_id.id != self.currency_id.id else 0.00,
                        # 'tc': exchange_rate,
                        # 'partner_id': aml.partner_id.id,
                        'balance': float_round(abs(difference_signed),2) * -1, # if self.company_currency_id.id != self.currency_id.id else 0.00,
                        }
                    vals.append(val)
        # Diferencia de cambio
        # Obtener el diario y las cuentas de diferencia de cambio desde la configuración
        exchange_journal = self.env.company.currency_exchange_journal_id
        total_credit = sum(item['credit'] for item in vals)
        total_debit = sum(item['debit'] for item in vals)
        # if self.invoice_ids[0].type == 'out_invoice':
        if total_credit > total_debit:
            # Asiento de diferencia de cambio por ganancia
            val = {
                'name': _('Currency exchange rate difference'),
                'send_form_id': self.id,
                'exchange_rate': exchange_rate,
                'debit': float_round(abs(total_debit - total_credit),2), #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                'credit': 0.0, #if self.invoice_ids[0].type == 'out_invoice' else float_round(abs(total_debit - total_credit),2),
                'account_id': exchange_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                'move_id': self.account_move.id,
                'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                # 'amount_currency': float_round(abs(total_debit - total_credit) / self.exchange_rate,2)  if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0.00,
                # 'tc': exchange_rate,
                'balance': float_round(abs(total_debit - total_credit),2), # if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0.00,
                }
            vals.append(val)
        if total_credit < total_debit:
            # Asiento de diferencia de cambio por perdida
            val = {
                'name': _('Currency exchange rate difference'),
                'send_form_id': self.id,
                'exchange_rate': exchange_rate,
                'debit': 0.0, #if self.invoice_ids[0].type == 'out_invoice' else abs(float_round(total_debit - total_credit,2)),
                'credit': abs(float_round(total_debit - total_credit,2)), #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                'account_id': exchange_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                'move_id': self.account_move.id,
                'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                # 'amount_currency': float_round(abs(total_debit - total_credit) / self.exchange_rate,2) * -1 if self.company_currency_id.id != self.currency_id.id else 0.00,
                # 'tc': exchange_rate,
                'balance': float_round(abs(total_debit - total_credit),2) * -1,
                }
            vals.append(val)
        self.env['account.move.line'].create(vals)
        self.state = 'to_reconcile'
        for bill in self.bill_ids:
            bill.send_form_id = self.id
            bill.last_state = bill.state_of_bill
            bill.last_account_id = bill.account_id
            bill.account_id = self.journal_id.default_debit_account_id
            bill.state_of_bill = 'to_reconcile'

    def disburse_wizard(self):
        # Agregar un wizard para desembolsar las letras
        return self.env['disburse.wizard']\
            .with_context(active_ids=self.ids, active_model='account.send.bank', active_id=self.id)\
            .get_disburse_data()

    def disburse(self):
        disbursement_journal_id = self.env.context.get('journal_id')
        disbursement_date = self.env.context.get('disbursement_date')
        disbursement_amount = self.env.context.get('disbursement_amount')
        disbursement_interests = self.env.context.get('disbursement_interests')
        financial_expenses = self.env.context.get('financial_expenses')
        amount_claim = self.env.context.get('amount_claim')
        bank_claim_journal_id = self.env.context.get('bank_claim_journal_id')
        operation_number = self.env.context.get('operation_number')
        gloss = self.env.context.get('gloss')
        # interest_operation_number = self.env.context.get('interest_operation_number')
        # expenses_operation_number = self.env.context.get('expenses_operation_number')
        exchange_rate = self.get_rates(disbursement_date)
        # Validar modena de diario
        if disbursement_journal_id.currency_id.id == False:
            journal_currency = self.company_currency_id
        else:
            journal_currency = disbursement_journal_id.currency_id
        if self.currency_id != journal_currency:
            raise UserError(_('The currency of the disbursement journal is different from the currency sent to the bank.'))
        if not disbursement_journal_id.bank_partner_id:
            raise UserError(_('Disbursement journal does not have a bank partner. Please select one.'))
        val = {}
        vals = []
        val = {
            # 'name': self.env['ir.sequence'].next_by_code('account.bank.disbursement'),
            # 'ref': operation_number,
            'partner_id': disbursement_journal_id.bank_partner_id.id,
            'currency_id': self.currency_id.id,
            'date': disbursement_date,
            'invoice_date': disbursement_date,
            'journal_id': self.journal_id.id,
            'glosa': gloss,
            'type': 'bill',
            'currency_rate': exchange_rate,
        }
        bank_disbursement_account_move = self.env['account.move'].create(val)
        val = {
            'send_form_id': self.id,
            'journal_id': disbursement_journal_id.id,
            'company_id': self.company_id.id,
            'company_currency_id': self.company_currency_id.id,
            'currency_id': self.currency_id.id,
            'exchange_rate': exchange_rate,
            'disbursement_date': disbursement_date,
            'disbursement_amount': disbursement_amount - disbursement_interests - financial_expenses,
            'disbursement_interests': disbursement_interests,
            'financial_expenses': financial_expenses,
            'account_move': bank_disbursement_account_move.id,
            'is_advanced_payment': True if any(bill.is_advanced_payment for bill in self.bill_ids) else False,
            'state': 'payment' if any(bill.is_advanced_payment for bill in self.bill_ids) else 'done',
            'operation_number': operation_number,
            'gloss': gloss,
        }
        self.bank_disbursement_id = self.env['account.bank.disbursement'].create(val)
        bank_disbursement_account_move.name = self.bank_disbursement_id.name
        # La responsabilidad con el banco
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
        for bill in self.bill_ids:
            val = {
                # 'ref': self.name,
                'bank_disburse_id': self.bank_disbursement_id.id,
                # 'bill_form_id': bill.bill_form_id.id,
                'partner_id': bill.acceptor_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': bill.bill_number,
                'exchange_rate': exchange_rate,
                'move_id': bank_disbursement_account_move.id,
                'name': _('Bank Responsabillity ' + bill.bill_number),
                'date': disbursement_date,
                'journal_id': self.journal_id.id,
                'currency_id': bill.bill_currency_id.id if bill.company_currency_id.id != bill.bill_currency_id.id else False,
                'company_id': bill.company_id.id,
                'company_currency_id': bill.company_currency_id.id,
                'account_id': self.journal_id.default_credit_account_id.id, #bill.account_id.id, #self.journal_id.default_debit_account_id.id,
                'debit': 0, #if bill.company_currency_id.id == bill.bill_currency_id.id else float_round(bill.bill_amount_total * exchange_rate, 2),
                'amount_currency': bill.bill_amount_total * -1 if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
                'tc': exchange_rate,
                'balance': float_round(bill.bill_amount_total * exchange_rate,2) * -1, # if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
                'credit': float_round(bill.bill_amount_total * exchange_rate,2),
                'date_maturity': bill.bill_date_due,
            }
            vals.append(val)
        # Desembolso con datos de gastos financieros e intereses del wizard
        disbursement = disbursement_amount - disbursement_interests - financial_expenses
        disbursement_signed = float_round(disbursement * exchange_rate,2)
        interests_signed = float_round(disbursement_interests * exchange_rate, 2)
        amount_claim_signed = float_round(amount_claim * exchange_rate, 2)
        financial_expenses_signed = float_round(financial_expenses * exchange_rate, 2)
        # Verificar si es un anticipo
        # TODO ya no va 
        # if self.bill_ids.bill_form_id.advanced_bill_form_id:
        #     account_id = self.bill_ids.bill_form_id.advanced_bill_form_id.bridge_account_id
        # else:
        # account_id = disbursement_journal_id.default_debit_account_id.id
        # Desembolso
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','00')])
        val = {
            'ref': self.name,
            'bank_disburse_id': self.bank_disbursement_id.id,
            'partner_id': disbursement_journal_id.bank_partner_id.id,
            'type_document_id': type_document_id.id,
            'nro_comp': self.name,
            'move_id': bank_disbursement_account_move.id,
            'exchange_rate': exchange_rate,
            'name': _('Bank Disbursement') + ' ' + operation_number,
            'date': disbursement_date,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
            'company_id': self.company_id.id,
            'company_currency_id': self.company_currency_id.id,
            'account_id': disbursement_journal_id.default_debit_account_id.id,
            'debit':  disbursement_signed,
            'amount_currency': disbursement if self.company_currency_id.id != self.currency_id.id else 0,
            'tc': exchange_rate,
            'balance': disbursement_signed,
            'credit': 0,
            'date_maturity': disbursement_date,
        }
        vals.append(val)
        # Intereses
        # Obtener el diario y las cuentas de intereses bancarios desde la configuración
        params = self.env['ir.config_parameter'].sudo()
        bank_interests_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.bank_interests_boe_journal_id'))
        bank_interests_journal = self.env['account.journal'].search([('id','=',bank_interests_boe_journal_id)])
        bank_claim_journal = self.env['account.journal'].search([('id','=',bank_claim_journal_id.id)])

        if not bank_interests_journal:
            raise UserError(_('Bank Interests Journal not configured in settings.'))
        else:
            if not bank_interests_journal.default_credit_account_id:
                raise UserError(_('Bank Interests Journal credit account not configured in settings.'))
            if not bank_interests_journal.default_debit_account_id:
                raise UserError(_('Bank Interests Journal debit account not configured in settings.'))
        if not bank_claim_journal:
            raise UserError(_('Bank Interests Claim Journal not configured in settings.'))
        if not bank_claim_journal.default_credit_account_id:
            raise UserError(_('Bank Interests Claim Journal credit account not configured in settings.'))
        if not bank_claim_journal.default_debit_account_id:
            raise UserError(_('Bank Interests Claim Journal debit account not configured in settings.'))
        if disbursement_interests > 0:
            if amount_claim > 0:
                val = {
                    'ref': self.name,
                    'bank_disburse_id': self.bank_disbursement_id.id,
                    'partner_id': disbursement_journal_id.bank_partner_id.id,
                    'type_document_id': type_document_id.id,
                    'nro_comp': self.name,
                    'move_id': bank_disbursement_account_move.id,
                    'exchange_rate': exchange_rate,
                    'name': _('Bank Interests') , #+ ' ' + interest_operation_number,
                    'date': disbursement_date,
                    'journal_id': self.journal_id.id,
                    'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                    'company_id': self.company_id.id,
                    'company_currency_id': self.company_currency_id.id,
                    'account_id': bank_interests_journal.default_credit_account_id.id if self.bill_ids[0].type_bill == 'receivable' else  bank_interests_journal.default_debit_account_id.id,
                    'debit': interests_signed - amount_claim_signed,
                    'amount_currency': disbursement_interests - amount_claim if self.company_currency_id.id != self.currency_id.id else 0,
                    'tc': exchange_rate,
                    'balance': interests_signed,
                    'credit': 0,
                    'date_maturity': disbursement_date,
                }
                vals.append(val)
                val = {
                    'ref': self.name,
                    'bank_disburse_id': self.bank_disbursement_id.id,
                    'partner_id': disbursement_journal_id.bank_partner_id.id,
                    'type_document_id': type_document_id.id,
                    'nro_comp': self.name,
                    'move_id': bank_disbursement_account_move.id,
                    'exchange_rate': exchange_rate,
                    'name': _('Bank interesets claim'), # + ' ' + interest_operation_number,
                    'date': disbursement_date,
                    'journal_id': self.journal_id.id,
                    'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                    'company_id': self.company_id.id,
                    'company_currency_id': self.company_currency_id.id,
                    'account_id': bank_claim_journal.default_debit_account_id.id,
                    'debit': amount_claim_signed,
                    'amount_currency': amount_claim if self.company_currency_id.id != self.currency_id.id else 0,
                    'tc': exchange_rate,
                    'balance': amount_claim,
                    'credit': 0,
                    'date_maturity': disbursement_date,
                }
                vals.append(val)
            else:
                val = {
                    'ref': self.name,
                    'bank_disburse_id': self.bank_disbursement_id.id,
                    'partner_id': disbursement_journal_id.bank_partner_id.id,
                    'type_document_id': type_document_id.id,
                    'nro_comp': self.name,
                    'move_id': bank_disbursement_account_move.id,
                    'exchange_rate': exchange_rate,
                    'name': _('Bank Interests'), # + ' ' + interest_operation_number,
                    'date': disbursement_date,
                    'journal_id': self.journal_id.id,
                    'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                    'company_id': self.company_id.id,
                    'company_currency_id': self.company_currency_id.id,
                    'account_id': bank_interests_journal.default_credit_account_id.id if self.bill_ids[0].type_bill == 'receivable' else  bank_interests_journal.default_debit_account_id.id,
                    'debit': interests_signed,
                    'amount_currency': disbursement_interests if self.company_currency_id.id != self.currency_id.id else 0,
                    'tc': exchange_rate,
                    'balance': interests_signed,
                    'credit': 0,
                    'date_maturity': disbursement_date,
                }
                vals.append(val)
        # Gastos financieros
        if not bank_interests_journal:
            raise UserError(_('Financial Expenses Journal not configured in settings.'))
        else:
            if not bank_interests_journal.default_credit_account_id:
                raise UserError(_('Financial Expenses Journal credit account not configured in settings.'))
            if not bank_interests_journal.default_debit_account_id:
                raise UserError(_('Financial Expenses Journal debit account not configured in settings.'))
        if financial_expenses > 0:
            val = {
                'ref': self.name,
                'bank_disburse_id': self.bank_disbursement_id.id,
                'partner_id': disbursement_journal_id.bank_partner_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.name,
                'move_id': bank_disbursement_account_move.id,
                'exchange_rate': exchange_rate,
                'name': _('Financial Expenses'), # + ' ' + expenses_operation_number,
                'date': disbursement_date,
                'journal_id': self.journal_id.id,
                'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                'company_id': self.company_id.id,
                'company_currency_id': self.company_currency_id.id,
                'account_id': bank_interests_journal.default_credit_account_id.id if self.bill_ids[0].type_bill == 'receivable' else  bank_interests_journal.default_debit_account_id.id,
                'debit': financial_expenses_signed,
                'amount_currency': financial_expenses if self.company_currency_id.id != self.currency_id.id else 0,
                'tc': exchange_rate,
                'balance': financial_expenses_signed,
                'credit': 0,
                'date_maturity': disbursement_date,
            }
            vals.append(val)
        # Diferencia por redondeo
        # Obtener el diario y las cuentas de redondeo desde la configuración
        if self.currency_id != self.company_currency_id:
            params = self.env['ir.config_parameter'].sudo()
            round_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.round_boe_journal_id'))
            round_journal = self.env['account.journal'].search([('id','=',round_boe_journal_id)])
            # total_credit = 0
            # total_credit_currency = 0
            # exchange_rate = 0
            # for item in vals:
            #     exchange_rate = item['exchange_rate'] # TODO debo agregar 0 de lo contrario devuelve una tupla. Es muy extraño
            #     total_credit += item['credit'] / exchange_rate
            #     total_credit_currency += item['amount_currency'] if item['credit'] else 0
            
            # exchange_rate = self.get_rates(disbursement_date)
            # # total_credit = sum(item['credit'] for item in vals) 
            # # total_credit_currency = sum(item['amount_currency'] if item['credit'] else 0 for item in vals) 
            # total_debit = sum(item['debit'] for item in vals) #/ exchange_rate
            # total_debit_currency = sum(item['amount_currency'] if item['debit'] else 0 for item in vals) 
            # # difference = float_round(total_amount_currency * self.exchange_rate - total_debit, 2)
            # difference_responsability = float_round(total_credit - abs(total_credit_currency),2)
            # difference_responsability_signed = float_round(difference_responsability * exchange_rate,2)
            # # difference_disburse = float_round(total_debit / exchange_rate - total_debit_currency,2)
            # # difference_disburse_signed = float_round(difference_disburse * exchange_rate,2)
            # difference_disburse_signed = float_round(total_debit / exchange_rate - total_debit_currency,2)
            # difference_disburse = float_round(difference_disburse_signed / exchange_rate,2)

            total_debit = sum(item['debit'] for item in vals)
            total_credit = sum(item['credit'] for item in vals)
            difference = total_debit - total_credit

            # '''Si los ajustes por redondeo de las responsabilidades son iguales a los ajustes
            #    de la suma de desembolso intereses y gastos bancarios ya no se colocan en el 
            #    asiento contable con el siguiente if'''
            # if difference_responsability_signed != difference_disburse_signed:
            if float_round(difference,2) < 0:
                # Asiento de diferencia por redondeo ganancia
                val = {
                    'name': _('Currency round difference'),
                    'type_document_id': type_document_id.id,
                    'nro_comp': self.name,
                    'bank_disburse_id': self.bank_disbursement_id.id,
                    'exchange_rate': exchange_rate,
                    'debit': float_round(abs(difference),2), #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'credit': 0.0, #if self.invoice_ids[0].type == 'out_invoice' else float_round(abs(total_debit - total_credit),2),
                    'account_id': round_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                    'move_id': bank_disbursement_account_move.id,
                    'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                    # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                    # 'amount_currency': float_round(abs(difference_responsability),2) if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    'tc': exchange_rate,
                    'balance': float_round(abs(difference),2), # if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    }
                vals.append(val)
            if float_round(difference,2) > 0:
                # Asiento de diferencia por redondeo perdida
                val = {
                    'name': _('Currency round difference'),
                    'type_document_id': type_document_id.id,
                    'nro_comp': self.name,
                    'bank_disburse_id': self.bank_disbursement_id.id,
                    'exchange_rate': exchange_rate,
                    'debit': 0.0, #if self.invoice_ids[0].type == 'out_invoice' else abs(float_round(total_debit - total_credit,2)),
                    'credit': float_round(abs(difference),2), #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'account_id': round_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                    'move_id': bank_disbursement_account_move.id,
                    'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                    # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                    # 'amount_currency': float_round(abs(difference_responsability),2) * -1 if self.company_currency_id.id != self.currency_id.id else 0.00,
                    'tc': exchange_rate,
                    # 'partner_id': aml.partner_id.id,
                    'balance': float_round(abs(difference),2) * -1, # if self.company_currency_id.id != self.currency_id.id else 0.00,
                    }
                vals.append(val)
                # if float_round(difference_disburse_signed,2) > 0:
                #     # Asiento de diferencia por redondeo ganancia
                #     val = {
                #         'name': _('Currency round difference'),
                #         'bank_disburse_id': self.bank_disbursement_id.id,
                #         'exchange_rate': exchange_rate,
                #         'debit': float_round(abs(difference_disburse_signed),2), #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                #         'credit': 0.0, #if self.invoice_ids[0].type == 'out_invoice' else float_round(abs(total_debit - total_credit),2),
                #         'account_id': round_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                #         'move_id': bank_disbursement_account_move.id,
                #         'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                #         # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                #         # 'amount_currency': float_round(abs(difference_disburse),2) if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0.00,
                #         'tc': exchange_rate,
                #         'balance': float_round(abs(difference_disburse_signed),2), # if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0.00,
                #         }
                #     vals.append(val)
                # if float_round(difference_disburse_signed,2) < 0:
                #     # Asiento de diferencia por redondeo perdida
                #     val = {
                #         'name': _('Currency round difference'),
                #         'bank_disburse_id': self.bank_disbursement_id.id,
                #         'exchange_rate': exchange_rate,
                #         'debit': 0.0, #if self.invoice_ids[0].type == 'out_invoice' else abs(float_round(total_debit - total_credit,2)),
                #         'credit': float_round(abs(difference_disburse_signed),2), #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                #         'account_id': round_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                #         'move_id': bank_disbursement_account_move.id,
                #         'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                #         # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                #         # 'amount_currency': float_round(abs(difference_disburse),2) * -1 if self.company_currency_id.id != self.currency_id.id else 0.00,
                #         'tc': exchange_rate,
                #         # 'partner_id': aml.partner_id.id,
                #         'balance': float_round(abs(difference_disburse_signed),2) * -1, # if self.company_currency_id.id != self.currency_id.id else 0.00,
                #         }
                #     vals.append(val)
            # Diferencia de cambio
            # Obtener el diario y las cuentas de diferencia de cambio desde la configuración
            exchange_journal = self.env.company.currency_exchange_journal_id
            total_credit = float_round(sum(item['credit'] for item in vals),2)
            total_debit = float_round(sum(item['debit'] for item in vals),2)
            # if self.invoice_ids[0].type == 'out_invoice':
            if total_credit > total_debit:
                # Asiento de diferencia de cambio por ganancia
                val = {
                    'name': _('Currency exchange rate difference'),
                    'bank_disburse_id': self.bank_disbursement_id.id,
                    'exchange_rate': exchange_rate,
                    'debit': float_round(abs(total_debit - total_credit),2), #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'credit': 0.0, #if self.invoice_ids[0].type == 'out_invoice' else float_round(abs(total_debit - total_credit),2),
                    'account_id': exchange_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                    'move_id': bank_disbursement_account_move.id,
                    'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                    # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                    # 'amount_currency': float_round(abs(total_debit - total_credit) / self.exchange_rate,2)  if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    'tc': exchange_rate,
                    'balance': float_round(abs(total_debit - total_credit),2), # if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    }
                vals.append(val)
            if total_credit < total_debit:
                # Asiento de diferencia de cambio por perdida
                val = {
                    'name': _('Currency exchange rate difference'),
                    'bank_disburse_id': self.bank_disbursement_id.id,
                    'exchange_rate': exchange_rate,
                    'debit': 0.0, #if self.invoice_ids[0].type == 'out_invoice' else abs(float_round(total_debit - total_credit,2)),
                    'credit': abs(float_round(total_debit - total_credit,2)), #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'account_id': exchange_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                    'move_id': bank_disbursement_account_move.id,
                    'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                    # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                    # 'amount_currency': float_round(abs(total_debit - total_credit) / self.exchange_rate,2) * -1 if self.company_currency_id.id != self.currency_id.id else 0.00,
                    'tc': exchange_rate,
                    'balance': float_round(abs(total_debit - total_credit),2) * -1,
                    }
                vals.append(val)
        self.env['account.move.line'].create(vals)
        self.state = 'disbursed'
        bank_disbursement_account_move.ref = operation_number
        bank_disbursement_account_move.action_post()
        for bill in self.bill_ids:
            bill.send_form_id = self.id
            bill.last_state = bill.state_of_bill
            # bill.last_account_id = bill.account_id
            # bill.account_id = self.journal_id.default_debit_account_id
            bill.state_of_bill = 'disbursed'

    def reconcile(self):
        if self.state != 'to_reconcile':
            raise UserError(_('You can\'t reconcile a form in %s state.' %self.state))
        self.state = 'sent' if self.bank_position != 'discount' else 'to_disburse'
        self.account_move.action_post()
        # Reconciliar asientos
        # TODO por ahora no es necesario segun itgrupo
        for line in self.account_move_line_ids:
            lines = line
            for bill in self.bill_ids:
                filtered = bill.bill_form_id.account_move_line_ids.filtered(lambda l: l.account_id == lines[0].account_id and\
                    not l.reconciled and\
                    l.name == line.name)
                if filtered:
                    lines += filtered[0]
                if len(lines)>1:
                    break
            if line.credit > 0 and not line.reconciled and\
                line.name != _('Currency exchange rate difference') and\
                line.name != _('Currency round difference'):
                lines.reconcile()
        for bill in self.bill_ids:
            bill.state_of_bill = self.bank_position
            self.bill_form_ids = [(4,bill.bill_form_id.id)] if bill.bill_form_id else self.bill_form_ids
            self.bill_refinancing_form_ids = [(4,bill.refinancing_form_id.id)] if bill.refinancing_form_id else self.bill_refinancing_form_ids
            bill.bill_form_id.send_form_ids = [(4,self.id)]
            if self.bank_position == 'discount':
                bill.state_of_bill = 'to_disburse'
                # bill.last_account_id = bill.account_id
                bill.account_id = self.journal_id.default_debit_account_id

    def cancel(self):
        if self.state == 'imported':
            raise UserError(_("You can't cancel an imported form. Please go to importation forms."))
        if any(x.state_of_bill != self.bill_ids[0].state_of_bill for x in self.bill_ids):
            raise UserError(_("You can't cancel this form because some of their bills are in diferent states."))
        if any(x.state_of_bill != 'disbursed' for x in self.bill_ids) and self.state == 'disbursed':
            raise UserError(_("You can't cancel this form because it have been disbursed and some of their bills have changed state."))
        if any(x.state_of_bill not in ['collection','guarantee'] for x in self.bill_ids) and self.state == 'sent':
            raise UserError(_("You can't cancel this form because it have been sent and some of their bills have changed state."))
        # if self.state == 'disbursed':
        if self.state == 'disbursed':
            if self.bank_disbursement_id.payment_id:
                raise UserError(_('You can\'t cancel this form because disbursment have advanced payments.'))
            self.bank_disbursement_id.account_move.button_draft()
            self.bank_disbursement_id.account_move_line_ids.unlink()
            self.bank_disbursement_id.unlink()
            self.bank_disbursement_id = False
            self.is_discount = False
            self.state = 'to_disburse'
            for bill in self.bill_ids:
                bill.state_of_bill = 'to_disburse'
        else:
            self.account_move.button_draft()
            for line in self.account_move_line_ids:
                line.remove_move_reconcile()
            self.account_move.with_context(force_delete=True).unlink()
            self.state = 'draft'
            for bill in self.bill_ids:
                bill.state_of_bill = 'portfolio'
                if bill.bill_form_id:
                    bill.account_id = bill.bill_form_id.journal_id.default_debit_account_id
                if bill.refinancing_form_id:
                    bill.account_id = bill.refinancing_form_id.journal_id.default_debit_account_id
                self.bill_form_ids = [(3,bill.bill_form_id.id)]
                bill.bill_form_id.send_form_ids = [(3,self.id)]

    def open_bill_form_view(self):
        if self.bill_ids[0].type_bill == 'receivable':
            [action] = self.env.ref('jp_account_bills_of_exchange.action_account_customer_bill_forms').read()
        else:
            [action] = self.env.ref('jp_account_bills_of_exchange.action_account_supplier_bill_forms').read()
        ids = self.bill_form_ids.ids
        action['domain'] = [('id', 'in', ids)]
        return action

    def open_bill_refinancing_form_view(self):
        [action] = self.env.ref('jp_account_bills_of_exchange.action_account_customer_refinancing_forms').read()
        ids = self.bill_refinancing_form_ids.ids
        action['domain'] = [('id', 'in', ids)]
        return action

    #TODO borrar despues de utilizar
    def curar_fecha(self):
        lines = self.env['account.move.line'].search([('exchange_bill_id','!=',False)])
        for line in lines:
            print(str(line.exchange_bill_id.bill_date_issue))
            sql = """UPDATE account_move_line set date = '""" + str(line.exchange_bill_id.bill_date_issue) + """' where id = """ + str(line.id)
            self.env.cr.execute(sql)
            #line.date = line.exchange_bill_id.bill_date_issue
