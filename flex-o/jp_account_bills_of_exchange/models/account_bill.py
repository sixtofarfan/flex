from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, Warning
from datetime import datetime, timedelta, date
from odoo.tools import float_round

class AccountBill(models.Model):
    _name = 'account.bill'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Bill of Exchange'

    # def _get_creditor(self):
    #     if self.bill_form_id.partner_id:
    #         return self.bill_form_id.partner_id
    #     else:
    #         import_form_id = self.env['account.import.bill.form'].search([('id','=',self.bill_form_id)])
    #         return self.bill_form_id.

    name = fields.Char(string='Name', compute='_compute_get_name')
    bill_form_id = fields.Many2one(comodel_name='account.bill.form', string='Bill Form')
    refinancing_form_id = fields.Many2one(comodel_name='account.refinancing.form', string='Refinance Form')
    send_form_id = fields.Many2one(comodel_name='account.send.bank', string='Send Form', tracking=True,)
    renew_form_id = fields.Many2one(comodel_name='renew.bill.form', string='Renewal Form')
    renew_date = fields.Date(string='Renew Date', default=fields.Date.context_today, required = True, tracking=True,)
    responsable_id = fields.Many2one(comodel_name='res.partner', string='Responsable')
    guarantee_id = fields.Many2one(comodel_name='res.partner', string='Guarantee')
    acceptor_id = fields.Many2one(comodel_name='res.partner', string='Acceptor')
    creditor_id = fields.Many2one(comodel_name='res.partner', string='Creditor') #, compute=_get_creditor)
    origin_bill_id = fields.Many2one(comodel_name='account.bill', string='Origin', default=False)
    renew_bill_id = fields.Many2one(comodel_name='account.bill', string='Renewal from bill', default=False)
    renewal_ids = fields.One2many(comodel_name='account.bill', inverse_name='origin_bill_id', string='Renewals')
    bill_date_due = fields.Date(string='Bill Due Date')
    bill_date_issue = fields.Date(string='Bill Issue Date')
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.company),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    bill_currency_id = fields.Many2one(comodel_name='res.currency', string='Bill Currency')
    bill_number = fields.Char('Bill Number')
    bank_number = fields.Char('Bank Number', tracking=True,)
    bill_amount_total = fields.Monetary(string='Total', currency_field='bill_currency_id', default=0)
    bill_amount_total_signed = fields.Monetary(string='Total Signed', currency_field='company_currency_id', default=0)
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1)
    amount_text = fields.Text(string='Amount Text', compute='_get_amount_text')
    state_of_bill = fields.Selection([
     ('draft', 'Draft'),
     ('to_accept', 'To accept'),
     ('to_reconcile', 'To reconcile'),
     ('to_disburse', 'To disburse'),
     ('portfolio', 'Portfolio'),
     ('accepted', 'Accepted'),
     ('collection', 'Collection'),
     ('discount', 'Discount'),
     ('guarantee', 'Guarantee'),
     ('disbursed', 'Disbursed'),
     ('pending', 'Pending renew'),
     ('to_renew', 'To renew'),
     ('renewed', 'Renewed'),
     ('protested', 'Protested'),
     ('refinanced', 'Refinanced'),
     ('paid', 'Paid')],
      string='State',
      default='draft', tracking=True,)
    last_state = fields.Char('Last State')
    last_account_id = fields.Many2one(comodel_name='account.account', string='Last Account')
    account_id = fields.Many2one(comodel_name='account.account', string='Account')    
    account_move_line_ids = fields.One2many('account.move.line', 'bill_id', string='Account move lines')
    account_move = fields.Many2one('account.move', 'Account Move')
    type_bill = fields.Selection([('receivable', 'Receivable'),('payable', 'Payable')], string='Type of Bill')
    protest_payment_id = fields.Many2one('account.protest.payment', string='Protest payment')
    protest_date_compute = fields.Date(string='Protest Date', compute='_compute_protest_date')
    is_from_dn = fields.Boolean('Is bill from debit note?', help='If bill is from debit note on refinancing')
    bank_disbursement_id = fields.Many2one('account.bank.disbursement', string='Disbursement', related="send_form_id.bank_disbursement_id")
    payment_date = fields.Date(string='Payment Date')
    account_move_bank_interests_id = fields.Many2one('account.move', string='Financial Expenses Move')
    protest_debit_note_id = fields.Many2one('account.move', string='Protest Debit Note')
    is_advanced_payment = fields.Boolean(string='Is advanced payment')
    partial_payment_ids = fields.One2many('account.bill.partial.payment', 'bill_id', string='Partial payments')
    renew_payment_id = fields.Many2one('account.move', string='Renew Payment Move')

    def is_holiday(self, date):
        # Verifica si la fecha es feriado
        from_date = datetime.strftime(date, '%Y-%m-%d %H:%M:%S')
        to_date = datetime.strftime(date, '%Y-%m-%d 23:59:59')
        holidays = self.env['resource.calendar.leaves'].search([('date_from','>=',from_date),('date_from','<=',to_date)])
        if len(holidays)>0:
            return True
        else:
            return False
        # return True if len(holidays.ids) > 0 else False

    @api.onchange('bill_date_due')
    def onchange_bill_date_due(self):
        # print(self.bill_date_due.strftime('%A'))
        if self.bill_date_due:
            if self.bill_date_due.strftime('%A') == 'sábado' or self.bill_date_due.strftime('%A') == 'domingo' or self.is_holiday(self.bill_date_due):
                return {
                    'warning': {
                        'title': _('Check Date'), 
                        'message': _('The date should be Monday through Friday and should not be a holiday.'),
                        'type': 'danger',
                        },
                    }

    @api.depends('bill_amount_total')
    def _get_amount_text(self):
        for bill in self:
            if bill.bill_amount_total<2 and bill.bill_amount_total>=1:
                currency_name = bill.bill_currency_id.singular_name or bill.bill_currency_id.plural_name or bill.bill_currency_id.name or ""
            else:
                currency_name = bill.bill_currency_id.plural_name or bill.bill_currency_id.name or ""
            fraction_name = bill.bill_currency_id.fraction_name or ""
            amount_text = bill.bill_currency_id.amount_to_text(bill.bill_amount_total)
            bill.amount_text = amount_text
    
    @api.onchange('bill_amount_total','exchange_rate')
    def onchange_bill_amount_total(self):
        if self.bill_currency_id != self.company_currency_id:
            self.bill_amount_total_signed = self.bill_amount_total * self.exchange_rate
        else:
            self.bill_amount_total_signed = self.bill_amount_total

    @api.onchange('bill_amount_total_signed')
    def onchange_bill_amount_total_signed(self):
        if self.bill_currency_id != self.company_currency_id:
            self.bill_amount_total = self.bill_amount_total_signed / self.exchange_rate
        else:
            self.bill_amount_total = self.bill_amount_total_signed

    @api.depends('bill_date_due')
    def _compute_protest_date(self):
        for bill in self:
            bill.protest_date_compute = bill.bill_date_due + timedelta(days=8)

    def get_exchange_rate(self, amount, currency, company, date):
        return self.bill_currency_id._convert(amount, currency, company, date, False)

    def get_rates(self, change_date):
        if self.bill_currency_id.id == self.company_currency_id.id:
            exchange_rate = 1
        else:
            exchange_rate = self.get_exchange_rate(1, self.company_id.currency_id, self.company_id, change_date)
        return exchange_rate

    def get_exchange_rate_currency(self, amount, currency, company, date, currency_id):
        return currency_id._convert(amount, currency, company, date, False)

    def get_rates_currency(self, currency_id, change_date):
        if currency_id == self.company_currency_id.id:
            exchange_rate = 1
        else:
            exchange_rate = self.get_exchange_rate_currency(1, self.company_id.currency_id, self.company_id, change_date, currency_id)
        return exchange_rate

    @api.model
    def _compute_get_name(self):
        for bill in self:
            bill.name = bill.bill_number + '(' + bill.bank_number + ')' if bill.bank_number else bill.bill_number

    def unlink(self):
        for bill in self:
            if bill.state_of_bill != 'draft' and not self._context.get('force_delete'):
                raise UserError(_("You cannot delete a bill in %s.") %bill.state_of_bill)
        return super(AccountBill, self).unlink()

    def pay_bill_wizard(self):
        # Si la letra ya fue desembolsada en descuento
        # if self.state_of_bill == 'disbursed' or self.last_state == 'disbursed' and self.state_of_bill != 'protested':
        #     self.last_state = self.state_of_bill
        #     self.state_of_bill = 'paid'
        #     return
        # Agregar un wizard para pagar la letra
        return self.env['pay.bill.wizard']\
            .with_context(active_ids=self.ids, active_model='account.bill', active_id=self.id)\
            .get_payment()
    
    def pay_bill(self):
        #Validaciones
        if self.state_of_bill == 'protested':
            vals = []
            val = {}
            payment_date = self.env.context.get('payment_date')
            payment_journal_id = self.env.context.get('payment_journal')
            payment_currency_id = self.env.context.get('payment_currency_id')
            payment_amount = self.env.context.get('payment_amount')
            exchange_rate = self.env.context.get('exchange_rate') if self.env.context.get('exchange_rate') else round(self.get_rates(payment_date), 3)
            operation_number = self.env.context.get('operation_number')
            add_debit_note = self.env.context.get('add_debit_note')
            total_partial_payments = payment_amount_signed =0
            for pp in self.partial_payment_ids:
                total_partial_payments += pp.payment_amount_signed
            # total_partial_payments += payment_amount
            if self.bill_currency_id != payment_currency_id:
                if payment_currency_id == self.env.company.currency_id:
                    payment_amount_signed = float_round(payment_amount / exchange_rate, 2)
                else:
                    payment_amount_signed = float_round(payment_amount * exchange_rate, 2)
            else:
                payment_amount_signed = payment_amount
            # if self.env.context.get('payment_amount') < self.bill_amount_total:
            if payment_amount_signed < round(self.bill_amount_total - total_partial_payments + (self.protest_debit_note_id.amount_residual if add_debit_note else 0), 2):
                # raise UserError(_('Can\'t pay less than the original amount %s %s') %(self.bill_currency_id.name, self.bill_amount_total))
                val ={
                    'name': self.env['ir.sequence'].next_by_code('account.bill.partial.payment'),
                    'payment_date': payment_date,
                    'bill_id': self.id,
                    'currency_id': payment_currency_id.id,
                    'payment_amount': payment_amount,
                    'payment_amount_signed': payment_amount_signed,
                    'journal_id': payment_journal_id.id,
                    'operation_number': operation_number,
                    'exchange_rate': exchange_rate,
                }
                partial_payment_id = self.env['account.bill.partial.payment'].create(val)
                partial_payment_id.create_move(self)
                return
            elif round(payment_amount_signed + total_partial_payments, 2) > round(self.bill_amount_total + (self.protest_debit_note_id.amount_residual if add_debit_note else 0), 2):
                # print(payment_amount_signed + total_partial_payments , self.bill_amount_total + (self.protest_debit_note_id.amount_residual if add_debit_note else 0))
                raise UserError(_('Can\'t pay more than the original amount %s %s') %(self.bill_currency_id.name, self.bill_amount_total))
            # payment_amount = total_partial_payments
            val = {
                'name': self.env['ir.sequence'].next_by_code('account.protest.payment'),#'PP-' + self.name,
                'currency_id': self.bill_currency_id.id,
                'currency_rate': exchange_rate,
                'date': payment_date,
                # 'invoice_date': payment_date,
                # 'partner_id': self.responsable_id.id,
                'invoice_date': self.bill_date_issue,
                'journal_id': self.bill_form_id.journal_id.id if self.bill_form_id else self.origin_bill_id.bill_form_id.journal_id.id if self.origin_bill_id and self.origin_bill_id.bill_form_id else self.origin_bill_id.send_form_id.journal_id.id if self.origin_bill_id.send_form_id else self.send_form_id.journal_id.id,
                'glosa': _('Protest payment bill %s') %self.bill_number,
                'type': 'bill',
            }
            protest_payment_account_move = self.env['account.move'].create(val)
            val = {
                'bill_id': self.id,
                'payment_date': payment_date,
                'company_id': self.company_id.id,
                'company_currency_id': self.company_currency_id.id,
                'currency_id': payment_currency_id.id,
                'exchange_rate': exchange_rate,
                'payment_amount_total': payment_amount,
                'payment_amount_total_signed': round(payment_amount * exchange_rate,2),
                'account_move': protest_payment_account_move.id,
                'bill_last_state': self.last_state,
                'type_form': '3' if self.type_bill == 'receivable' else '4'
            }
            self.protest_payment_id = self.env['account.protest.payment'].create(val)
            # Crear asientos desde el protesto
            # Asiento de pago de cliente
            # Verificamos primero si la letra no ha sido importada
            if self.account_move_line_ids:
                item = self.account_move_line_ids[0]
            else:
                # Si la letra no ha sido importada creamos una linea de asiento para obtener los datos
                # esta linea al final de todo se hará la comprobación nuevamente si fue importada y
                # será eliminada.
                # Obtener el diario y las cuentas de protesto desde la configuración
                params = self.env['ir.config_parameter'].sudo()
                protest_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.protest_boe_journal_id'))
                protest_journal = self.env['account.journal'].search([('id','=',protest_boe_journal_id)])
                val = {
                    'move_id': protest_payment_account_move.id,
                    # 'ref': 'Imported protested bill',
                    'name': _('Protest payment'),
                    'account_id': self.account_id.id,
                    'journal_id': protest_journal.id,
                    'currency_id': self.bill_currency_id.id,
                    'company_id': self.company_id.id,
                    'company_currency_id': self.company_currency_id.id,
                    'exchange_rate': self.exchange_rate,
                    'amount_currency': self.bill_amount_total * -1 if self.bill_currency_id != self.company_currency_id else 0,
                    'debit': 0,
                    'credit': self.bill_amount_total_signed,
                    'balance': self.bill_amount_total_signed * -1,
                    'date_maturity': self.bill_date_due,
                    'tc': exchange_rate,
                }
                vals.append(val)
                val = {
                    'move_id': protest_payment_account_move.id,
                    # 'ref': 'Imported protested bill',
                    'name': 'Protest payment',
                    'account_id': self.account_id.id,
                    'journal_id': protest_journal.id,
                    'currency_id': self.bill_currency_id.id,
                    'company_id': self.company_id.id,
                    'company_currency_id': self.company_currency_id.id,
                    'exchange_rate': self.exchange_rate,
                    'amount_currency': self.bill_amount_total if self.bill_currency_id != self.company_currency_id else 0,
                    'debit': self.bill_amount_total_signed,
                    'credit': 0,
                    'balance': self.bill_amount_total_signed,
                    'date_maturity': self.bill_date_due,
                    'tc': exchange_rate,
                }
                vals.append(val)
                items = self.env['account.move.line'].create(vals)
                item = items[0]
                vals =[]
            if self.bill_currency_id != payment_currency_id:
                if payment_currency_id != self.company_currency_id: 
                    total_amount = payment_amount 
                else:
                    total_amount = payment_amount / exchange_rate
            else:
                total_amount = payment_amount
            total_amount_signed = round(total_amount * exchange_rate,2) if self.company_currency_id != payment_currency_id else payment_amount
            # Pago del banco
            # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
            type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
            val = {
                # 'ref': item.ref,
                'protest_payment_id': self.protest_payment_id.id,
                'partner_id': self.acceptor_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': operation_number,
                'move_id': protest_payment_account_move.id,
                'exchange_rate': exchange_rate,
                'name': _('Customer payment for bill ') + self.name + ('' if not add_debit_note else _(' and debit note ')), #item.name if item.name[:20] != _('Bank charge for bill') else _('Customer payment for bill ') + self.name,
                'date': payment_date,
                'journal_id': item.journal_id.id ,
                'currency_id': item.currency_id.id,
                'company_id': item.company_id.id,
                'company_currency_id': item.company_currency_id.id,
                'account_id': payment_journal_id.default_debit_account_id.id,
                'amount_currency': total_amount * (1 if self.type_bill == 'receivable' else -1) if self.company_currency_id != payment_currency_id else 0, #item.amount_currency * -1.0,
                'tc': exchange_rate,
                'balance': total_amount_signed * (1 if self.type_bill == 'receivable' else -1), #item.balance * -1.0,
                'debit': abs(total_amount_signed) if self.type_bill == 'receivable' else 0, #item.credit if self.type_bill == 'receivable' else 0,
                'credit': 0 if self.type_bill == 'receivable' else abs(total_amount_signed), #0 if self.type_bill == 'receivable' else item.credit,
                'date_maturity': item.date_maturity,
            }
            vals.append(val)
            # Si el campo add_debit_note es verdadero se agrega la nota de debito del protesto
            # al pago parcial
            if add_debit_note:
                if self.protest_debit_note_id.currency_id != payment_currency_id:
                    if payment_currency_id != self.company_currency_id: 
                        total_amount = self.protest_debit_note_id.amount_residual 
                    else:
                        total_amount = self.protest_debit_note_id.amount_residual / exchange_rate
                else:
                    total_amount = self.protest_debit_note_id.amount_residual
                total_amount_signed = round(self.protest_debit_note_id.amount_residual * exchange_rate,2) if self.company_currency_id != payment_currency_id else self.protest_debit_note_id.amount_residual
                val = {
                'ref': item.ref,
                'protest_payment_id': self.protest_payment_id.id,
                'partner_id': self.protest_debit_note_id.partner_id.id,
                'type_document_id': self.protest_debit_note_id.type_document_id.id,
                'nro_comp': self.protest_debit_note_id.ref,
                'move_id': protest_payment_account_move.id,
                'exchange_rate': exchange_rate,
                'name': _('Debit note payment ') + self.protest_debit_note_id.ref, #item.name if item.name[:20] != _('Bank charge for self') else _('Customer payment for self ') + self.name,
                'date': self.protest_debit_note_id.invoice_date,
                'journal_id': item.journal_id.id ,
                'currency_id': item.currency_id.id,
                'company_id': item.company_id.id,
                'company_currency_id': item.company_currency_id.id,
                'account_id': self.protest_debit_note_id.line_ids.filtered(lambda l: l.account_internal_type == 'receivable').account_id.id,
                'amount_currency': total_amount * (1 if self.type_bill != 'receivable' else -1) if self.company_currency_id != self.protest_debit_note_id.currency_id else 0, #item.amount_currency * -1.0,
                'tc': exchange_rate,
                'balance': total_amount_signed * (1 if self.type_bill != 'receivable' else -1), #item.balance * -1.0,
                'debit': abs(total_amount_signed) if self.type_bill != 'receivable' else 0, #item.credit if self.type_bill != 'receivable' else 0,
                'credit': 0 if self.type_bill != 'receivable' else abs(total_amount_signed), #0 if self.type_bill != 'receivable' else item.credit,
                'date_maturity': self.protest_debit_note_id.invoice_date_due,
                }
                vals.append(val)
            # Asiento de salida de letra
            if self.account_move_line_ids:
                item = self.account_move_line_ids.filtered(lambda l: l.name == self.bill_number and \
                    l.account_id == self.account_id and \
                    l.account_internal_type in ('receivable', 'payable') and \
                    l.debit > 0 and \
                    l.reconciled == False)
            # total_amount = abs(item.amount_currency) if item.amount_currency else item.debit
            # if self.protest_debit_note_id.currency_id != payment_currency_id:
            #     if payment_currency_id != self.company_currency_id: 
            #         total_amount = self.protest_debit_note_id.amount_residual 
            #     else:
            #         total_amount = self.protest_debit_note_id.amount_residual / exchange_rate
            # else:
            #     total_amount = self.protest_debit_note_id.amount_residual
            total_amount = round((payment_amount_signed - self.protest_debit_note_id.amount_residual if add_debit_note else payment_amount_signed) if item.amount_currency else item.debit, 2)
            # total_amount = payment_amount_signed if item.amount_currency else item.debit
            total_amount_signed = round(total_amount * exchange_rate,2) if self.bill_currency_id != self.env.company.currency_id else self.bill_amount_total
            val = {
                # 'ref': item.ref,
                'protest_payment_id': self.protest_payment_id.id,
                'partner_id': self.acceptor_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.bill_number,
                'move_id': protest_payment_account_move.id,
                'exchange_rate': exchange_rate,
                'name': self.name, #item.name if item.name[:20] != _('Bank Responsabillity') else self.name,
                'date': payment_date,
                'journal_id': item.journal_id.id,
                'currency_id': item.currency_id.id,
                'company_id': item.company_id.id,
                'company_currency_id': item.company_currency_id.id,
                'account_id': self.account_id.id, #item.account_id.id if item.name[:20] != _('Bank Responsabillity') else self.account_id.id,
                'amount_currency': total_amount * (-1 if self.type_bill == 'receivable' else 1) if item.amount_currency else 0,
                'tc': exchange_rate,
                'balance': total_amount_signed * (-1 if self.type_bill == 'receivable' else 1),
                'debit': 0 if self.type_bill == 'receivable' else total_amount_signed,
                'credit': total_amount_signed if self.type_bill == 'receivable' else 0,
                'date_maturity': item.date_maturity,
            }
            vals.append(val)
            # TODO NO VA PORKE SE HACE LUEGO CON NOTA DE DEBITO LOS INTERESES FINANCIEROS
            # # Asiento de los gastos financieros
            # item = self.account_move_line_ids[2]
            # total_amount = item.amount_currency if item.amount_currency else item.debit
            # total_amount_signed = round(total_amount * exchange_rate,2) if self.bill_currency_id != payment_currency_id else item.debit
            # val = {
            #     'ref': item.ref,
            #     'protest_payment_id': self.protest_payment_id.id,
            #     'move_id': protest_payment_account_move.id,
            #     'name': item.name, # if item.name[:20] != _('Bank Responsabillity') else self.name,
            #     'date': payment_date,
            #     'journal_id': item.journal_id.id ,
            #     'currency_id': item.currency_id.id,
            #     'company_id': item.company_id.id,
            #     'company_currency_id': item.company_currency_id.id,
            #     'account_id': item.account_id.id, # if item.name[:20] != _('Bank Responsabillity') else self.account_id.id,
            #     'amount_currency': item.amount_currency * -1.0,
            #     'balance': total_amount_signed * -1.0,
            #     'debit': 0 if self.type_bill == 'receivable' else total_amount_signed,
            #     'credit': total_amount_signed if self.type_bill == 'receivable' else 0,
            #     'date_maturity': item.date_maturity,
            # }
            # vals.append(val)

            # TODO ANTIGUO
            # for item in self.account_move_line_ids:
            #     if item.debit >0:
            #         val = {
            #             'ref': item.ref,
            #             'protest_payment_id': self.protest_payment_id.id,
            #             'move_id': protest_payment_account_move.id,
            #             'name': item.name if item.name[:20] != _('Bank Responsabillity') else self.name,
            #             'date': payment_date,
            #             'journal_id': item.journal_id.id ,
            #             'currency_id': item.currency_id.id,
            #             'company_id': item.company_id.id,
            #             'company_currency_id': item.company_currency_id.id,
            #             'account_id': item.account_id.id if item.name[:20] != _('Bank Responsabillity') else self.account_id.id,
            #             'amount_currency': item.amount_currency * -1.0,
            #             'balance': item.balance * -1.0,
            #             'debit': 0 if self.type_bill == 'receivable' else item.debit,
            #             'credit': item.debit if self.type_bill == 'receivable' else 0,
            #             'date_maturity': item.date_maturity,
            #         }
            #         vals.append(val)
            #     else:
            #         total_amount = item.amount_currency
            #         total_amount_signed = round(total_amount * exchange_rate,2) if self.company_currency_id != payment_currency_id else item.credit
            #         val = {
            #             'ref': item.ref,
            #             'protest_payment_id': self.protest_payment_id.id,
            #             'move_id': protest_payment_account_move.id,
            #             'name': item.name if item.name[:20] != _('Bank charge for bill') else _('Customer payment for bill ') + self.name,
            #             'date': payment_date,
            #             'journal_id': item.journal_id.id ,
            #             'currency_id': item.currency_id.id,
            #             'company_id': item.company_id.id,
            #             'company_currency_id': item.company_currency_id.id,
            #             'account_id': item.account_id.id,
            #             'amount_currency': total_amount * -1.0, #item.amount_currency * -1.0,
            #             'balance': total_amount_signed * -1, #item.balance * -1.0,
            #             'debit': abs(total_amount_signed) if self.type_bill == 'receivable' else 0, #item.credit if self.type_bill == 'receivable' else 0,
            #             'credit': 0 if self.type_bill == 'receivable' else abs(total_amount_signed), #0 if self.type_bill == 'receivable' else item.credit,
            #             'date_maturity': item.date_maturity,
            #         }
            #         vals.append(val)

            # TODO NO VA PORKE NO HAY REDONDEO CON DOS APUNTES SOLO DIFERENCIA DE CAMBIO
            # # Diferencia por redondeo
            # # Obtener el diario y las cuentas de redondeo desde la configuración
            # params = self.env['ir.config_parameter'].sudo()
            # round_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.round_boe_journal_id'))
            # round_journal = self.env['account.journal'].search([('id','=',round_boe_journal_id)])
            # # difference = 0
            # # if self.bill_currency_id != self.company_currency_id:
            # #     if payment_currency_id != self.bill_currency_id:
            # #         total_amount_currency = sum(item['amount_currency'] if item['debit'] else 0 for item in vals)
            # #         total_debit = sum(item['debit'] for item in vals)
            # #         difference = round(abs(total_amount_currency) * exchange_rate - abs(total_debit), 2)
            # total_credit = sum(item['credit'] for item in vals)
            # total_debit = sum(item['debit'] for item in vals)
            # difference = round(abs(total_credit) - abs(total_debit), 2)

            # if difference > 0:
            #     # Asiento de diferencia por redondeo ganancia
            #     val = {
            #         'name': _('Currency round difference'),
            #         'protest_payment_id': self.protest_payment_id.id,
            #         'debit': round(abs(difference),2) if self.type_bill == 'receivable' else  0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
            #         'credit': 0.0 if self.type_bill == 'receivable' else round(abs(difference),2), #if self.invoice_ids[0].type == 'out_invoice' else round(abs(total_debit - total_credit),2),
            #         'account_id': round_journal.default_debit_account_id.id if self.type_bill == 'receivable' else round_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
            #         'move_id': protest_payment_account_move.id,
            #         'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else '' ,
            #         'amount_currency': round(abs(difference) / self.exchange_rate,2) * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
            #         'balance': round(abs(difference),2) * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
            #         }
            #     vals.append(val)
            # if difference < 0:
            #     # Asiento de diferencia por redondeo perdida
            #     val = {
            #         'name': _('Currency round difference'),
            #         'protest_payment_id': self.protest_payment_id.id,
            #         'debit': 0.0 if self.type_bill == 'receivable' else round(abs(difference),2), #if self.invoice_ids[0].type == 'out_invoice' else abs(round(total_debit - total_credit,2)),
            #         'credit': round(abs(difference),2) if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
            #         'account_id': round_journal.default_credit_account_id.id if self.type_bill == 'receivable' else round_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
            #         'move_id': protest_payment_account_move.id,
            #         'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else '' ,
            #         'amount_currency': round(abs(difference) / self.exchange_rate,2) * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0.00,
            #         # 'partner_id': aml.partner_id.id,
            #         'balance': round(abs(difference),2) * (-1 if self.type_bill == 'receivable' else 1), # if self.company_currency_id.id != self.bill_currency_id.id else 0.00,
            #         }
            #     vals.append(val)
            # Diferencia de cambio
            # Obtener el diario y las cuentas de diferencia de cambio desde la configuración
            exchange_journal = self.env.company.currency_exchange_journal_id
            total_credit = round(sum(item['credit'] for item in vals),2)
            total_debit = round(sum(item['debit'] for item in vals),2)
            if total_credit > total_debit:
                # Asiento de diferencia de cambio por ganancia
                val = {
                    'name': _('Currency exchange rate difference'),
                    'protest_payment_id': self.protest_payment_id.id,
                    # 'exchange_rate': exchange_rate,
                    'debit': round(abs(total_debit - total_credit),2), # if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'credit': 0.0, # if self.type_bill == 'receivable' else round(abs(total_debit - total_credit),2), #if self.invoice_ids[0].type == 'out_invoice' else round(abs(total_debit - total_credit),2),
                    'account_id': exchange_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                    'move_id': protest_payment_account_move.id,
                    'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                    # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                    # 'amount_currency': round(abs(total_debit - total_credit) / exchange_rate,2) * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    # 'tc': exchange_rate,
                    'balance': round(abs(total_debit - total_credit),2) * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    }
                vals.append(val)
            if total_credit < total_debit:
                # Asiento de diferencia de cambio por perdida
                val = {
                    'name': _('Currency exchange rate difference'),
                    'protest_payment_id': self.protest_payment_id.id,
                    # 'exchange_rate': exchange_rate,
                    'debit': 0.0, # if self.type_bill == 'receivable' else abs(round(total_debit - total_credit,2)), #if self.invoice_ids[0].type == 'out_invoice' else abs(round(total_debit - total_credit,2)),
                    'credit': abs(round(total_debit - total_credit,2)), # if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'account_id': exchange_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                    'move_id': protest_payment_account_move.id,
                    'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                    # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                    # 'amount_currency': round(abs(total_debit - total_credit) / exchange_rate,2) * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0.00,
                    # 'tc': exchange_rate,
                    'balance': round(abs(total_debit - total_credit),2) * (-1 if self.type_bill == 'receivable' else 1),
                    }
                vals.append(val)
            # Si la letra ha sido importada borramos la linea, el objeto creado item
            if not self.account_move_line_ids:
                items.unlink()
            self.env['account.move.line'].create(vals)
            self.protest_payment_id.bill_last_state = self.last_state
            self.last_state = self.state_of_bill 
            self.protest_payment_id.last_account_id = self.account_id
            # self.last_account_id = self.account_id
            self.state_of_bill = 'paid'
            self.payment_date = payment_date
            self.protest_payment_id.account_move.action_post()
            # TODO Si se agregó la nota de debito al pago la cancelamos tambien
            if add_debit_note:
                line = self.protest_payment_id.account_move_line_ids.filtered(lambda l: self.protest_debit_note_id.ref in l.name)
                self.protest_debit_note_id.js_assign_outstanding_line(line.id)
            # Actualizar lineas por problemas con Libro Diario
            # for line in self.account_move.line_ids:
            #     line.tc = line.exchange_rate
            #     line.partner_id = self.responsable_id
            #     line.type_document_id = type_document_id
            #     line.nro_comp = self.bill_number
            #     line.invoice_date = self.bill_date_issue
            #     line.date_maturity = self.bill_date_due
            # Reconciliar asientos
            if self.account_move_line_ids:
                for line in self.account_move_line_ids:
                    if line.account_id.reconcile and not line.reconciled:
                        lines = line
                        filtered = self.protest_payment_id.account_move_line_ids.filtered(lambda l: l.account_id == lines[0].account_id and\
                            not l.reconciled and\
                            l.name == line.name)
                        if filtered:
                            lines += filtered[0]
                            break
                lines.reconcile()
            else:
                for line in self.send_form_id.account_move_line_ids:
                    # Si es una letra importada
                    if line.account_id.reconcile and not line.reconciled:
                        lines = line
                        filtered = self.protest_payment_id.account_move_line_ids.filtered(lambda l: l.account_id == lines[0].account_id and\
                            not l.reconciled and\
                            l.name == line.name)
                        if filtered:
                            lines += filtered[0]
                            break
                lines.reconcile()
            return {
                    # 'name': _('Protest Payment'),
                    'res_model': 'account.protest.payment',
                    'view_mode': 'form',
                    'view_id': self.env.ref('jp_account_bills_of_exchange.view_protest_payment_form').id,
                    'res_id': self.protest_payment_id.id,
                    'target': 'current',
                    'type': 'ir.actions.act_window',
                }
            
        payment_journal_id = self.env.context.get('payment_journal')
        payment_date = self.env.context.get('payment_date')
        payment_currency_id = self.env.context.get('payment_currency_id')
        payment_amount_wizard = self.env.context.get('payment_amount')
        payment_amount = payment_amount_wizard
        exchange_rate = self.env.context.get('exchange_rate') #round(self.get_rates(payment_date),3)
        operation_number = self.env.context.get('operation_number')
        if self.env.context.get('different_journal'):
            if payment_currency_id != self.bill_currency_id:
                payment_amount = round(payment_amount_wizard / exchange_rate, 2)        
        # Para pagos parciales
        total_partial_payments = payment_amount_signed =0
        for pp in self.partial_payment_ids:
            total_partial_payments += pp.payment_amount_signed
        # total_partial_payments += payment_amount
        if self.bill_currency_id != payment_currency_id:
            if payment_currency_id == self.env.company.currency_id:
                payment_amount_signed = float_round(payment_amount / exchange_rate, 2)
            else:
                payment_amount_signed = float_round(payment_amount * exchange_rate, 2)
        else:
            payment_amount_signed = payment_amount
        # if self.env.context.get('payment_amount') < self.bill_amount_total:
        if payment_amount_signed < round(self.bill_amount_total - total_partial_payments, 2):
            # raise UserError(_('Can\'t pay less than the original amount %s %s') %(self.bill_currency_id.name, self.bill_amount_total))
            val ={
                'name': self.env['ir.sequence'].next_by_code('account.bill.partial.payment'),
                'payment_date': payment_date,
                'bill_id': self.id,
                'currency_id': payment_currency_id.id,
                'payment_amount': payment_amount,
                'payment_amount_signed': payment_amount_signed,
                'journal_id': payment_journal_id.id,
                'operation_number': operation_number,
                'exchange_rate': exchange_rate,
            }
            partial_payment_id = self.env['account.bill.partial.payment'].create(val)
            partial_payment_id.create_move(self)
            return

        # Crear los asientos contables
        vals = []
        val = {}
        # Obtener el diario dependiendo del estado y si es importada o no
        if self.send_form_id:
            journal_id = self.send_form_id.journal_id.id
        else:
            if self.origin_bill_id:
                if self.origin_bill_id.send_form_id:
                    journal_id = self.origin_bill_id.send_form_id.journal_id.id
                else:
                    journal_id = self.origin_bill_id.bill_form_id.journal_id.id
            else:
                journal_id = self.bill_form_id.journal_id.id
        val = {
            'name': self.env['ir.sequence'].next_by_code('account.bill.payment'), #'PB-' + self.name,
            'currency_id': self.bill_currency_id.id,
            'currency_rate': exchange_rate,
            'date': payment_date,
            # 'invoice_date': payment_date,
            'invoice_date': self.bill_date_issue,
            'journal_id': journal_id, #self.bill_form_id.journal_id.id if self.bill_form_id.journal_id.id else self.origin_bill_id.bill_form_id.journal_id.id or self.origin_bill_id.send_form_id.journal_id.id,
            'glosa': _('Bill payment %s') %self.bill_number ,
            'type': 'bill',
        }
        self.account_move = self.env['account.move'].create(val)
        # Primero la linea del asiento de la letra o renovacion o responsabilidad
        # con el banco en caso de ser una letra en descuento
        if self.origin_bill_id or self.send_form_id:
            if self.origin_bill_id:
                if self.origin_bill_id.send_form_id.bank_position == 'discount' and self.origin_bill_id.send_form_id.state  in ('disbursed','imported'):
                    val_name = _('Bank Responsabillity %s') %self.bill_number
                    val_account_id = self.origin_bill_id.send_form_id.journal_id.default_credit_account_id.id
                else:
                    val_name = self.bill_number
                    val_account_id = self.account_id.id
            else:
                if self.send_form_id.bank_position == 'discount' and self.send_form_id.state in ('disbursed','imported'):
                    val_name = _('Bank Responsabillity %s') %self.bill_number
                    val_account_id = self.send_form_id.journal_id.default_credit_account_id.id
                else:
                    val_name = self.bill_number
                    val_account_id = self.account_id.id
        else:
            val_name = self.bill_number
            val_account_id = self.account_id.id
        # val_bill_amount_total_signed = float_round(self.bill_amount_total * (exchange_rate if self.bill_currency_id != self.env.company.currency_id else 1), 2) #val_exchange_rate
        partial_payment = 0
        for payment in self.partial_payment_ids:
            partial_payment += payment.payment_amount_signed
        val_bill_amount = self.bill_amount_total - partial_payment
        val_bill_amount_total_signed = float_round(val_bill_amount * (exchange_rate if self.bill_currency_id != self.env.company.currency_id else 1), 2) #val_exchange_rate
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
        type_document_id2 = self.env['einvoice.catalog.01'].search([('code','=','00')])
        val = {
            'ref': self.name,
            'bill_id': self.id,
            'partner_id': self.acceptor_id.id,
            'type_document_id': type_document_id.id,
            'nro_comp': self.bill_number,
            'move_id': self.account_move.id,
            'exchange_rate': exchange_rate, #self.exchange_rate, #if self.send_form_id.bank_position != 'discount' else exchange_rate,
            # 'name': _('Bank Responsabillity ' + self.bill_number),
            # 'name': self.bill_number if (self.origin_bill_id.send_form_id.bank_position if self.origin_bill_id else self.send_form_id.bank_position) != 'discount' and (self.origin_bill_id.send_form_id.state if self.origin_bill_id else self.send_form_id.state) != 'disbursed' else _('Bank Responsabillity ' + self.bill_number),
            'name': val_name,
            'date': payment_date,
            'journal_id': self.bill_form_id.journal_id.id if self.bill_form_id.journal_id.id else self.origin_bill_id.bill_form_id.journal_id.id,
            'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
            'company_id': self.company_id.id,
            'company_currency_id': self.company_currency_id.id,
            # 'account_id': self.account_id.id if (self.origin_bill_id.send_form_id.bank_position if self.origin_bill_id else self.send_form_id.bank_position) != 'discount' and (self.origin_bill_id.send_form_id.state if self.origin_bill_id else self.send_form_id.state) != 'disbursed' else self.origin_bill_id.send_form_id.journal_id.default_credit_account_id.id if self.origin_bill_id else self.send_form_id.journal_id.default_credit_account_id.id,
            'account_id': val_account_id,
            # 'amount_currency': self.bill_amount_total * (-1 if self.type_bill == 'receivable' and not self.state_of_bill == 'disbursed' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0,
            'amount_currency': val_bill_amount * (-1 if self.type_bill == 'receivable' and not self.state_of_bill == 'disbursed' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0,
            'tc': exchange_rate, #self.exchange_rate, #if self.send_form_id.bank_position != 'discount' else exchange_rate,
            'balance': val_bill_amount_total_signed * (-1 if self.type_bill == 'receivable' and not self.state_of_bill == 'disbursed' else 1), # if self.company_currency_id.id != self.bill_currency_id.id else 0,
            'debit': 0 if self.type_bill == 'receivable' and not self.state_of_bill == 'disbursed' else val_bill_amount_total_signed,
            'credit': val_bill_amount_total_signed if self.type_bill == 'receivable' and not self.state_of_bill == 'disbursed' else 0,
            'date_maturity': self.bill_date_due,
        }
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        # Actualizar si es una letra que no fue a descuento
        bank_pos = ''
        if self.origin_bill_id:
            if self.origin_bill_id.send_form_id.state not in ['draft','to_reconcile']:
                bank_pos = self.origin_bill_id.send_form_id.bank_position
        else:
            if self.send_form_id:
                if self.send_form_id.state not in ['draft','to_reconcile']:
                    bank_pos = self.send_form_id.bank_position
        if bank_pos != 'discount':
            val.update({
                'partner_id': self.responsable_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.bill_number,
            })
        vals.append(val)
        # Luego el pago del banco o la letra en descuento
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        # type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
        payment = float_round(payment_amount ,2)
        # #******************************* TODO SE COMENTA POR EL TIPO DE CAMBIO *****************************
        # # payment_signed = round(payment * exchange_rate,2)
        # # if self.env.context.get('different_journal'):
        # if payment_currency_id != self.bill_currency_id:
        #     if self.company_currency_id == payment_currency_id:
        #         # exchange_rate = round(self.get_rates_currency(payment_currency_id,payment_date), 3)
        #         payment_signed = round(payment_amount_wizard,2)
        #     else:
        #         if self.state_of_bill == 'disbursed':
        #             if self.origin_bill_id == self.renew_bill_id:
        #                 exchange_rate = self.origin_bill_id.send_form_id.exchange_rate #if exchange_rate == 0 else exchange_rate
        #             else:
        #                 exchange_rate = self.renew_bill_id.account_move_line_ids[0].exchange_rate if exchange_rate == 0 else exchange_rate
        #         else:
        #             exchange_rate = round(self.get_rates_currency(payment_currency_id,payment_date), 3) if exchange_rate == 0 else exchange_rate
        #         payment_signed = round(payment_amount_wizard * (exchange_rate * 1000), 2) / 1000
        # else:
        #     if self.company_currency_id == payment_currency_id:
        #         payment_signed = round(payment_amount_wizard,2)
        #     else:
        #         if self.state_of_bill == 'disbursed':
        #             if self.origin_bill_id:
        #                 # if self.origin_bill_id != self.renew_bill_id:
        #                 #     exchange_rate = self.origin_bill_id.send_form_id.exchange_rate
        #                 # else:
        #                 exchange_rate = self.renew_bill_id.account_move_line_ids[0].exchange_rate #if exchange_rate == 0 else exchange_rate
        #             else:
        #                 if self.bill_form_id:
        #                     exchange_rate = self.send_form_id.exchange_rate #if exchange_rate == 0 else exchange_rate
        #                 else:
        #                     exchange_rate = self.exchange_rate  if exchange_rate == 0 else exchange_rate
        #             payment_signed = round(payment_amount_wizard * (exchange_rate * 1000), 2) / 1000
        #         else:
        #             payment_signed = round(payment_amount_wizard * (exchange_rate * 1000), 2) / 1000
        # #******************************* TODO SE COMENTA POR EL TIPO DE CAMBIO *****************************
        if self.company_currency_id == payment_currency_id:
            payment_signed = float_round(payment_amount_wizard,2)
        else:
            # if self.state_of_bill == 'disbursed':
            #     if self.origin_bill_id:
            #         # if self.origin_bill_id != self.renew_bill_id:
            #         #     exchange_rate = self.origin_bill_id.send_form_id.exchange_rate
            #         # else:
            #         exchange_rate = self.renew_bill_id.account_move_line_ids[0].exchange_rate #if exchange_rate == 0 else exchange_rate
            #     else:
            #         if self.bill_form_id:
            #             exchange_rate = self.send_form_id.exchange_rate #if exchange_rate == 0 else exchange_rate
            #         else:
            #             exchange_rate = self.exchange_rate  if exchange_rate == 0 else exchange_rate
            #     payment_signed = round(payment_amount_wizard * (exchange_rate * 1000), 2) / 1000
            # else:
            payment_signed = float_round(payment_amount_wizard * exchange_rate, 2)
            
        val = {
            'ref': self.account_move.name,
            'bill_id': self.id,
            'partner_id': self.acceptor_id.id if self.type_bill == 'receivable' else self.creditor_id.id,
            'type_document_id': type_document_id.id if self.state_of_bill == 'disbursed' else type_document_id2.id,
            'nro_comp': self.bill_number if self.state_of_bill == 'disbursed' else operation_number,
            'move_id': self.account_move.id,
            'exchange_rate': exchange_rate,
            'name': self.bill_number if self.state_of_bill == 'disbursed' else _('Bank payment for bill %s' %self.name),
            'date': payment_date,
            'journal_id': payment_journal_id.id,
            'company_id': self.company_id.id,
            'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
            'company_currency_id': self.company_currency_id.id,
            'account_id': self.account_id.id if self.state_of_bill == 'disbursed' else payment_journal_id.default_credit_account_id.id,
            'amount_currency': payment * (1.0 if self.type_bill == 'receivable' and not self.state_of_bill == 'disbursed' else -1.0) if self.company_currency_id.id != payment_currency_id.id else 0,
            'tc': exchange_rate,
            'balance': payment_signed * (1.0 if self.type_bill == 'receivable' and not self.state_of_bill == 'disbursed' else -1.0),
            'debit': payment_signed if self.type_bill == 'receivable' and not self.state_of_bill == 'disbursed' else 0,
            'credit': 0 if self.type_bill == 'receivable' and not self.state_of_bill == 'disbursed' else payment_signed,
            'date_maturity': payment_date,
            'reconciled': False,
            }
        vals.append(val)
        # Diferencia por redondeo
        # Obtener el diario y las cuentas de redondeo desde la configuración
        params = self.env['ir.config_parameter'].sudo()
        round_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.round_boe_journal_id'))
        round_journal = self.env['account.journal'].search([('id','=',round_boe_journal_id)])
        # if self.company_currency_id.id != self.bill_currency_id.id:   
        #     total_amount_currency = sum(item['amount_currency'] if item['credit'] else 0 for item in vals)
        # else:
        #     total_amount_currency = sum(item['credit'] for item in vals)
        # # total_amount_currency = round(sum(item['amount_currency'] if item['credit'] else 0 for item in vals),2)
        # total_debit = round(sum(item['debit'] for item in vals),2)
        # # difference = round(total_amount_currency * self.exchange_rate - total_debit, 2)
        # if self.env.context.get('different_journal'):
        #     if payment_currency_id != self.bill_currency_id:
        #         if self.company_currency_id == payment_currency_id:
        #             exchange_rate = round(self.get_rates_currency(self.bill_currency_id,payment_date),3)
        #             total_amount_currency = payment_amount_wizard / exchange_rate
        #         else:
        #             exchange_rate = round(self.get_rates_currency(self.bill_currency_id,payment_date),3)
        #             total_amount_currency = payment_amount_wizard * exchange_rate
        # difference = round((abs(total_amount_currency) - payment_amount) * exchange_rate, 2)

        if self.bill_currency_id != self.company_currency_id:
            if payment_currency_id != self.bill_currency_id:
                total_amount_currency = sum(item['amount_currency'] if (item['credit'] if self.type_bill == 'receivable' else item['debit']) else 0 for item in vals)
                total_debit = sum(item['debit'] if self.type_bill == 'receivable' else item['credit'] for item in vals) / exchange_rate
                difference = round((abs(total_amount_currency) - abs(total_debit)) * exchange_rate, 2)
            else:
                total_amount_currency = sum(item['amount_currency'] if (item['credit'] if self.type_bill == 'receivable' else item['debit']) else 0 for item in vals)
                total_debit = sum(item['amount_currency'] if (item['debit'] if self.type_bill == 'receivable' else item['credit']) else 0 for item in vals)
                difference = round((abs(total_amount_currency) - abs(total_debit)) * exchange_rate, 2)
        else:
            total_amount_currency = sum(item['credit'] if self.type_bill == 'receivable' else item['debit'] for item in vals)
            total_debit = sum(item['debit'] if self.type_bill == 'receivable' else item['credit'] for item in vals)
            difference = round(abs(total_amount_currency) - abs(total_debit), 2)

        if float_round(difference,2) > 0:
            # Asiento de diferencia por redondeo ganancia
            val = {
                'name': _('Currency round difference'),
                'bill_id': self.id,
                # 'exchange_rate': exchange_rate,
                'debit': round(abs(difference),2) if self.type_bill == 'receivable' else  0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                'credit': 0.0 if self.type_bill == 'receivable' else round(abs(difference),2), #if self.invoice_ids[0].type == 'out_invoice' else round(abs(total_debit - total_credit),2),
                'account_id': round_journal.default_debit_account_id.id if self.type_bill == 'receivable' else round_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                'move_id': self.account_move.id,
                'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                'amount_currency': round(abs(difference) / self.exchange_rate,2) * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                # 'tc': exchange_rate,
                'balance': round(abs(difference),2) * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                }
            vals.append(val)
        if float_round(difference,2) < 0:
            # Asiento de diferencia por redondeo perdida
            val = {
                'name': _('Currency round difference'),
                'bill_id': self.id,
                # 'exchange_rate': exchange_rate,
                'debit': 0.0 if self.type_bill == 'receivable' else round(abs(difference),2), #if self.invoice_ids[0].type == 'out_invoice' else abs(round(total_debit - total_credit,2)),
                'credit': round(abs(difference),2) if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                'account_id': round_journal.default_credit_account_id.id if self.type_bill == 'receivable' else round_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                'move_id': self.account_move.id,
                'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                'amount_currency': round(abs(difference) / self.exchange_rate,2) * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0.00,
                # 'tc': exchange_rate,
                # 'partner_id': aml.partner_id.id,
                'balance': round(abs(difference),2) * (-1 if self.type_bill == 'receivable' else 1), # if self.company_currency_id.id != self.bill_currency_id.id else 0.00,
                }
            vals.append(val)
        # Diferencia de cambio
        # Obtener el diario y las cuentas de diferencia de cambio desde la configuración
        exchange_journal = self.env.company.currency_exchange_journal_id
        total_credit = round(sum(item['credit'] for item in vals),2)
        total_debit = round(sum(item['debit'] for item in vals),2)
        # if self.invoice_ids[0].type == 'out_invoice':
        if total_credit > total_debit:
            # Asiento de diferencia de cambio por ganancia
            val = {
                'name': _('Currency exchange rate difference'),
                'bill_id': self.id,
                # 'exchange_rate': exchange_rate,
                'debit': round(abs(total_debit - total_credit),2),# if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                'credit': 0.0, # if self.type_bill == 'receivable' else round(abs(total_debit - total_credit),2), #if self.invoice_ids[0].type == 'out_invoice' else round(abs(total_debit - total_credit),2),
                'account_id': exchange_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                'move_id': self.account_move.id,
                'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                # 'amount_currency': round(abs(total_debit - total_credit) / exchange_rate,2) * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                # 'tc': exchange_rate,
                'balance': round(abs(total_debit - total_credit),2) * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                }
            vals.append(val)
        if total_credit < total_debit:
            # Asiento de diferencia de cambio por perdida
            val = {
                'name': _('Currency exchange rate difference'),
                'bill_id': self.id,
                # 'exchange_rate': exchange_rate,
                'debit': 0.0, # if self.type_bill == 'receivable' else abs(round(total_debit - total_credit,2)), #if self.invoice_ids[0].type == 'out_invoice' else abs(round(total_debit - total_credit,2)),
                'credit': abs(round(total_debit - total_credit,2)), # if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                'account_id': exchange_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                'move_id': self.account_move.id,
                'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                # 'amount_currency': round(abs(total_debit - total_credit) / exchange_rate,2) * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0.00,
                # 'tc': exchange_rate,
                'balance': round(abs(total_debit - total_credit),2) * (-1 if self.type_bill == 'receivable' else 1),
                }
            vals.append(val)
        self.env['account.move.line'].create(vals)
        self.last_state = self.state_of_bill
        self.state_of_bill = 'paid'
        self.payment_date = payment_date
        self.account_move.action_post()
        # Actualizar lineas por problemas con Libro Diario
        # for line in self.account_move.line_ids:
        #     line.tc = line.exchange_rate
        #     line.partner_id = self.responsable_id
        #     line.type_document_id = type_document_id
        #     line.nro_comp = self.bill_number
        #     line.invoice_date = self.bill_date_issue
        #     line.date_maturity = self.bill_date_due
        # Reconciliar asientos
        # Si es una renovacion de una letra renovada
        if self.renew_bill_id.renew_bill_id:
            # for l in self.account_move_line_ids:
            #     print(l.name, l.account_id, l.credit)
            lines = self.account_move_line_ids.filtered(lambda l: l.name == self.bill_number and l.reconciled == False)
            # for line in self.account_move_line_ids:
            if lines.account_id.reconcile and not lines.reconciled:
                # lines = line
                filtered = self.renew_bill_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and\
                    not l.reconciled and\
                    l.name == lines.name)
                # ids =[]
                # for l in self.renew_bill_id.account_move_line_ids:
                #     if l.account_id == lines.account_id and\
                #     not l.reconciled and\
                #     l.name == lines.name:
                #         ids = l.id
                if filtered:
                    lines += filtered
        else:
            # Si es la primera renovacion
            if self.renew_bill_id:
                # for l in self.renew_bill_id.account_move_line_ids:
                #     print(l.name, l.account_id)
                lines = self.renew_bill_id.account_move_line_ids.filtered(lambda l: l.account_id == self.account_id and \
                    self.bill_number in l.name and \
                    l.reconciled == False)
                if lines.account_id.reconcile and not lines.reconciled:
                    # lines = line
                    filtered = self.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and\
                        not l.reconciled and\
                        l.name == lines.name and\
                        l.credit > 0)
                    if filtered:
                        lines += filtered
                        # break
            else:
                # for line in self.account_move_line_ids:
                # for l in self.account_move_line_ids:
                #     print(l.name, l.account_id, l.name == self.bill_number, l.account_id == self.account_id, l.reconciled == False)
                lines = self.account_move_line_ids.filtered(lambda l: l.account_id == self.account_id and \
                    l.name == self.bill_number and \
                    l.reconciled == False)
                if lines.account_id.reconcile and not lines.reconciled:
                    # lines = line
                    # Si es un desembolso
                    if self.send_form_id and self.send_form_id.state not in ['draft','to_reconcile']:
                        # for l in self.send_form_id.account_move_line_ids:
                        #     print(l.name, l.name == line.name[:7])
                        filtered = self.send_form_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and\
                            not l.reconciled and\
                            (l.name == lines.name or l.name == lines.name[:7]))
                        if filtered:
                            lines += filtered
                            # break
                    # Si es una letra en cartera o importada
                    else:
                        filtered = self.bill_form_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and\
                            not l.reconciled and\
                            (l.name == lines.name or l.name == lines.name[:7]))
                        if filtered:
                            lines += filtered
                            # break
        lines.reconcile()
        # Conciliar la responsabilidad si son de venta
        if self.type_bill == 'receivable':
            lines = self.account_move_line_ids.filtered(lambda l: l.account_id != self.account_id and self.bill_number in l.name and l.reconciled == False)
            # lines = self.account_move_line_ids.filtered(lambda l: l.account_id != self.account_id and l.reconciled == False)
            if self.send_form_id.bank_disbursement_id.id:
                lines += self.send_form_id.bank_disbursement_id.account_move_line_ids.filtered(lambda l: self.bill_number in l.name and l.reconciled == False)
            elif self.renew_bill_id:
                lines += self.renew_bill_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and \
                    self.bill_number in l.name and \
                    l.reconciled == False)
            else:
                # Conciliamos con la linea del asiento de importación
                import_form = self.env['account.import.bill.form'].search([('send_form_id','=', self.send_form_id.id if self.send_form_id else self.origin_bill_id.send_form_id.id)])
                account_move = import_form.account_move_ids.filtered(lambda am: self.bill_number in am.name or self.bill_number[:7] in am.name) #am.name.split('-')[0] == _('Bill import %s') %lines.ref + ' ' or am.name.split('-')[0] == _('Bill import %s') %lines.ref[:7] + ' ')
                lines += account_move.line_ids.filtered(lambda l: l.account_id == lines.account_id and self.bill_number in l.name or self.bill_number[:7] in l.name and l.credit > 0 and l.reconciled == False)
            lines.reconcile()

    def protest_bill_wizard(self):
        return self.env['financial.expenses.wizard']\
            .with_context(active_ids=self.ids, active_model='account.bill', active_id=self.id, disbursed=False if self.send_form_id and self.send_form_id.bank_position or self.origin_bill_id else True)\
            .get_financial_expenses()

    def protest_bill(self):
        #Validaciones
        expenses_journal_id = self.env.context.get('expenses_journal')
        protest_journal_id = self.env.context.get('protest_journal')
        financial_expenses = self.env.context.get('financial_expenses')
        bank_interests = self.env.context.get('bank_interests')
        protest_date = self.env.context.get('protest_date')
        # exchange_rate = round(self.get_rates(protest_date),3)
        exchange_rate = self.env.context.get('exchange_rate') if self.env.context.get('exchange_rate') > 0 else round(self.get_rates(protest_date),3)
        if self.env.context.get('different_journal'):
            if expenses_journal_id.currency_id != self.bill_currency_id:
                bank_interests = round(bank_interests / exchange_rate, 2)
                financial_expenses = round(financial_expenses / exchange_rate, 2)
        # Crear los asientos contables
        vals = []
        val = {}
        # Obtener el diario dependiendo del estado y si es importada o no
        if self.send_form_id:
            journal_id = self.send_form_id.journal_id.id
        else:
            if self.origin_bill_id:
                if self.origin_bill_id.send_form_id:
                    journal_id = self.origin_bill_id.send_form_id.journal_id.id
                else:
                    journal_id = self.origin_bill_id.bill_form_id.journal_id.id
            else:
                journal_id = self.bill_form_id.journal_id.id
        val = {
            'name': self.env['ir.sequence'].next_by_code('account.protest.bill'), #'PRB-' + self.name,
            'currency_id': self.bill_currency_id.id,
            'currency_rate': exchange_rate,
            'date': protest_date,
            # 'invoice_date': protest_date,
            'invoice_date': self.bill_date_issue,
            'journal_id': journal_id, #self.bill_form_id.journal_id.id if self.bill_form_id.journal_id.id else self.origin_bill_id.bill_form_id.journal_id.id if self.origin_bill_id else self.send_form_id.journal_id.id,
            'glosa': _('Protest bill %s') %self.bill_number,
            'type': 'bill',
        }
        self.account_move = self.env['account.move'].create(val)
        # payment = round(bank_interests ,2)
        # payment_signed = round(payment * exchange_rate,2)
        # total_amount_charged = round(self.bill_amount_total + payment, 2)
        # total_amount_charged_signed = round((self.bill_amount_total + payment) * exchange_rate, 2)
        payment = round(bank_interests ,2)
        payment_signed = round(payment * exchange_rate,2)
        total_amount_charged = self.bill_amount_total
        total_amount_charged_signed = round(round(self.bill_amount_total * exchange_rate,3), 2)
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
        if self.state_of_bill == 'disbursed':
            difference = 0
            # Primero el cargo al banco por la letra
            val = {
                'ref': self.name,
                'bill_id': self.id,
                'partner_id': self.responsable_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.bill_number,
                'move_id': self.account_move.id,
                'exchange_rate': exchange_rate,
                'name': _('Bank charge for bill %s' %self.name),
                'date': protest_date,
                'journal_id': expenses_journal_id.id,
                'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                'company_id': self.company_id.id,
                'company_currency_id': self.company_currency_id.id,
                'account_id': expenses_journal_id.default_credit_account_id.id,
                'amount_currency': total_amount_charged * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'tc': exchange_rate,
                'balance': total_amount_charged_signed * (-1 if self.type_bill == 'receivable' else 1), # if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'debit': 0 if self.type_bill == 'receivable' else total_amount_charged_signed,
                'credit': total_amount_charged_signed if self.type_bill == 'receivable' else 0,
                'date_maturity': protest_date,
            }
            vals.append(val)
            difference += abs(val['amount_currency']) * exchange_rate
            # Luego el cargo al banco por los intereses
            if payment > 0:
                val = {
                    'ref': self.name,
                    'bill_id': self.id,
                    'partner_id': self.responsable_id.id,
                    'type_document_id': type_document_id.id,
                    'nro_comp': self.bill_number,
                    'move_id': self.account_move.id,
                    'exchange_rate': exchange_rate,
                    'name': _('Bank charge for interests on bill %s' %self.name),
                    'date': protest_date,
                    'journal_id': expenses_journal_id.id,
                    'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                    'company_id': self.company_id.id,
                    'company_currency_id': self.company_currency_id.id,
                    'account_id': expenses_journal_id.default_credit_account_id.id,
                    'amount_currency': payment * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0,
                    'tc': exchange_rate,
                    'balance': payment_signed * (-1 if self.type_bill == 'receivable' else 1), # if self.company_currency_id.id != self.bill_currency_id.id else 0,
                    'debit': 0 if self.type_bill == 'receivable' else payment_signed,
                    'credit': payment_signed if self.type_bill == 'receivable' else 0,
                    'date_maturity': protest_date,
                }
                vals.append(val)
                difference += abs(val['amount_currency']) * exchange_rate
            # Luego la responsabilidad con el banco
            # Obtener el diario y las cuentas de gastos financieros desde la configuración
            params = self.env['ir.config_parameter'].sudo()
            protests_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.protests_boe_journal_id'))
            protests_journal = self.env['account.journal'].search([('id','=',protests_boe_journal_id)])
            # if self.origin_bill_id:
            #     if self.origin_bill_id.bill_form_id:
            #         exchange_rate_responsabillity = self.origin_bill_id.bill_form_id.exchange_rate
            #     if self.origin_bill_id.send_form_id:
            #         exchange_rate_responsabillity = self.origin_bill_id.send_form_id.exchange_rate
            #     if self.origin_bill_id.send_form_id.bank_disbursement_id:
            #         exchange_rate_responsabillity = self.origin_bill_id.send_form_id.bank_disbursement_id.account_move_line_ids[0].exchange_rate
            # else:
            #     exchange_rate_responsabillity = self.exchange_rate
            #exchange_rate_responsabillity = exchange_rate
            # exchange_rate_responsabillity = self.send_form_id.bank_disbursement_id.exchange_rate if self.send_form_id.bank_disbursement_id else self.exchange_rate
            val = {
                'ref': self.account_move.name,
                'bill_id': self.id,
                'partner_id': self.responsable_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.bill_number,
                'move_id': self.account_move.id,
                'exchange_rate': exchange_rate, #self.send_form_id.bank_disbursement_id.exchange_rate if self.state_of_bill == 'disbursed' else self.send_form_id.exchange_rate if self.send_form_id else self.bill_form_id.exchange_rate,
                'name': _('Bank Responsabillity %s') %self.name,
                'date': protest_date,
                'journal_id': journal_id, #self.bill_form_id.journal_id.id or self.origin_bill_id.bill_form_id.journal_id.id,
                'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                'company_id': self.company_id.id,
                'company_currency_id': self.company_currency_id.id,
                'account_id': self.origin_bill_id.send_form_id.journal_id.default_credit_account_id.id if self.origin_bill_id else self.send_form_id.journal_id.default_credit_account_id.id, #if self.send_form_id.bank_position != 'discount' else self.send_form_id.journal_id.default_credit_account_id.id,
                'amount_currency': self.bill_amount_total * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'tc': exchange_rate,
                'balance': round(round(self.bill_amount_total * exchange_rate,3),2) * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'debit': round(round(self.bill_amount_total * exchange_rate,3),2) if self.type_bill == 'receivable' else 0,
                'credit': 0 if self.type_bill == 'receivable' else round(round(self.bill_amount_total * exchange_rate,3),2),
                'date_maturity': self.bill_date_due,
                }
            vals.append(val)
            difference += abs(val['amount_currency']) * exchange_rate
            # Luego los intereses bancarios de la letra protestada
            # Obtener el diario y las cuentas de intereses bancarios desde la configuración
            params = self.env['ir.config_parameter'].sudo()
            protests_financial_expenses_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.protests_financial_expenses_boe_journal_id'))
            protests_financial_expenses_journal = self.env['account.journal'].search([('id','=',protests_financial_expenses_boe_journal_id)])
            if bank_interests>0:
                val = {
                    'ref': self.account_move.name,
                    'bill_id': self.id,
                    'partner_id': self.responsable_id.id,
                    'type_document_id': type_document_id.id,
                    'nro_comp': self.bill_number,
                    'move_id': self.account_move.id,
                    'exchange_rate': exchange_rate,
                    'name': _('Bank interests for bill %s' %self.name),
                    'date': protest_date,
                    'journal_id': journal_id, #self.bill_form_id.journal_id.id or self.origin_bill_id.bill_form_id.journal_id.id,
                    'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                    'company_id': self.company_id.id,
                    'company_currency_id': self.company_currency_id.id,
                    'account_id': protests_financial_expenses_journal.default_debit_account_id.id,
                    'amount_currency': payment * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0,
                    'tc': exchange_rate,
                    'balance': payment_signed * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0,
                    'debit': payment_signed if self.type_bill == 'receivable' else 0,
                    'credit': 0 if self.type_bill == 'receivable' else payment_signed,
                    'date_maturity': self.bill_date_due,
                    }
                vals.append(val)
                difference += abs(val['amount_currency']) * exchange_rate
            # Primero la letra en descuento
            # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
            # if self.state_of_bill == 'disbursed':
            #     exchange_rate_protest = self.send_form_id.exchange_rate
            # else:
            #     exchange_rate_protest = self.exchange_rate
            val = {
                'ref': self.name,
                'bill_id': self.id,
                'partner_id': self.responsable_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.bill_number,
                'move_id': self.account_move.id,
                'exchange_rate': exchange_rate,
                'name': self.bill_number,
                'date': protest_date,
                'journal_id': journal_id, #expenses_journal_id.id,
                'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                'company_id': self.company_id.id,
                'company_currency_id': self.company_currency_id.id,
                'account_id': self.account_id.id,
                'amount_currency': self.bill_amount_total * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'tc': exchange_rate,
                'balance': float_round(self.bill_amount_total * exchange_rate,2) * (-1 if self.type_bill == 'receivable' else 1), # if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'debit': 0 if self.type_bill == 'receivable' else float_round(self.bill_amount_total * exchange_rate,2),
                'credit': float_round(self.bill_amount_total * exchange_rate,2) if self.type_bill == 'receivable' else 0,
                'date_maturity': protest_date,
            }
            vals.append(val)
            difference += abs(val['amount_currency']) * exchange_rate
            # Luego la letra protestada
            # Obtener el diario de protestos desde la configuración
            # params = self.env['ir.config_parameter'].sudo()
            # protests_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.protests_boe_journal_id'))
            # protests_journal = self.env['account.journal'].search([('id','=',protests_boe_journal_id)])
            val = {
                'ref': self.account_move.name,
                'bill_id': self.id,
                'partner_id': self.responsable_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.bill_number,
                'move_id': self.account_move.id,
                'exchange_rate': exchange_rate,
                'name': self.bill_number, # if self.send_form_id.bank_position != 'discount' else _('Bank Responsabillity ' + self.bill_number),
                'date': protest_date,
                'journal_id': journal_id, #self.bill_form_id.journal_id.id or self.origin_bill_id.bill_form_id.journal_id.id,
                'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                'company_id': self.company_id.id,
                'company_currency_id': self.company_currency_id.id,
                'account_id': protest_journal_id.default_debit_account_id.id,
                'amount_currency': self.bill_amount_total * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'tc': exchange_rate,
                'balance': float_round(self.bill_amount_total * exchange_rate,2) * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'debit': float_round(self.bill_amount_total * exchange_rate,2) if self.type_bill == 'receivable' else 0,
                'credit': 0 if self.type_bill == 'receivable' else float_round(self.bill_amount_total * exchange_rate,2),
                'date_maturity': self.bill_date_due,
                }
            vals.append(val)
            difference += abs(val['amount_currency']) * exchange_rate
            # if self.bill_currency_id != self.company_currency_id:
            #     # Diferencia por redondeo
            #     # Obtener el diario y las cuentas de redondeo desde la configuración
            #     params = self.env['ir.config_parameter'].sudo()
            #     round_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.round_boe_journal_id'))
            #     round_journal = self.env['account.journal'].search([('id','=',round_boe_journal_id)]) 
            #     # if self.company_currency_id.id != self.bill_currency_id.id:   
            #     #     total_amount_currency = sum(item['amount_currency'] if item['credit'] else 0 for item in vals)
            #     # else:
            #     #     total_amount_currency = sum(item['credit'] for item in vals)
            #     # total_debit = sum(item['debit'] for item in vals)
            #     # difference = round((abs(total_amount_currency) * exchange_rate - total_debit), 2)
            #     # if self.company_currency_id.id != self.bill_currency_id.id:   
            #     #     total_amount_currency = sum(item['amount_currency'] if item['credit'] else 0 for item in vals)
            #     # else:
            #     #     total_amount_currency = sum(item['credit'] for item in vals)]
            #     total_debit = sum(item['debit'] for item in vals)
            #     total_credit = sum(item['credit'] for item in vals)
            #     difference = round(total_credit - total_debit, 2)
            #     if difference > 0:
            #         # Asiento de diferencia por redondeo ganancia
            #         val = {
            #             'name': _('Currency round difference'),
            #             'bill_id': self.id,
            #             'exchange_rate': exchange_rate,
            #             'debit': round(abs(difference),2) if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
            #             'credit': 0.0 if self.type_bill == 'receivable' else round(abs(difference),2), #if self.invoice_ids[0].type == 'out_invoice' else round(abs(total_debit - total_credit),2),
            #             'account_id': round_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
            #             'move_id': self.account_move.id,
            #             'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else '' ,
            #             'amount_currency': round(abs(difference) / exchange_rate,2) * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
            #             'tc': exchange_rate,
            #             'balance': round(abs(difference),2) * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
            #             }
            #         vals.append(val)
            #     if difference < 0:
            #         # Asiento de diferencia por redondeo perdida
            #         val = {
            #             'name': _('Currency round difference'),
            #             'bill_id': self.id,
            #             'exchange_rate': exchange_rate,
            #             'debit': 0.0 if self.type_bill == 'receivable' else round(abs(difference),2), #if self.invoice_ids[0].type == 'out_invoice' else abs(round(total_debit - total_credit,2)),
            #             'credit': round(abs(difference),2) if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
            #             'account_id': round_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
            #             'move_id': self.account_move.id,
            #             'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else '' ,
            #             'amount_currency': round(abs(difference) / exchange_rate,2) * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0.00,
            #             'tc': exchange_rate,
            #             # 'partner_id': aml.partner_id.id,
            #             'balance': round(abs(difference),2) * (-1 if self.type_bill == 'receivable' else 1), # if self.company_currency_id.id != self.bill_currency_id.id else 0.00,
            #             }
            #         vals.append(val)
        else:
            # Primero la letra en cartera o cobranza
            # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
            type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
            val = {
                'ref': self.name,
                'bill_id': self.id,
                'partner_id': self.responsable_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.bill_number,
                'move_id': self.account_move.id,
                'exchange_rate': exchange_rate,
                'name': self.bill_number,
                'date': protest_date,
                'journal_id': journal_id, #expenses_journal_id.id,
                'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                'company_id': self.company_id.id,
                'company_currency_id': self.company_currency_id.id,
                'account_id': self.account_id.id,
                'amount_currency': self.bill_amount_total * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'tc': exchange_rate,
                'balance': float_round(self.bill_amount_total * exchange_rate, 2) * (-1 if self.type_bill == 'receivable' else 1), # if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'debit': 0 if self.type_bill == 'receivable' else float_round(self.bill_amount_total * exchange_rate, 2),
                'credit': float_round(self.bill_amount_total * exchange_rate, 2) if self.type_bill == 'receivable' else 0,
                'date_maturity': protest_date,
            }
            vals.append(val)
            # Luego la letra protestada
            # Obtener el diario de protestos desde la configuración
            # params = self.env['ir.config_parameter'].sudo()
            # protests_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.protests_boe_journal_id'))
            # protests_journal = self.env['account.journal'].search([('id','=',protests_boe_journal_id)])
            val = {
                'ref': self.account_move.name,
                'bill_id': self.id,
                'partner_id': self.responsable_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.bill_number,
                'move_id': self.account_move.id,
                'exchange_rate': exchange_rate,
                'name': self.bill_number, # if self.send_form_id.bank_position != 'discount' else _('Bank Responsabillity ' + self.bill_number),
                'date': protest_date,
                'journal_id': journal_id, #self.bill_form_id.journal_id.id or self.origin_bill_id.bill_form_id.journal_id.id,
                'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                'company_id': self.company_id.id,
                'company_currency_id': self.company_currency_id.id,
                'account_id': protest_journal_id.default_debit_account_id.id if self.type_bill == 'receivable' else protest_journal_id.default_credit_account_id.id,
                'amount_currency': self.bill_amount_total * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'tc': exchange_rate,
                'balance': float_round(self.bill_amount_total * exchange_rate,2) * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'debit': float_round(self.bill_amount_total * exchange_rate,2) if self.type_bill == 'receivable' else 0,
                'credit': 0 if self.type_bill == 'receivable' else float_round(self.bill_amount_total * exchange_rate,2),
                'date_maturity': self.bill_date_due,
                }
            vals.append(val)
        if self.bill_currency_id != self.company_currency_id:
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
                    'bill_id': self.id,
                    # 'exchange_rate': exchange_rate,
                    'debit': float_round(abs(total_debit - total_credit),2), # if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'credit': 0.0, # if self.type_bill == 'receivable' else float_round(abs(total_debit - total_credit),2), #if self.invoice_ids[0].type == 'out_invoice' else float_round(abs(total_debit - total_credit),2),
                    'account_id': exchange_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                    'move_id': self.account_move.id,
                    'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                    # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                    # 'amount_currency': float_round(abs(total_debit - total_credit) / exchange_rate,2) * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    # 'tc': exchange_rate,
                    'balance': float_round(abs(total_debit - total_credit),2) * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    }
                vals.append(val)
            if total_credit < total_debit:
                # Asiento de diferencia de cambio por perdida
                val = {
                    'name': _('Currency exchange rate difference'),
                    'bill_id': self.id,
                    # 'exchange_rate': exchange_rate,
                    'debit': 0.0, # if self.type_bill == 'receivable' else abs(float_round(total_debit - total_credit,2)), #if self.invoice_ids[0].type == 'out_invoice' else abs(float_round(total_debit - total_credit,2)),
                    'credit': abs(float_round(total_debit - total_credit,2)), # if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'account_id': exchange_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                    'move_id': self.account_move.id,
                    'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                    # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                    # 'amount_currency': float_round(abs(total_debit - total_credit) / exchange_rate,2) * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0.00,
                    # 'tc': exchange_rate,
                    'balance': float_round(abs(total_debit - total_credit),2) * (-1 if self.type_bill == 'receivable' else 1),
                    }
                vals.append(val)
        self.env['account.move.line'].create(vals)
        self.last_state = self.state_of_bill
        self.state_of_bill = 'protested'
        self.last_account_id = self.account_id
        self.account_id = protest_journal_id.default_debit_account_id
        self.account_move.action_post()
        # Actualizar lineas por problemas con Libro Diario
        # for line in self.account_move.line_ids:
        #     line.tc = line.exchange_rate
        #     line.partner_id = self.responsable_id
        #     line.type_document_id = type_document_id
        #     line.nro_comp = self.bill_number
        #     line.invoice_date = self.bill_date_issue
        #     line.date_maturity = self.bill_date_due
        # Reconciliar asientos
        # for line in self.account_move_line_ids:
        lines = self.account_move_line_ids.filtered(lambda l: l.name == self.bill_number and l.reconciled == False and l.credit > 0)
        if lines.account_id.reconcile:
            if self.renew_bill_id:
                filtered = self.renew_bill_id.account_move_line_ids.filtered(lambda l: l.account_id == lines[0].account_id and\
                    not l.reconciled and\
                    l.name == lines.name)
                if filtered:
                    lines += filtered[0]
                lines.reconcile()
            else:
                if self.send_form_id:
                    filtered = self.send_form_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and\
                        not l.reconciled and\
                        (l.name == lines.name or l.name == lines.name[:7]))
                    if filtered:
                        lines += filtered
                else:
                    filtered = self.bill_form_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and\
                        not l.reconciled and\
                        self.bill_number == l.name)
                    if filtered:
                        lines += filtered
                lines.reconcile()
        # Conciliar la responsabilidad
        # lines = self.account_move_line_ids.filtered(lambda l: l.name[:20] == _('Bank Responsabillity'))
        lines = self.account_move_line_ids.filtered(lambda l: l.account_id == (self.send_form_id.journal_id.default_credit_account_id if self.send_form_id else self.origin_bill_id.send_form_id.journal_id.default_credit_account_id) and l.reconciled == False)
        if self.send_form_id.bank_disbursement_id.id:
            lines += self.send_form_id.bank_disbursement_id.account_move_line_ids.filtered(lambda l: self.bill_number in l.name and l.reconciled == False)
        elif self.renew_bill_id:
            lines += self.renew_bill_id.account_move_line_ids.filtered(lambda l: self.bill_number in l.name and l.account_id == lines.account_id and l.reconciled == False)
        else:
            # Conciliamos con la linea del asiento de importación
            import_form = self.env['account.import.bill.form'].search([('send_form_id','=', self.send_form_id.id if self.send_form_id else self.origin_bill_id.send_form_id.id)])
            account_move = import_form.account_move_ids.filtered(lambda am: self.bill_number in am.name or self.bill_number[:7] in am.name) #am.name.split('-')[0] == _('Bill import %s') %lines.display_name + ' ')
            # for l in account_move.line_ids:
            #     print(l.name, self.bill_number, self.bill_number in l.name, self.bill_number[:7] in l.name)
            # for l in account_move.line_ids:
            #     print(l.name, l.account_id, lines.account_id, self.bill_number, l.credit, l.reconciled)
            lines += account_move.line_ids.filtered(lambda l: (self.bill_number in l.name or \
                self.bill_number[:7] in l.name) and \
                l.credit > 0 and \
                l.account_id == lines.account_id and \
                l.reconciled == False)
        lines.reconcile()

        # lines = self.renew_bill_id.account_move_line_ids.filtered(lambda l: l.account_id.id == account[0] and l.debit > 0)
        # if self.renew_bill_id.send_form_id.bank_disbursement_id:
        #     lines += self.renew_bill_id.send_form_id.bank_disbursement_id.account_move_line_ids.filtered(lambda l: l.name == lines.name)
        # elif self.renew_bill_id.renew_bill_id:
        #     lines += self.renew_bill_id.renew_bill_id.account_move_line_ids.filtered(lambda l: l.name[:24] == _('New Bank Responsabillity'))
        # else:
        #     # Conciliamos con la linea del asiento de importación
        #     import_form = self.env['account.import.bill.form'].search([('send_form_id','=', self.origin_bill_id.send_form_id.id)])
        #     account_move = import_form.account_move_ids.filtered(lambda am: am.name.split('-')[0] == _('Bill import %s') %lines.ref + ' ' or am.name.split('-')[0] == _('Bill import %s') %lines.ref[:7] + ' ')
        #     lines += account_move.line_ids.filtered(lambda l: l.name == lines.name or l.name == lines.name[:28] and l.credit > 0)
        # lines.reconcile()

        # Luego verifiacmos si creamos un asiento mas por separado para los portes y comisiones
        # de las letras descontadas
        if financial_expenses > 0 and self.last_state == 'disbursed':
            # Crear los asientos contables
            vals = []
            val = {}
            val = {
                'name': self.account_move.name + '-A',
                'currency_id': self.bill_currency_id.id,
                'currency_rate': exchange_rate,
                'date': protest_date,
                'invoice_date': self.bill_date_issue,
                'journal_id': self.bill_form_id.journal_id.id if self.bill_form_id else (self.send_form_id.journal_id.id if self.send_form_id else(self.origin_bill_id.bill_form_id.journal_id.id if self.origin_bill_id.bill_form_id else self.origin_bill_id.send_form_id.journal_id.id)),
                'glosa': _('Financial expenses for protest bill %s') %self.bill_number,
                'type': 'bill',
            }
            self.account_move_bank_interests_id = self.env['account.move'].create(val)
            payment = float_round(financial_expenses ,2)
            payment_signed = float_round(payment * exchange_rate,2)
            # Luego los gastos financieros de la letra protestada
            # Obtener el diario y las cuentas de gastos financieros desde la configuración
            params = self.env['ir.config_parameter'].sudo()
            protests_financial_expenses_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.protests_financial_expenses_boe_journal_id'))
            protest_financial_expenses_journal = self.env['account.journal'].search([('id','=',protests_financial_expenses_boe_journal_id)])
            val = {
                # 'ref': self.account_move_bank_interests_id.name,
                'partner_id': expenses_journal_id.bank_partner_id.id, #self.responsable_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.bill_number,
                'move_id': self.account_move_bank_interests_id.id,
                'exchange_rate': exchange_rate,
                'name': _('Financial expenses for bill %s' %self.name),
                'date': protest_date,
                'journal_id': self.bill_form_id.journal_id.id or self.origin_bill_id.bill_form_id.journal_id.id,
                'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                'company_id': self.company_id.id,
                'company_currency_id': self.company_currency_id.id,
                'account_id': protest_financial_expenses_journal.default_debit_account_id.id,
                'amount_currency': payment * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'tc': exchange_rate,
                'balance': payment_signed * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'debit': payment_signed if self.type_bill == 'receivable' else 0,
                'credit': 0 if self.type_bill == 'receivable' else payment_signed,
                'date_maturity': self.bill_date_due,
                }
            vals.append(val)
            # Luego el cargo al banco
            val = {
                # 'ref': self.name,
                'partner_id': self.responsable_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.bill_number,
                'move_id': self.account_move_bank_interests_id.id,
                'exchange_rate': exchange_rate,
                'name': _('Bank charge for financial expenses %s' %self.name),
                'date': protest_date,
                'journal_id': expenses_journal_id.id,
                'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                'company_id': self.company_id.id,
                'company_currency_id': self.company_currency_id.id,
                'account_id': expenses_journal_id.default_credit_account_id.id,
                'amount_currency': payment * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'tc': exchange_rate,
                'balance': payment_signed * (-1 if self.type_bill == 'receivable' else 1), # if self.company_currency_id.id != self.bill_currency_id.id else 0,
                'debit': 0 if self.type_bill == 'receivable' else payment_signed,
                'credit': payment_signed if self.type_bill == 'receivable' else 0,
                'date_maturity': self.bill_date_due,
            }
            vals.append(val)
            self.env['account.move.line'].create(vals)
            self.account_move_bank_interests_id.action_post()

    def get_renew_date(self):
        return self.env['renew.date.wizard']\
            .with_context(active_ids=self.ids, active_model='account.bill', active_id=self.id, type_bill=True if self.type_bill == 'receivable' else False)\
            .get_date()

    def renew_one_bill(self):
        return {
            'name': _('Renew bill %s') %self.name,
            'res_model': 'renew.bill.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jp_account_bills_of_exchange.view_renew_bill_wizard').id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def renew_bill(self):
        renew_journal_id = self.env.context.get('renew_journal_id')
        renew_financial_expenses = self.env.context.get('renew_financial_expenses')
        # renew_currency_id = self.env.context.get('renew_currency_id')
        exchange_rate = round(self.get_rates(self.renew_date),3)
        if renew_journal_id.currency_id != self.bill_currency_id:
            renew_financial_expenses = round(renew_financial_expenses / exchange_rate, 2)
        if renew_journal_id.currency_id != self.company_currency_id:
            renew_financial_expenses_signed = round(renew_financial_expenses * exchange_rate,2)
        else:
            renew_financial_expenses_signed = 0
        vals = []
        val = {}
        # Se generan 2 asientos, uno por el pago de la renovacion y el otro por la cancelacion
        # de la letra antigua y por la generacion de la nueva letra
        # Primero el Asiento del pago del porcentaje renovado en la letra antigua
        val = {
            'name': self.env['ir.sequence'].next_by_code('account.renew.bill'), #'RB-' + self.name,
            'currency_id': self.bill_currency_id.id,
            'currency_rate': exchange_rate,
            'date': self.renew_date,
            'invoice_date': self.renew_date,
            'journal_id': self.bill_form_id.journal_id.id if self.bill_form_id.journal_id.id else self.origin_bill_id.bill_form_id.journal_id.id if self.origin_bill_id.bill_form_id else self.origin_bill_id.send_form_id.journal_id.id,
            'glosa': _('Payment of renewal bill %s') %self.renew_bill_id.bill_number,
            'type': 'bill',
        }
        self.renew_bill_id.renew_payment_id = self.env['account.move'].create(val)
        # Hallamos el monto de la renovacion en moneda de la empresa
        difference = self.renew_bill_id.bill_amount_total - self.bill_amount_total
        difference_signed = round(difference * exchange_rate,2)
        # Linea del pago disminuye por el monto de la nueva letratype_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
        val = {
            'ref': self.name,
            # 'bill_id': self.renew_bill_id.id,
            'partner_id': self.responsable_id.id,
            'type_document_id': type_document_id.id,
            'nro_comp': self.renew_bill_id.bill_number,
            'move_id': self.renew_bill_id.renew_payment_id.id,
            'exchange_rate': exchange_rate,
            'name': self.renew_bill_id.bill_number,
            'date': self.renew_date,
            'journal_id': self.origin_bill_id.bill_form_id.journal_id.id,
            'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
            'company_id': self.company_id.id,
            'company_currency_id': self.company_currency_id.id,
            'account_id': self.renew_bill_id.account_id.id,
            'debit': difference_signed if self.type_bill != 'receivable' else 0,
            'amount_currency': difference * (1.0 if self.type_bill != 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0,
            'tc': exchange_rate,
            'balance': difference_signed * (1.0 if self.type_bill != 'receivable' else -1.0),
            'credit': 0 if self.type_bill != 'receivable' else difference_signed,
            'date_maturity': self.bill_date_due,
        }
        vals.append(val)
        # Linea de la responsabilidad
        # if self.last_state == 'disbursed':
        name = ('Bank Responsabillity %s') %self.renew_bill_id.name
        account = self.origin_bill_id.send_form_id.journal_id.default_credit_account_id.id if self.type_bill == 'receivable' else renew_journal_id.default_credit_account_id.id,
        # else:
        #     name = _('Bank payment for bill %s' %self.renew_bill_id.name)
        #     account = renew_journal_id.default_debit_account_id.id,
        val = {
            'ref': self.renew_bill_id.name,
            # 'bill_id': self.renew_bill_id.id,
            'partner_id': self.responsable_id.id,
            'type_document_id': type_document_id.id,
            'nro_comp': self.renew_bill_id.bill_number,
            'move_id': self.renew_bill_id.renew_payment_id.id,
            'exchange_rate': exchange_rate,
            'name': name,
            'date': self.renew_date,
            'journal_id': self.origin_bill_id.send_form_id.journal_id.id if self.type_bill == 'receivable' else renew_journal_id.id,
            'company_id': self.renew_bill_id.company_id.id,
            'currency_id': self.renew_bill_id.bill_currency_id.id if self.renew_bill_id.company_currency_id.id != self.renew_bill_id.bill_currency_id.id else False,
            'company_currency_id': self.renew_bill_id.company_currency_id.id,
            'account_id': account[0],
            'amount_currency': (difference) * (1.0 if self.type_bill == 'receivable' else -1.0) if self.renew_bill_id.company_currency_id.id != self.renew_bill_id.bill_currency_id.id else 0,
            'tc': exchange_rate,
            'balance': (difference_signed) * (1.0 if self.type_bill == 'receivable' else -1.0),
            'debit': (difference_signed) if self.type_bill == 'receivable' else 0,
            'credit': 0 if self.type_bill == 'receivable' else (difference_signed),
            'date_maturity': self.renew_date,
            }
        vals.append(val)
        # Creamos las lineas del asiento
        self.env['account.move.line'].create(vals)
        self.renew_bill_id.renew_payment_id.post()
        # Conciliar lineas del pago
        if self.renew_bill_id.renew_bill_id:
            # for l in self.renew_bill_id.renew_payment_id.line_ids:
            #     print(l.name, l.account_id, l.credit)
            lines = self.renew_bill_id.renew_payment_id.line_ids.filtered(lambda l: l.name == self.renew_bill_id.bill_number and\
                l.account_id == self.renew_bill_id.account_id and\
                l.credit > 0)
            if lines.account_id.reconcile and not lines.reconciled:
                # for l in self.renew_bill_id.renew_bill_id.account_move_line_ids:
                #     print(l.name, l.account_id, l.credit)
                filtered = self.renew_bill_id.renew_bill_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and\
                    not l.reconciled and\
                    l.name == lines.name)
                if filtered:
                    lines += filtered
        else:
            lines = self.renew_bill_id.renew_payment_id.line_ids.filtered(lambda l: l.name == self.renew_bill_id.bill_number and\
                l.account_id == self.renew_bill_id.account_id and\
                l.credit > 0 and \
                not l.reconciled)
            # if lines.account_id.reconcile and not lines.reconciled:
            if self.renew_bill_id.send_form_id.bank_disbursement_id:
                filtered = self.renew_bill_id.send_form_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and\
                    not l.reconciled and\
                    l.name == lines.name)
            else:
                filtered = self.renew_bill_id.send_form_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and\
                    not l.reconciled and\
                    (l.name == lines.name or l.name == lines.name[:7]))
                # for l in self.renew_bill_id.send_form_id.account_move_line_ids:
                #     print(l.name, lines.name, l.account_id, self.bill_number, lines.account_id, l.reconciled)
                # print(filtered.account_id == lines.account_id, filtered.reconciled == lines.reconciled, filtered.name == lines.name[:7])
            if filtered:
                lines += filtered
        lines.reconcile()
        # return
        # Conciliar la responsabilidad
        lines = self.renew_bill_id.renew_payment_id.line_ids.filtered(lambda l: l.account_id.id == account[0])
        if self.renew_bill_id.send_form_id.bank_disbursement_id:
            lines += self.renew_bill_id.send_form_id.bank_disbursement_id.account_move_line_ids.filtered(lambda l: l.name == lines.name)
        elif self.renew_bill_id.renew_bill_id:
            for l in self.renew_bill_id.renew_bill_id.account_move_line_ids:
                print(l.name, lines.name)
            lines += self.renew_bill_id.renew_bill_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and not l.reconciled and l.credit > 0)
        else:
            # Conciliamos con la linea del asiento de importación
            import_form = self.env['account.import.bill.form'].search([('send_form_id','=', self.origin_bill_id.send_form_id.id)])
            account_move = import_form.account_move_ids.filtered(lambda am: self.renew_bill_id.bill_number in am.name or self.renew_bill_id.bill_number[:7] in am.name) # am.name.split('-')[0] == _('Bill import %s') %lines.ref + ' ' or am.name.split('-')[0] == _('Bill import %s') %lines.ref[:7] + ' ')
            # for l in account_move.line_ids:
            #     print(l.id, l.name, l.account_id, self.bill_number, lines.account_id)
            lines += account_move.line_ids.filtered(lambda l: (self.renew_bill_id.bill_number in l.name or self.renew_bill_id.bill_number[:7] in l.name) and l.account_id == lines.account_id and l.credit > 0)
        lines.reconcile()
        # Segundo el Asiento de la renovacion en la letra antigua
        vals = []
        val = {}
        val = {
            'name': self.env['ir.sequence'].next_by_code('account.renew.bill'), #'RB-' + self.name,
            'currency_id': self.bill_currency_id.id,
            'currency_rate': exchange_rate,
            'date': self.renew_date,
            'invoice_date': self.renew_date,
            'journal_id': self.bill_form_id.journal_id.id if self.bill_form_id.journal_id.id else self.origin_bill_id.bill_form_id.journal_id.id if self.origin_bill_id.bill_form_id else self.origin_bill_id.send_form_id.journal_id.id,
            'glosa': _('Renewal bill %s') %self.bill_number,
            'type': 'bill',
        }
        self.renew_bill_id.account_move = self.env['account.move'].create(val)
        # Hallamos el saldo de la letra renovada
        difference = self.bill_amount_total
        difference_signed = round(difference * exchange_rate,2)
        # Primero la linea del asiento de la renovacion
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
        val = {
            'ref': self.name,
            'bill_id': self.renew_bill_id.id,
            'partner_id': self.responsable_id.id,
            'type_document_id': type_document_id.id,
            'nro_comp': self.bill_number,
            'move_id': self.renew_bill_id.account_move.id,
            'exchange_rate': exchange_rate,
            'name': self.bill_number,
            'date': self.renew_date,
            'journal_id': self.origin_bill_id.bill_form_id.journal_id.id,
            'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
            'company_id': self.company_id.id,
            'company_currency_id': self.company_currency_id.id,
            'account_id': self.renew_bill_id.account_id.id,
            'debit': difference_signed if self.type_bill == 'receivable' else 0,
            'amount_currency': difference * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0, #self.bill_amount_total * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0,
            'tc': exchange_rate,
            'balance': difference_signed * (1.0 if self.type_bill == 'receivable' else -1.0),
            'credit': 0 if self.type_bill == 'receivable' else difference_signed,
            'date_maturity': self.bill_date_due,
        }
        vals.append(val)
        # Luego el pago del banco o la responsabilidad si es desembolso
        # if self.last_state == 'disbursed':
        name = _('Bank Responsabillity %s') %self.renew_bill_id.name
        account = self.origin_bill_id.send_form_id.journal_id.default_credit_account_id.id if self.type_bill == 'receivable' else renew_journal_id.default_credit_account_id.id,
        # else:
        #     name = _('Bank payment for bill %s' %self.renew_bill_id.name)
        #     account = renew_journal_id.default_debit_account_id.id,
        val = {
            'ref': self.renew_bill_id.name,
            'bill_id': self.renew_bill_id.id,
            'partner_id': self.responsable_id.id,
            'type_document_id': type_document_id.id,
            'nro_comp': self.renew_bill_id.bill_number,
            'move_id': self.renew_bill_id.account_move.id,
            'exchange_rate': exchange_rate,
            'name': name,
            'date': self.renew_date,
            'journal_id': self.origin_bill_id.send_form_id.journal_id.id if self.type_bill == 'receivable' else renew_journal_id.id,
            'company_id': self.renew_bill_id.company_id.id,
            'currency_id': self.renew_bill_id.bill_currency_id.id if self.renew_bill_id.company_currency_id.id != self.renew_bill_id.bill_currency_id.id else False,
            'company_currency_id': self.renew_bill_id.company_currency_id.id,
            'account_id': account[0],
            'amount_currency': (difference) * (1.0 if self.type_bill == 'receivable' else -1.0) if self.renew_bill_id.company_currency_id.id != self.renew_bill_id.bill_currency_id.id else 0,
            'tc': exchange_rate,
            'balance': (difference_signed) * (1.0 if self.type_bill == 'receivable' else -1.0),
            'debit': (difference_signed) if self.type_bill == 'receivable' else 0,
            'credit': 0 if self.type_bill == 'receivable' else (difference_signed),
            'date_maturity': self.renew_date,
            }
        vals.append(val)
        # Luego otra linea para la antigua responsabilidad solo si es desembolso
        # if self.last_state == 'disbursed':
        name = _('New Bank Responsabillity %s') %self.name
        account = self.origin_bill_id.send_form_id.journal_id.default_credit_account_id.id if self.type_bill == 'receivable' else renew_journal_id.default_credit_account_id.id,
        renew_amount = self.bill_amount_total
        renew_exchange_rate = exchange_rate
        if self.bill_currency_id != self.company_currency_id:
            renew_amount_signed = round(renew_amount * renew_exchange_rate,2)
        else:
            renew_amount_signed = renew_amount
        val = {
            'ref': self.renew_bill_id.name,
            'bill_id': self.renew_bill_id.id,
            'partner_id': self.responsable_id.id,
            'type_document_id': type_document_id.id,
            'nro_comp': self.bill_number,
            'move_id': self.renew_bill_id.account_move.id,
            'exchange_rate': exchange_rate,
            'name': name,
            'date': self.renew_date,
            'journal_id': self.origin_bill_id.send_form_id.journal_id.id if self.type_bill == 'receivable' else renew_journal_id.id,
            'company_id': self.renew_bill_id.company_id.id,
            'currency_id': self.renew_bill_id.bill_currency_id.id if self.renew_bill_id.company_currency_id.id != self.renew_bill_id.bill_currency_id.id else False,
            'company_currency_id': self.renew_bill_id.company_currency_id.id,
            'account_id': account[0],
            'amount_currency': (renew_amount) * (1.0 if self.type_bill != 'receivable' else -1.0) if self.renew_bill_id.company_currency_id.id != self.renew_bill_id.bill_currency_id.id else 0,
            'tc': exchange_rate,
            'balance': renew_amount_signed * (1.0 if self.type_bill != 'receivable' else -1.0),
            'debit': renew_amount_signed if self.type_bill != 'receivable' else 0,
            'credit': 0 if self.type_bill != 'receivable' else renew_amount_signed,
            'date_maturity': self.renew_date,
            }
        vals.append(val)
        # Luego los gastos financieros de la renovación solo si es una letra por pagar
        # Obtener el diario y las cuentas de gastos financieros desde la configuración
        if self.type_bill == 'payable':
            params = self.env['ir.config_parameter'].sudo()
            protests_financial_expenses_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.protests_financial_expenses_boe_journal_id'))
            protest_financial_expenses_journal = self.env['account.journal'].search([('id','=',protests_financial_expenses_boe_journal_id)])
            if renew_journal_id.currency_id != self.company_currency_id:
                renew_financial_expenses_signed = round(renew_financial_expenses * exchange_rate,2)
            if renew_financial_expenses_signed>0:
                val = {
                    'ref': self.account_move.name,
                    'bill_id': self.renew_bill_id.id,
                    'move_id': self.renew_bill_id.account_move.id,
                    'exchange_rate': exchange_rate,
                    'name': _('Financial expenses for bill %s' %self.name),
                    'date': self.renew_date,
                    'journal_id': renew_journal_id.id,
                    'company_id': self.renew_bill_id.company_id.id,
                    'currency_id': self.renew_bill_id.bill_currency_id.id if self.renew_bill_id.company_currency_id.id != self.renew_bill_id.bill_currency_id.id else False,
                    'company_currency_id': self.renew_bill_id.company_currency_id.id,
                    'account_id': protest_financial_expenses_journal.default_debit_account_id.id,
                    'amount_currency': renew_financial_expenses if self.renew_bill_id.company_currency_id.id != self.renew_bill_id.bill_currency_id.id else 0,
                    'tc': exchange_rate,
                    'balance': renew_financial_expenses_signed,
                    'debit': renew_financial_expenses_signed,
                    'credit': 0,
                    'date_maturity': self.renew_date,
                    }
                vals.append(val)
        # Luego la linea del asiento de la letra renovada
        renew_amount = self.bill_amount_total
        renew_exchange_rate = exchange_rate #self.renew_bill_id.account_move_line_ids[0].exchange_rate if self.renew_bill_id.send_form_id else self.origin_bill_id.account_move_line_ids[0].exchange_rate # self.origin_bill_id.send_form_id.exchange_rate if self.renew_bill_id == self.origin_bill_id else self.renew_bill_id.renew_bill_id.account_move_line_ids[0].exchange_rate
        if self.bill_currency_id != self.company_currency_id:
            renew_amount_signed = round(renew_amount * renew_exchange_rate,2)
        else:
            renew_amount_signed = renew_amount
        val = {
            'ref': self.renew_bill_id.name,
            'bill_id': self.renew_bill_id.id,
            'partner_id': self.responsable_id.id,
            'type_document_id': type_document_id.id,
            'nro_comp': self.renew_bill_id.bill_number,
            'move_id': self.renew_bill_id.account_move.id,
            'exchange_rate': renew_exchange_rate,#self.origin_bill_id.send_form_id.exchange_rate,
            'name': self.renew_bill_id.bill_number,
            'date': self.renew_date,
            'journal_id': self.origin_bill_id.bill_form_id.journal_id.id,
            'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
            'company_id': self.company_id.id,
            'company_currency_id': self.company_currency_id.id,
            'account_id': self.renew_bill_id.account_id.id,
            # 'amount_currency': self.renew_bill_id.bill_amount_total * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.renew_bill_id.bill_currency_id.id else 0,
            # 'tc': self.origin_bill_id.send_form_id.exchange_rate,
            # 'balance': self.origin_bill_id.send_form_id.bill_amount_total_signed * (-1 if self.type_bill == 'receivable' else 1), # if self.company_currency_id.id != self.renew_bill_id.bill_currency_id.id else 0,
            # 'debit': 0 if self.type_bill == 'receivable' else self.renew_bill_id.bill_amount_total_signed,
            # 'credit': self.renew_bill_id.bill_amount_total_signed if self.type_bill == 'receivable' else 0,
            'amount_currency': renew_amount * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.renew_bill_id.bill_currency_id.id else 0,
            'tc': renew_exchange_rate, #self.origin_bill_id.send_form_id.exchange_rate,
            'balance': renew_amount_signed * (-1 if self.type_bill == 'receivable' else 1), # if self.company_currency_id.id != self.renew_bill_id.bill_currency_id.id else 0,
            'debit': 0 if self.type_bill == 'receivable' else renew_amount_signed,
            'credit': renew_amount_signed if self.type_bill == 'receivable' else 0,
            'date_maturity': self.renew_bill_id.bill_date_due,
        }
        vals.append(val)
        if self.bill_currency_id != self.company_currency_id:
            # Diferencia por redondeo
            # Obtener el diario y las cuentas de redondeo desde la configuración
            params = self.env['ir.config_parameter'].sudo()
            round_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.round_boe_journal_id'))
            round_journal = self.env['account.journal'].search([('id','=',round_boe_journal_id)])

            # total_amount_currency = sum(item['credit'] if self.type_bill == 'receivable' else item['debit'] for item in vals)
            # total_debit = sum(item['debit'] if self.type_bill == 'receivable' else item['credit'] for item in vals)
            # difference = abs(total_amount_currency) - abs(total_debit)
            total_amount_currency = sum(item['debit'] if self.type_bill == 'receivable' else item['credit'] for item in vals)
            total_debit = sum(item['credit'] if self.type_bill == 'receivable' else item['debit'] for item in vals)
            # total_debit = sum(item['amount_currency'] if item['credit'] else 0 for item in vals) if self.type_bill == 'receivable' else sum(item['amount_currency'] if item['debit'] else 0 for item in vals)
            # difference = abs(total_amount_currency) - abs(total_debit * exchange_rate)
            difference = abs(total_amount_currency) - abs(total_debit)

            for i in range(8,1,-1):
                difference = round(difference,i)

            if float_round(difference,2) < 0:
                # Asiento de diferencia por redondeo ganancia
                val = {
                    'name': _('Currency round difference'),
                    'bill_id': self.renew_bill_id.id,
                    'exchange_rate': exchange_rate,
                    'debit': round(abs(difference),2) if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'credit': 0.0 if self.type_bill == 'receivable' else round(abs(difference),2), #if self.invoice_ids[0].type == 'out_invoice' else round(abs(total_debit - total_credit),2),
                    'account_id': round_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                    'move_id': self.renew_bill_id.account_move.id,
                    'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                    'amount_currency': round(abs(difference) / exchange_rate,2) * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    'tc': exchange_rate,
                    # 'partner_id': aml.partner_id.id,
                    'balance': round(abs(difference),2) * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    }
                vals.append(val)
            # if total_amount_currency * exchange_rate < total_debit and difference != 0:
            if float_round(difference,2) > 0:
                # Asiento de diferencia por redondeo perdida
                val = {
                    'name': _('Currency round difference'),
                    'bill_id': self.renew_bill_id.id,
                    'exchange_rate': exchange_rate,
                    'debit': 0.0 if self.type_bill == 'receivable' else abs(round(difference,2)), #if self.invoice_ids[0].type == 'out_invoice' else abs(round(total_debit - total_credit,2)),
                    'credit': abs(round(difference,2)) if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'account_id': round_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                    'move_id': self.renew_bill_id.account_move.id,
                    'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                    'amount_currency': round(abs(difference) / exchange_rate,2) * (-1 if self.type_bill == 'receivable' else 1) if self.company_currency_id.id != self.bill_currency_id.id else 0.00,
                    'tc': exchange_rate,
                    # 'partner_id': aml.partner_id.id,
                    'balance': round(abs(difference),2) * (-1 if self.type_bill == 'receivable' else 1), # if self.company_currency_id.id != self.bill_currency_id.id else 0.00,
                    }
                vals.append(val)
            # Diferencia de cambio
            # Obtener el diario y las cuentas de diferencia de cambio desde la configuración
            exchange_journal = self.env.company.currency_exchange_journal_id
            total_credit = round(sum(item['credit'] for item in vals),2)
            total_debit = round(sum(item['debit'] for item in vals),2)
            # if self.invoice_ids[0].type == 'out_invoice':
            if total_credit > total_debit:
                # Asiento de diferencia de cambio por ganancia
                val = {
                    'name': _('Currency exchange rate difference'),
                    'bill_id': self.renew_bill_id.id,
                    'exchange_rate': exchange_rate,
                    'debit': round(abs(total_debit - total_credit),2),# if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'credit': 0.0,# if self.type_bill == 'receivable' else round(abs(total_debit - total_credit),2), #if self.invoice_ids[0].type == 'out_invoice' else round(abs(total_debit - total_credit),2),
                    'account_id': exchange_journal.default_debit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                    'move_id': self.renew_bill_id.account_move.id,
                    'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                    # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                    # 'amount_currency': round(abs(total_debit - total_credit) / exchange_rate,2) if self.company_currency_id.id != self.bill_currency_id.id else 0.00,# * (1.0 if self.type_bill == 'receivable' else -1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    'tc': exchange_rate,
                    # 'partner_id': aml.partner_id.id,
                    'balance': round(abs(total_debit - total_credit),2),# * (1.0 if self.type_bill == 'receivable' else -1.0), # if self.company_currency_id.id != self.bill_currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    }
                vals.append(val)
            if total_credit < total_debit:
                # Asiento de diferencia de cambio por perdida
                val = {
                    'name': _('Currency exchange rate difference'),
                    'bill_id': self.renew_bill_id.id,
                    'exchange_rate': exchange_rate,
                    'debit': 0.0,# if self.type_bill == 'receivable' else abs(round(total_debit - total_credit,2)), #if self.invoice_ids[0].type == 'out_invoice' else abs(round(total_debit - total_credit,2)),
                    'credit': abs(round(total_debit - total_credit,2)), # if self.type_bill == 'receivable' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'account_id': exchange_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                    'move_id': self.renew_bill_id.account_move.id,
                    'currency_id': self.bill_currency_id.id if self.company_currency_id.id != self.bill_currency_id.id else False,
                    # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                    # 'amount_currency': round(abs(total_debit - total_credit) / exchange_rate,2) * -1.0 if self.company_currency_id.id != self.bill_currency_id.id else 0.00,# * (-1.0 if self.type_bill == 'receivable' else 1.0) if self.company_currency_id.id != self.bill_currency_id.id else 0.00,
                    'tc': exchange_rate,
                    # 'partner_id': aml.partner_id.id,
                    'balance': round(abs(total_debit - total_credit),2) * -1.0, # * (-1.0 if self.type_bill == 'receivable' else 1.0),
                    }
                vals.append(val)
        self.env['account.move.line'].create(vals)
        self.last_state = self.state_of_bill
        self.state_of_bill = self.renew_bill_id.last_state
        self.renew_bill_id.state_of_bill = 'renewed'
        self.renew_bill_id.account_move.action_post()
        # Actualizar lineas por problemas con Libro Diario
        # for line in self.renew_bill_id.account_move.line_ids:
        #     line.tc = line.exchange_rate
        #     line.partner_id = self.responsable_id
        #     line.type_document_id = type_document_id
        #     line.nro_comp = self.bill_number
        #     line.invoice_date = self.bill_date_issue
        #     line.date_maturity = self.bill_date_due
        # Reconciliar asientos
        if self.renew_bill_id.renew_bill_id:
            lines = self.renew_bill_id.account_move_line_ids.filtered(lambda l: l.name == self.renew_bill_id.bill_number and\
                l.account_id == self.renew_bill_id.account_id and\
                l.credit > 0)
            if lines.account_id.reconcile and not lines.reconciled:
                filtered = self.renew_bill_id.renew_bill_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and\
                    not l.reconciled and\
                    l.name == lines.name)
                if filtered:
                    lines += filtered
        else:
            lines = self.renew_bill_id.account_move_line_ids.filtered(lambda l: l.name == self.renew_bill_id.bill_number and\
                l.account_id == self.renew_bill_id.account_id and\
                l.credit > 0)
            if lines.account_id.reconcile and not lines.reconciled:
                if self.renew_bill_id.send_form_id.bank_disbursement_id:
                    filtered = self.renew_bill_id.send_form_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and\
                        not l.reconciled and\
                        l.name == lines.name)
                else:
                    # for l in self.renew_bill_id.send_form_id.account_move_line_ids:
                    #     print(l.name, lines.name, l.account_id, lines.account_id, l.reconciled, (l.name == lines.name or l.name == lines.name[:7]))
                    filtered = self.renew_bill_id.send_form_id.account_move_line_ids.filtered(lambda l: l.account_id == lines.account_id and \
                        not l.reconciled and \
                        (l.name == lines.name or l.name == lines.name[:7]))
                if filtered:
                    lines += filtered
        lines.reconcile()
        # # Conciliar la responsabilidad
        # lines = self.renew_bill_id.account_move_line_ids.filtered(lambda l: l.name[:20] == _('Bank Responsabillity'))
        # if self.renew_bill_id.send_form_id.bank_disbursement_id.id:
        #     lines += self.renew_bill_id.send_form_id.bank_disbursement_id.account_move_line_ids.filtered(lambda l: l.name == lines.name)
        # else:
        #     # Conciliamos con la linea del asiento de importación
        #     import_form = self.env['account.import.bill.form'].search([('send_form_id','=', self.origin_bill_id.send_form_id.id)])
        #     account_move = import_form.account_move_ids.filtered(lambda am: am.name.split('-')[0] == _('Bill import %s') %lines.ref + ' ')
        #     lines += account_move.line_ids.filtered(lambda l: l.name == lines.name and l.credit > 0)
        # lines.reconcile()

        # Conciliar la responsabilidad
        lines = self.renew_bill_id.account_move_line_ids.filtered(lambda l: l.account_id.id == account[0] and l.debit > 0)
        if self.renew_bill_id.send_form_id.bank_disbursement_id:
            lines += self.renew_bill_id.send_form_id.bank_disbursement_id.account_move_line_ids.filtered(lambda l: self.renew_bill_id.bill_number in l.name and l.account_id == lines.account_id and l.credit > 0 and not l.reconciled)
        elif self.renew_bill_id.renew_bill_id:
            lines += self.renew_bill_id.renew_bill_id.account_move_line_ids.filtered(lambda l: self.renew_bill_id.bill_number in l.name and l.credit > 0)
            # lines += self.renew_bill_id.renew_bill_id.account_move_line_ids.filtered(lambda l: l.name[:24] == _('New Bank Responsabillity'))
        else:
            # Conciliamos con la linea del asiento de importación
            import_form = self.env['account.import.bill.form'].search([('send_form_id','=', self.origin_bill_id.send_form_id.id)])
            account_move = import_form.account_move_ids.filtered(lambda am: self.renew_bill_id.bill_number in am.name or self.renew_bill_id.bill_number[:7] in am.name)#am.name.split('-')[0] == _('Bill import %s') %lines.ref + ' ' or am.name.split('-')[0] == _('Bill import %s') %lines.ref[:7] + ' ')
            # for l in account_move.line_ids:
            #     print(l.name, self.renew_bill_id.name, l.account_id, lines.account_id, l.credit)
            lines += account_move.line_ids.filtered(lambda l: (self.renew_bill_id.bill_number in l.name or self.bill_number[:7] in l.name) and l.account_id == lines.account_id and l.credit > 0)
        lines.reconcile()

    def cancel(self):
        if self.state_of_bill == 'pending':
            self.renew_form_id = False
            other_bill = self.env['account.bill'].search([('renew_bill_id','=',self.id),('state_of_bill','=','to_renew')])
            other_bill.state_of_bill = 'draft'
            if len(other_bill.renew_form_id.renew_bill_ids) == 1:
                other_bill.renew_form_id.state = 'draft'
                other_bill.renew_form_id.unlink()
            other_bill.unlink()
            self.account_move.button_draft()
            self.account_move_line_ids.unlink()
            self.account_move = False
            self.state_of_bill = self.last_state
            self.account_id = self.last_account_id
            return

        if self.state_of_bill == 'to_renew':
            rbf_id = self.env['renew.bill.form'].search([('id','=',self.renew_form_id.id)])
            rbf_id.renew_bill_ids = [(3, self.id)]
            rbf_id.origin_bill_ids = [(3, self.renew_bill_id.id)]
            if len(rbf_id.renew_bill_ids) == 1:
                rbf_id.with_context(force_delete=True).unlink()
            self.renew_bill_id.account_move.button_draft()
            self.renew_bill_id.account_move_line_ids.unlink()
            self.renew_bill_id.account_move = False
            self.renew_bill_id.state_of_bill = self.renew_bill_id.last_state
            self.account_id = self.last_account_id
            self.state_of_bill = 'draft'
            before_unlink = self.origin_bill_id
            self.unlink()
            return {
                'name': before_unlink.name,
                'res_model': 'account.bill',
                'view_mode': 'tree',
                'view_id': before_unlink.env.ref('jp_account_bills_of_exchange.view_account_bill_tree').id,
                'res_id': before_unlink.env.ref('jp_account_bills_of_exchange.view_account_bill_tree').id,
                'target': 'current',
                'type': 'ir.actions.act_window',
            }
            
            #TODO Esto se utiliza para enviar un mensaje tipo java
            # title = _("Connection Test Succeeded!")
            # message = _("Everything seems properly set up!")
            # return {
            #     'type': 'ir.actions.client',
            #     'tag': 'display_notification',
            #     'params': {
            #         'title': title,
            #         'message': message,
            #         'sticky': False,
            #     }
            # }
        
        if self.state_of_bill in ['collection','discount','guarantee','disbursed']:
            if self.renew_bill_id:
                self.renew_bill_id.account_move.button_draft()
                self.renew_bill_id.account_move.with_context(force_delete=True).unlink()
                self.renew_bill_id.renew_payment_id.button_draft()
                self.renew_bill_id.renew_payment_id.with_context(force_delete=True).unlink()
                self.renew_bill_id.account_id = self.renew_bill_id.last_account_id if self.renew_bill_id.state_of_bill != 'renewed' else self.renew_bill_id.account_id
                self.renew_bill_id.state_of_bill = 'pending' #self.renew_bill_id.last_state
                self.state_of_bill = 'to_renew'
                # self.state_of_bill = 'draft'
                # self.renew_form_id.origin_bill_ids = [(3, self.renew_bill_id.id)]
                # if len(self.renew_form_id.renew_bill_ids) == 1:
                #     self.renew_form_id.with_context(force_delete=True).unlink()
                # self.unlink()
                # return {
                #     'name': _('Bills of Exchange'), #before_unlink.name,
                #     'res_model': 'account.bill',
                #     # 'view_mode': 'tree',
                #     'view_type': 'list',
                #     'view_mode': 'list,form',
                #     # 'view_id': self.env.ref('jp_account_bills_of_exchange.view_account_bill_tree').id,
                #     'domain': [('type_bill','=', 'receivable')],
                #     'target': 'main',
                #     'type': 'ir.actions.act_window',
                # }
            else:
                raise UserError(_("You cannot cancel a bill sent."))
        
        if self.state_of_bill in ['accepted']:
            if self.renew_bill_id:
                self.renew_bill_id.account_move.button_draft()
                self.renew_bill_id.account_move_line_ids.unlink()
                self.renew_bill_id.account_move = False
                self.renew_bill_id.state_of_bill = self.renew_bill_id.last_state
                self.renew_bill_id.account_id = self.renew_bill_id.last_account_id
                self.state_of_bill = 'accepted'
                self.renew_form_id.origin_bill_ids = [(3, self.renew_bill_id.id)]
                if len(self.renew_form_id.renew_bill_ids) == 1:
                    self.renew_form_id.with_context(force_delete=True).unlink()
                else:
                    self.with_context(force_delete=True).unlink()
                return {
                    'name': _('Bills of Exchange'), #before_unlink.name,
                    'res_model': 'account.bill',
                    # 'view_mode': 'tree',
                    'view_type': 'list',
                    'view_mode': 'list,form',
                    # 'view_id': self.env.ref('jp_account_bills_of_exchange.view_account_bill_tree').id,
                    'domain': [('type_bill','=', 'payable')],
                    'target': 'main',
                    'type': 'ir.actions.act_window',
                }
            else:
                raise UserError(_("You cannot cancel a bill sent."))

        if self.state_of_bill in ['paid','protested']:
            if self.state_of_bill == 'protested' and self.last_state == False:
                raise UserError (_('The bill you are triying to cancel its an inicial bill. You can\'t cancel this one !'))
            if self.state_of_bill == 'protested':
                self.state_of_bill = self.last_state
                self.payment_date = False
                self.last_state = self.state_of_bill if not self.protest_payment_id else self.protest_payment_id.bill_last_state
                self.account_id = self.protest_payment_id.last_account_id if self.protest_payment_id else self.last_account_id
                self.protest_payment_id.account_move.button_draft()
                self.protest_payment_id.account_move_line_ids.unlink()
                self.protest_payment_id.unlink()
                self.protest_payment_id = False
                self.account_move.button_draft()
                self.account_move.with_context(force_delete=True).unlink()
                self.account_move = False
                # si tienen los gastos financieros separados tambien cancela el asiento
                if self.account_move_bank_interests_id:
                    self.account_move_bank_interests_id.button_draft()
                    self.account_move_bank_interests_id.line_ids.unlink()
                    self.account_move_bank_interests_id.name = "/"
                    self.account_move_bank_interests_id.unlink()
                    self.account_move_bank_interests_id = False
                if self.protest_debit_note_id and self.protest_debit_note_id.state == 'posted':
                    raise UserError(_('You have to cancel first the debit note.'))
                #     self.protest_debit_note_id.button_draft()
                #     self.protest_debit_note_id.line_ids.unlink()
                #     self.protest_debit_note_id.name = "/"
                #     self.protest_debit_note_id.unlink()
                #     self.protest_debit_note_id = False
                # return
            else:
                if self.state_of_bill != 'paid':
                    self.account_id = self.last_account_id if self.last_account_id else self.account_id
                self.account_move.button_draft()
                # self.account_move_line_ids.unlink()
                self.account_move.with_context(force_delete=True).unlink()
                self.state_of_bill = self.last_state
                self.last_state = self.state_of_bill if not self.protest_payment_id else self.protest_payment_id.bill_last_state
                self.payment_date = False
                if self.last_state != 'protested':
                    self.account_move = False
                self.payment_amount = 0

    def debit_note_wizard(self):
        # Agregar un wizard para los gastos administrativos
        return self.env['admin.interest.protest']\
            .with_context(active_ids=self.ids, active_model='account.bill', active_id=self.id, type='or')\
            .get_debit_note_data()

class InterestAdministrativeOnProtest(models.TransientModel):
    _name = 'admin.interest.protest'
    _description = 'Interest Administrative on Protest'

    interest_administrative = fields.Float(string='Interest Administrative', digits=(12, 2))

    def get_debit_note_data(self):
        active_id = self.env.context.get('active_id')
        if not active_id:
            return ''

        return {
            'name': _('Interest Administrative1'),
            'res_model': 'admin.interest.protest',
            'view_mode': 'form',
            'view_id': self.env.ref('jp_account_bills_of_exchange.view_protest_admin_interest_wizard').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def create_debit_note_data(self):
        active_id = self.env.context.get('active_id')
        type = self.env.context.get('type')
        bill_id = self.env['account.bill'].search([('id','=',active_id)])
        if not active_id:
            return ''

        # Creamos la nota de débito con los datos del protesto
        # Obtener el diario de gastos financieros
        params = self.env['ir.config_parameter'].sudo()
        # protests_financial_expenses_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.protests_financial_expenses_boe_journal_id'))
        # journal_id = self.env['account.journal'].search([('id','=',protests_financial_expenses_boe_journal_id)])
        protests_financial_expenses_boe_account_id = int(params.get_param('jp_account_bills_of_exchange.protests_financial_expenses_boe_account_id'))
        account_id = self.env['account.account'].search([('id','=',protests_financial_expenses_boe_account_id)])
        type_document = self.env['einvoice.catalog.01'].search([('code','=','08')], limit=1)
        debit_note_type = self.env['einvoice.catalog.10'].search([('code','=','01')], limit=1)
        serie_id = self.env['it.invoice.serie'].search([('document_type_id.code','=','08')], limit=1)
        lines = []  
        if self.interest_administrative > 0:
            interest_administrative = {
                'name': _('Interest administrative'),
                'quantity': 1,
                'account_id': account_id.id,
                'price_unit': self.interest_administrative,
                'tax_ids': [(6, 0, [self.env.company.account_sale_tax_id.id])]
            }
            lines.insert(0, (0, 0, interest_administrative))
        if bill_id.account_move_bank_interests_id:
            line_financial_expenses = {
                'name': _('Postage and comissions for protest'),
                'quantity': 1,
                'account_id': account_id.id,
                'price_unit': bill_id.account_move_bank_interests_id.line_ids[1].credit if bill_id.bill_currency_id == self.env.company.currency_id else abs(bill_id.account_move_bank_interests_id.line_ids[1].amount_currency),
                'tax_ids': [(6, 0, [self.env.company.account_sale_tax_id.id])]
            }
            lines.insert(0, (0, 0, line_financial_expenses))
        if bill_id.account_move_line_ids.filtered(lambda l: l.name[:14] == 'Bank interests'):
            bank_interests = {
                'name': _('Bank interests'),
                'quantity': 1,
                'account_id': account_id.id,
                'price_unit': bill_id.account_move_line_ids.filtered(lambda l: l.name[:14] == 'Bank interests').debit if bill_id.bill_currency_id == self.env.company.currency_id else abs(bill_id.account_move_line_ids.filtered(lambda l: l.name[:14] == 'Bank interests').amount_currency),
                'tax_ids': [(6, 0, [self.env.company.account_sale_tax_id.id])]
            }
            lines.insert(0, (0, 0, bank_interests))
        val = {
            'ref': '',
            'date': datetime.now(),
            'invoice_date': datetime.now(),
            'currency_rate': bill_id.bill_currency_id._get_conversion_rate(bill_id.bill_currency_id, bill_id.company_currency_id, bill_id.company_id, datetime.now()),
            # 'journal_id': bill_id.bill_form_id.journal_id.id, # TODO poner el diario de facturas
            'serie_id': serie_id.id,
            # 'ref': serie_id.sequence_id.number_next_actual,
            'type': 'out_invoice',
            'currency_id': bill_id.bill_currency_id.id,
            'partner_id': bill_id.responsable_id.id,
            'type_document_id': type_document.id,
            'debit_note_type_id': debit_note_type.id,
            'pe_debit_note_code': debit_note_type.id,
            'glosa': _('Interest on protest bill %s') %bill_id.name,
            'invoice_line_ids': lines,         
        }
        account_move = self.env['account.move'].create(val)
        account_move.onchange_serie_id()
        bill_id.protest_debit_note_id = account_move.id
        # Cambia las cuentas de las lineas
        # for line in account_move.invoice_line_ids:
        #         line.account_id = journal_id.default_debit_account_id.id,

        return {
            'name': _('Debit Note'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'context': self.env.context,
            'target': 'current',
            'res_id': account_move.id,
            'type': 'ir.actions.act_window',
        }
