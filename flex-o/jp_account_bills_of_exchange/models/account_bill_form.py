from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from . import amount_to_text_es
from datetime import datetime, timedelta, date
from odoo.tools import float_round

TYPE2JOURNAL = {'out_invoice':'sale',
 'in_invoice':'purchase',
 'out_refund':'sale',
 'in_refund':'purchase'}

class BillForm(models.Model):
    _name = 'account.bill.form'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Bill of Exchange Form'
    _order = 'exchange_date desc, name desc, id desc'

    def _get_default_journal_id(self):
        # Obtener el diario y las cuentas desde la configuración
        if self._context.get('type', False) == 'out_invoice':
            # Obtener la cuenta de letras de cliente desde la configuración
            params = self.env['ir.config_parameter'].sudo()
            customer_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.customer_boe_journal_id'))
            return self.env['account.journal'].search([('id','=',customer_boe_journal_id)])
        else:
            # Obtener la cuenta de letras de proveedor desde la configuración
            params = self.env['ir.config_parameter'].sudo()
            supplier_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.supplier_boe_journal_id'))
            return self.env['account.journal'].search([('id','=',supplier_boe_journal_id)])
            # if not self.journal_id:
            #     raise UserError('You must configure the Bill of Exchange Journal in settings.')

    # def _get_default_currency(self):
    #     # Obtener el diario y las cuentas desde la configuración
    #     if self._context.get('type', False) == 'out_invoice':
    #         # Obtener la cuenta de letras de cliente desde la configuración
    #         params = self.env['ir.config_parameter'].sudo()
    #         customer_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.customer_boe_journal_id'))
    #         journal_id = self.env['account.journal'].search([('id','=',customer_boe_journal_id)])
    #         return journal_id.currency_id if journal_id.currency_id else self.env.company.currency_id
    #     else:
    #         # Obtener la cuenta de letras de proveedor desde la configuración
    #         params = self.env['ir.config_parameter'].sudo()
    #         supplier_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.supplier_boe_journal_id'))
    #         journal_id = self.env['account.journal'].search([('id','=',supplier_boe_journal_id)])
    #         return journal_id.currency_id if journal_id.currency_id else self.env.company.currency_id

    name = fields.Char('Form number', copy=False, readonly=True, default=(lambda x: _('New')))
    partner_id = fields.Many2one('res.partner', 'Partner', tracking=True)
    exchange_date = fields.Date('Exchange Date', default=fields.Date.context_today, tracking=True)
    gloss = fields.Char('Gloss', required=True)
    reference = fields.Char('Reference')
    bill_ids = fields.One2many('account.bill', 'bill_form_id', 'Bills of Exchange', tracking=True)
    invoice_ids = fields.Many2many('account.move', string='Invoices', tracking=True)
    account_move_line_ids = fields.One2many('account.move.line', 'bill_form_id', string='Account move lines')
    custom_exchange_rate = fields.Boolean(string='Custom Exchange Rate')
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1, tracking=True)
    account_move = fields.Many2one('account.move', 'Account Move')
    state = fields.Selection([('draft', 'Draft'), ('to_reconcile', 'To Reconcile'), ('done', 'Done'), ('imported', 'Imported'), ('advanced', 'Advanced')], string='State', default='draft', tracking=True)
    retention_percentage = fields.Float(string='Retention percentage (%)', tracking=True)
    apply_retention = fields.Boolean(string='Apply retentions')
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.company),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    # currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, states={'draft': [('readonly', False)]},string='Currency',default=(lambda self: self.env.user.company_id.currency_id))
    # currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, states={'draft': [('readonly', False)]},string='Currency',default=_get_default_currency)
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, states={'draft': [('readonly', False)]},string='Currency')
    total_retention = fields.Monetary('Total retencion', currency_field='currency_id', default=0)
    total_retention_signed = fields.Monetary('Total retencion Signed', currency_field='company_currency_id', default=0)
    total_exchange = fields.Monetary('Total exchange', currency_field='company_currency_id', default=0)
    total_invoices = fields.Monetary('Total Invoices', currency_field='company_currency_id', default=0)
    total_bills = fields.Monetary('Total Bills', currency_field='company_currency_id', default=0)
    bills_qty = fields.Integer('Bills quantity', default=1)
    days_due_first = fields.Integer('Expiration days of 1st Bill', default=15)
    range_bill = fields.Integer('Range of days between bills', default=15)
    guarantee_id = fields.Many2one('res.partner', string='Guarantee')
    acceptor_id = fields.Many2one('res.partner', string='Acceptor')
    journal_id = fields.Many2one('account.journal', string='Journal for Bills of Exchange', default=_get_default_journal_id)
    type_form = fields.Char(string="Form Type", default='1')
    send_form_ids = fields.Many2many('account.send.bank', string='Send to Bank Forms')

    # Para la importación de letras
    bank_position = fields.Selection(string='Bank Position', selection=[('collection', 'Collection'), ('discount', 'Discount'), ('guarantee', 'Guarantee'),],)
    
    # Para las letras por anticipo o letras de favor
    #advanced_bill_form_ids = fields.One2many('account.advanced.bill.form', 'bill_form_id', string='Advanced bill form')
    advanced_bill_form_id = fields.Many2one('account.advanced.bill.form', string='Advanced Bill Form')

    @api.onchange('gloss')
    def _onchange_gloss(self):
        if self.account_move:
            self.account_move.glosa = self.gloss

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.bank_position = self.journal_id.bank_position
        self.currency_id = self.journal_id.currency_id if self.journal_id.currency_id else self.env.company.currency_id

    @api.onchange('invoice_ids')
    def _check_form_type(self):
        if self.invoice_ids:
            if self.invoice_ids[0].type == 'out_invoice':
                self.type_form = '1'
            else:
                self.type_form = '2'
    
    def get_exchange_rate(self, amount, currency, company, date):
        return self.currency_id._convert(amount, currency, company, date, False)

    @api.onchange('currency_id','exchange_date','custom_exchange_rate')
    def onchange_currency_id(self):
        if self.currency_id and self.currency_id != self.env.user.company_id.currency_id:
            rates = self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id),('name','=',self.exchange_date or fields.Date.context_today)])
            if not rates:
                rates = self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id)], order='name desc', limit=1)
                # if rates:
                #     self.exchange_rate = round(1/rates.rate,3)
                #     self.env.user.notify_info(_('There is no exchange rate for that date. All the journal entries will be calculated with this rate %s from %s') %(round(1/rates.rate,3),datetime.strftime(rates.name, "%d/%m/%Y")))
                #     # return {
                #     #     'warning': {'title': _("Exchange Rate"), 'message': _('There is no exchange rate for that date. All the journal entries will be calculated with this rate %s from %s') %(round(1/rates.rate,3),datetime.strftime(rates.name, "%d/%m/%Y")),},
                #     #     }
                # else:
                #     self.env.user.notify_warning(_('There is no exchange rate for that date. All the journal entries will be calculated with this rate %s') %self.exchange_rate)
                #     # raise UserError(_('There is no exchange rate for that date. All the journal entries will be calculated with this rate %s') %self.exchange_rate)
        if not self.custom_exchange_rate:
            if self.currency_id.id == self.company_currency_id.id:
                self.exchange_rate = 1
            else:
                self.exchange_rate = self.get_exchange_rate(1, self.company_id.currency_id, self.company_id, self.exchange_date or fields.Date.context_today)
        self.onchange_retention()
        for bill in self.bill_ids:
            bill.exchange_rate = self.exchange_rate

    @api.onchange('apply_retention','retention_percentage','total_invoices')
    def onchange_retention(self):
        self.set_total_retention()

    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('account.bill.form') or _('New')
        return super(BillForm, self).create(values)

    def import_lines(self):
        self.type_form = '3'
        if self.bank_position:
            vals = {
                # 'name' : 1,
                'journal_id' : self.journal_id.id,
                'send_date' : self.exchange_date,
                'bank_position' : self.bank_position,
                'bill_ids' : self.bill_ids,
                # 'company_id' : 1,
                # 'company_currency_id' : 1,
                'currency_id' : self.currency_id.id,
                'state' : 'disbursed' if self.bank_position == 'discount' else 'sent',
                # 'account_move_line_ids' : 1,
                # 'account_move' : 1,
                # 'custom_exchange_rate' : 1,
                # 'exchange_rate' : 1,
                # 'bank_disbursement_id' : 1,
                # 'is_discount' : 1,
                # 'bill_form_ids' : [4 ,self.id],
                # 'interest_rate' : 1,
            }
            send_form = self.env['account.send.bank'].create(vals)
            for bill in self.bill_ids:
                bill.send_form_id = send_form
            # self.send_form_ids = [4, send_form.id]
        self.state = 'done'

    def get_total_invoices(self):
        total_invoices = 0
        if self.invoice_ids:
            for line in self.invoice_ids:
                total_invoices += line.amount_residual
        return total_invoices

    def get_total_bills(self):
        total_bills = 0
        if self.bill_ids:
            for bill in self.bill_ids:
                if bill.bill_currency_id != self.currency_id:
                    if self.currency_id != self.company_currency_id:
                        total_bills += bill.bill_amount_total / bill.exchange_rate
                    else:
                        total_bills += bill.bill_amount_total * bill.exchange_rate
                else:
                    total_bills += bill.bill_amount_total
        return total_bills
    
    def set_total_retention(self):
        if self.apply_retention:
            self.total_retention = self.get_total_invoices() * (self.retention_percentage / 100)
            self.total_retention_signed = self.get_total_invoices() * self.exchange_rate * (self.retention_percentage / 100)
            self.total_bills = self.total_bills - self.total_retention
        else:
            self.total_retention = 0

    def check_invoice_and_bills(self):
        if self.state != 'done':
            total_invoices = self.get_total_invoices()
            total_bills = self.get_total_bills()
            # if self.type_form != '3' or self._context.get('type_form') != '3':
            #     if round(total_bills,2) + round(self.total_retention,2) > round(total_invoices,2):
            #         raise ValidationError('Bills of exchange total is greather than invoices total. Maybe one or more invoices have change their balance.')

    def write(self, vals):
        res = super(BillForm, self).write(vals)
        # self.check_invoice_and_bills()
        return res

    def unlink(self):
        for bill_form in self:
            if bill_form.state != 'draft' and not self._context.get('force_delete'):
                raise UserError(_("You cannot delete an entry which has been posted once."))
            bill_form.account_move_line_ids.unlink()
            bill_form.bill_ids.unlink()
        return super(BillForm, self).unlink()

    def change_bill_date(self, bill_date_due):
        # Si es sabado o domingo cambia la fecha
        # a lunes si es domingo y a viernes si es sabado
        # Luego si es ferido sigues bajando o subiendo
        days_to_add = -1 if date.weekday(bill_date_due) == 5 and not self._context.get('foward') else 1
        while True:
            # Aumenta un dia si es domingo y disminuye si es sabado
            if date.weekday(bill_date_due) > 4:
                bill_date_due = bill_date_due + timedelta(days=(days_to_add))
                # Si se aumento y cae domingo vuelve a aumentar
                if date.weekday(bill_date_due) > 4:
                    bill_date_due = bill_date_due + timedelta(days=(days_to_add))
            # Si es feriado aumentale un dia si era domingo
            # y diminuye un dia si era sabado
            from_date = datetime.strftime(bill_date_due, '%Y-%m-%d %H:%M:%S')
            to_date = datetime.strftime(bill_date_due, '%Y-%m-%d 23:59:59')
            holidays = self.env['resource.calendar.leaves'].search([('date_from','>=',from_date),('date_from','<=',to_date)])
            if holidays.ids:
                bill_date_due = bill_date_due + timedelta(days=(days_to_add))
            else:
                break
        return bill_date_due

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
                'bill_amount_total_signed':bill_amount_signed,
                'exchange_rate':self.exchange_rate,
                'account_id': self.journal_id.default_debit_account_id.id, # if self.invoice_ids[0].type == 'out_invoice' else self.journal_id.default_credit_account_id.id,
                'type_bill': 'receivable' if self.invoice_ids[0].type == 'out_invoice' else 'payable',
                'amount_text':amount_to_text_es.amount_to_text(bill_amount, self.currency_id.name)}))
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
                    'bill_amount_total_signed':bill_amount_signed,
                    'exchange_rate':self.exchange_rate,
                    'account_id':self.journal_id.default_debit_account_id.id, # if self.invoice_ids[0].type == 'out_invoice' else self.journal_id.default_credit_account_id.id,
                    'type_bill': 'receivable' if self.invoice_ids[0].type == 'out_invoice' else 'payable',
                    'amount_text':amount_to_text_es.amount_to_text(bill_amount, self.currency_id.name)}))

                self.bill_ids = result
            for bill in self.bill_ids:
                bill.account_id = self.journal_id.default_debit_account_id
            self.update_sequence_final()

    def update_form(self):
        self.total_invoices = self.get_total_invoices()
        self.total_bills = self.get_total_bills()
        self.set_total_retention()

    def process(self):
        if self.state != 'draft':
            raise UserError(_('You can\'t process a form in %s state.' %self.state))
        self.state = 'to_reconcile'
        for bill in self.bill_ids:
            bill.state_of_bill = 'to_accept'

    def create_move(self, exchange_date, exchange_rate):
        # if self.apply_retention:
        # self.update_bills()
        # self.update_sequence()
        if not self.bill_ids:
            raise UserError(_('There is no bills to exchange for invoices.'))
        # self.state = 'done'
        val = {}
        vals = []
        val = {
            'name': self.name,
            # TODO revisar diario de itgrupo
            # Se comenta para poder ingresar letras de terceros en soles y pagar facturas en dolares
            # 'currency_id': self.currency_id.id,
            'date': exchange_date,
            'invoice_date': exchange_date,
            'journal_id': self.journal_id.id,
            'glosa': self.gloss,
            'currency_rate': exchange_rate,
            # TODO revisar diario de itgrupo
            # Se comenta para poder ingresar letras de terceros en soles y pagar facturas en dolares
            # y se coloca nueva linea como 'entry'
            # 'type': 'bill',
            'type': 'entry',
        }
        if not self.account_move:
            self.account_move = self.env['account.move'].create(val)
        # Entrega los numeros finales
        self.update_sequence_final()
        # Letras
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
        for bill in self.bill_ids:
            bill.exchange_rate = exchange_rate
            bill.bill_amount_total_signed = float_round(bill.bill_amount_total * exchange_rate, 2) if bill.bill_currency_id != self.env.company.currency_id else bill.bill_amount_total_signed
            val = {
                # TODO Para que salga en los estados de cuenta estandar
                # debe tener la letra como referencia y ademas el partner_id en
                # la linea del asiento
                'ref': bill.bill_number,
                'bill_form_id': self.id,
                'partner_id': bill.acceptor_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': bill.bill_number,
                'move_id': self.account_move.id,
                'exchange_rate': exchange_rate if bill.company_currency_id != bill.bill_currency_id else 1,
                'name': bill.bill_number,
                'date': bill.bill_date_issue, #exchange_date,
                'journal_id': self.journal_id.id,
                'currency_id': bill.bill_currency_id.id if bill.company_currency_id.id != bill.bill_currency_id.id else False,
                'company_id': bill.company_id.id,
                'company_currency_id': bill.company_currency_id.id,
                'account_id': bill.account_id.id if not self.send_form_ids else self.journal_id.default_debit_account_id.id, #self.journal_id.default_debit_account_id.id, # if self.invoice_ids[0].type == 'out_invoice' else self.journal_id.default_credit_account_id.id,
                'debit': bill.bill_amount_total_signed if self.invoice_ids[0].type == 'out_invoice' else 0,
                'amount_currency': bill.bill_amount_total * (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
                'tc': exchange_rate if bill.company_currency_id != bill.bill_currency_id else 1,
                'balance': bill.bill_amount_total_signed * (1 if self.invoice_ids[0].type == 'out_invoice' else -1), # if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
                'credit':  0 if self.invoice_ids[0].type == 'out_invoice' else bill.bill_amount_total_signed,
                'date_maturity': bill.bill_date_due,
            }
            vals.append(val)
        # Facturas
        total_bills = self.get_total_bills()
        for invoice in self.invoice_ids:
            val = {
                'ref': invoice.ref,
                'bill_form_id': self.id,
                'partner_id': invoice.partner_id.id,
                'type_document_id': invoice.type_document_id.id,
                'nro_comp': invoice.ref,
                'move_id': self.account_move.id,
                'exchange_rate': exchange_rate, #invoice.amount_total_signed / invoice.amount_total if self.currency_id != self.env.user.company_id.currency_id else 0, 
                'name': invoice.ref,
                'date': invoice.invoice_date, #exchange_date,
                'journal_id': self.journal_id.id,
                'company_id': invoice.company_id.id,
                'currency_id': invoice.currency_id.id if invoice.company_currency_id.id != invoice.currency_id.id else False,
                'company_currency_id' : invoice.company_currency_id.id,
                'account_id': self.journal_id.default_credit_account_id.id,
                'amount_currency': invoice.amount_residual * (-1 if self.invoice_ids[0].type == 'out_invoice' else 1) if invoice.company_currency_id.id != invoice.currency_id.id else 0,
                'tc': exchange_rate, #invoice.amount_total_signed / invoice.amount_total if self.currency_id != self.env.user.company_id.currency_id else 0, 
                'balance': invoice.amount_residual * exchange_rate * (-1 if self.invoice_ids[0].type == 'out_invoice' else 1), #* (-1 if self.invoice_ids[0].type == 'out_invoice' else 1),
                'debit': 0 if self.invoice_ids[0].type == 'out_invoice' else float_round(abs(invoice.amount_residual * exchange_rate),2),
                'credit': float_round(abs(invoice.amount_residual * exchange_rate),2) if self.invoice_ids[0].type == 'out_invoice' else 0,
                'date_maturity': invoice.invoice_date_due,
                }
            total_bills -= invoice.amount_residual
            if total_bills < 0:
                total_bills = invoice.amount_residual + total_bills
                er = val['exchange_rate']
                val['amount_currency'] = total_bills * (-1 if self.invoice_ids[0].type == 'out_invoice' else 1) if invoice.company_currency_id.id != invoice.currency_id.id else 0
                val['balance'] = total_bills * er * -1
                val['debit'] = 0 if self.invoice_ids[0].type == 'out_invoice' else abs(total_bills) * er 
                val['credit'] = abs(total_bills) * er if self.invoice_ids[0].type == 'out_invoice' else 0
            vals.append(val)
        # Retención
        if self.apply_retention:
            # Obtener la cuenta de retenciones desde la configuración
            params = self.env['ir.config_parameter'].sudo()
            retention_boe_account_id = int(params.get_param('jp_account_bills_of_exchange.retention_boe_account_id'))
            retention_account_id = self.env['account.account'].search([('id','=',retention_boe_account_id)])
            val = {
                # 'ref': _('Retention: ') + self.name,
                'bill_form_id': self.id,
                'move_id': self.account_move.id,
                'exchange_rate': exchange_rate,
                'name': _('Retention: ') + self.name,
                'date': exchange_date,
                'journal_id': self.journal_id.id,
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                'company_currency_id' : self.company_currency_id.id,
                'account_id': retention_account_id.id,
                'amount_currency': self.total_retention * (1 if self.invoice_ids[0].type == 'out_invoice' else -1) if self.company_currency_id.id != self.currency_id.id else 0,
                'tc': exchange_rate,
                'balance': self.total_retention_signed * (1 if self.invoice_ids[0].type == 'out_invoice' else -1),
                'debit': self.total_retention_signed if self.invoice_ids[0].type == 'out_invoice' else 0,
                'credit': 0 if self.invoice_ids[0].type == 'out_invoice' else self.total_retention_signed,
                }
            vals.append(val)
        # Si hay saldo a favor del cliente
        total_inv = self.get_total_invoices()
        total_bill = self.get_total_bills()
        if total_bill > total_inv:
            partner_favor = float_round(total_bill - total_inv,2)
            partner_favor_signed = float_round((total_bill - total_inv) * exchange_rate,2)
            # Obtener la cuenta de anticipos desde la configuración
            params = self.env['ir.config_parameter'].sudo()
            advanced_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.advanced_boe_journal_id'))
            advanced_account_id = self.env['account.journal'].search([('id','=',advanced_boe_journal_id)]).default_debit_account_id
            if not advanced_account_id:
                raise UserError (_('There is no advanced payment journal configured in settings.'))
            # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
            type_document_id = self.env['einvoice.catalog.01'].search([('code','=','00')])
            val = {
                # 'ref': _('Balance in favor of the client'),
                'bill_form_id': self.id,
                'move_id': self.account_move.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.name,
                'partner_id': self.partner_id.id,
                'exchange_rate': exchange_rate,
                'name': _('Balance in favor of the client'),
                'date': exchange_date,
                'journal_id': self.journal_id.id,
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                'company_currency_id' : self.company_currency_id.id,
                'account_id': advanced_account_id.id,
                'amount_currency': partner_favor * (-1 if self.invoice_ids[0].type == 'out_invoice' else 1) if self.company_currency_id.id != self.currency_id.id else 0,
                'tc': exchange_rate,
                'balance': partner_favor_signed * (-1 if self.invoice_ids[0].type == 'out_invoice' else 1),
                'credit': partner_favor_signed if self.invoice_ids[0].type == 'out_invoice' else 0,
                'debit': 0 if self.invoice_ids[0].type == 'out_invoice' else partner_favor_signed,
                }
            vals.append(val)
        # Diferencia por redondeo
        # Obtener el diario y las cuentas de redondeo desde la configuración
        params = self.env['ir.config_parameter'].sudo()
        round_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.round_boe_journal_id'))
        round_journal = self.env['account.journal'].search([('id','=',round_boe_journal_id)])   
        if not round_journal:
            raise UserError(_('Round Journal not configured in settings.'))
        else:
            if not round_journal.default_credit_account_id:
                raise UserError(_('Round Journal credit account not configured in settings.'))
            if not round_journal.default_debit_account_id:
                raise UserError(_('Round Journal debit account not configured in settings.'))
        # Verificamos si existe mas de una letra para ver el ajuste por redondeo
        # if len(self.account_move_line_ids.filtered(lambda line: line.debit > 0)) > 1:
        # if self.company_currency_id.id != self.currency_id.id:
        #     total_debit =  sum(item['debit'] if self.invoice_ids[0].type == 'out_invoice' else item['credit'] for item in vals) / exchange_rate
        #     total_credit = sum(item['amount_currency'] if (item['credit'] if self.invoice_ids[0].type == 'out_invoice' else item['debit']) else 0 for item in vals)
        # else:
        total_debit = float_round(sum(item['debit'] for item in vals),2)
        total_credit = float_round(sum(item['credit'] for item in vals),2)
        # else:
        #     total_debit = 0
        #     total_credit = 0
        difference = (abs(total_credit) - (total_debit)) #* exchange_rate
        # print(float_round(difference,2))
        if float_round(difference,2) > 0:
            # Asiento de diferencia por redondeo ganancia
            val = {
                'name': _('Currency round difference'),
                'bill_form_id': self.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.name,
                # 'exchange_rate': exchange_rate,
                'debit': abs(float_round(difference,2)),# if self.invoice_ids[0].type == 'out_invoice' else 0, #round(abs(difference) * exchange_rate, 2),
                'credit': 0.0, # if self.invoice_ids[0].type == 'out_invoice' else abs(float_round(difference,2)),
                'account_id': round_journal.default_debit_account_id.id,
                'move_id': self.account_move.id,
                # 'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                # 'amount_currency': round(abs(difference) / exchange_rate,2) if self.company_currency_id.id != self.currency_id.id else 0.00,
                # 'tc': exchange_rate,
                'balance': float_round(abs(difference),2), #round(abs(difference) * exchange_rate, 2), # if self.company_currency_id.id != self.currency_id.id else 0.00,
                }
            vals.append(val)
        if float_round(difference,2) < 0:
            # Asiento de diferencia por redondeo perdida
            val = {
                'name': _('Currency round difference'),
                'bill_form_id': self.id,
                'type_document_id': type_document_id.id,
                'nro_comp': self.name,
                # 'exchange_rate': exchange_rate,
                'debit': 0.0,# if self.invoice_ids[0].type == 'out_invoice' else float_round(abs(difference),2),
                'credit': float_round(abs(difference),2),# if self.invoice_ids[0].type == 'out_invoice' else 0, #round(abs(difference) * exchange_rate,2), 
                'account_id': round_journal.default_credit_account_id.id,
                'move_id': self.account_move.id,
                # 'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                # 'amount_currency': round(abs(difference) / exchange_rate,2) * -1 if self.company_currency_id.id != self.currency_id.id else 0.00,
                # 'tc': exchange_rate,
                'balance': float_round(abs(difference),2) * -1, #round(abs(difference) * exchange_rate ,2) * -1, # if self.company_currency_id.id != self.currency_id.id else 0.00,
                }
            vals.append(val)
        # # *********************************** TODO CON MISMO TIPO DE CAMBIO *************************************
        # # Diferencia de cambio
        # # Obtener el diario y las cuentas de diferencia de cambio desde la configuración
        # exchange_journal = self.env.company.currency_exchange_journal_id
        # total_credit = round(sum(item['credit'] for item in vals),2)
        # total_debit = round(sum(item['debit'] for item in vals),2)
        # # if self.invoice_ids[0].type == 'out_invoice':
        # if total_credit > total_debit:
        #     # Asiento de diferencia de cambio por ganancia
        #     val = {
        #         'name': _('Currency exchange rate difference'),
        #         'bill_form_id': self.id,
        #         'exchange_rate': exchange_rate,
        #         'debit': round(abs(total_debit - total_credit),2), # if self.invoice_ids[0].type == 'out_invoice' else 0,
        #         'credit': 0.0, # if self.invoice_ids[0].type == 'out_invoice' else round(abs(total_debit - total_credit),2),
        #         'account_id': exchange_journal.default_debit_account_id.id,
        #         'move_id': self.account_move.id,
        #         'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
        #         # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
        #         # 'amount_currency': round(abs(total_debit - total_credit) / exchange_rate,2)  if self.company_currency_id.id != self.currency_id.id else 0.00,
        #         'tc': exchange_rate,
        #         'balance': round(abs(total_debit - total_credit),2) * (1 if self.invoice_ids[0].type == 'out_invoice' else -1), # if self.company_currency_id.id != self.currency_id.id else 0.00, 
        #         }
        #     vals.append(val)
        # if total_credit < total_debit:
        #     # Asiento de diferencia de cambio por perdida
        #     val = {
        #         'name': _('Currency exchange rate difference'),
        #         'bill_form_id': self.id,
        #         'exchange_rate': exchange_rate,
        #         'debit': 0.0, # if self.invoice_ids[0].type == 'out_invoice' else abs(round(total_debit - total_credit,2)),
        #         'credit': abs(round(total_debit - total_credit,2)), # if self.invoice_ids[0].type == 'out_invoice' else 0,
        #         'account_id': exchange_journal.default_credit_account_id.id,
        #         'move_id': self.account_move.id,
        #         'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
        #         # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
        #         # 'amount_currency': round(abs(total_debit - total_credit) / exchange_rate,2) * -1 if self.company_currency_id.id != self.currency_id.id else 0.00,
        #         'tc': exchange_rate,
        #         'balance': round(abs(total_debit - total_credit),2) * (-1 if self.invoice_ids[0].type == 'out_invoice' else 1),
        #         }
        #     vals.append(val)
        # # *********************************** TODO CON MISMO TIPO DE CAMBIO *************************************

        # else:
        #     if total_credit > total_debit:
        #         # Asiento de diferencia de cambio por ganancia
        #         val = {
        #             'name': _('Currency exchange rate difference'),
        #             'bill_form_id': self.id,
        #             'exchange_rate': exchange_rate,
        #             'debit': round(abs(total_debit - total_credit),2) if self.invoice_ids[0].type == 'out_invoice' else 0,
        #             'credit': 0.0 if self.invoice_ids[0].type == 'out_invoice' else round(abs(total_debit - total_credit),2),
        #             'account_id': exchange_journal.default_debit_account_id.id,
        #             'move_id': self.account_move.id,
        #             'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else '' ,
        #             # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
        #             # 'amount_currency': round(abs(total_debit - total_credit) / exchange_rate,2) if self.company_currency_id.id != self.currency_id.id else 0.00,
        #             'tc': exchange_rate,
        #             'balance': round(abs(total_debit - total_credit),2) * (1 if self.invoice_ids[0].type == 'out_invoice' else -1), # if self.company_currency_id.id != self.currency_id.id else 0.00,
        #             }
        #         vals.append(val)
        #     if total_credit < total_debit:
        #         # Asiento de diferencia de cambio por perdida
        #         val = {
        #             'name': _('Currency exchange rate difference'),
        #             'bill_form_id': self.id,
        #             'exchange_rate': exchange_rate,
        #             'debit': 0.0 if self.invoice_ids[0].type == 'out_invoice' else abs(round(total_debit - total_credit,2)),
        #             'credit': abs(round(total_debit - total_credit,2)) if self.invoice_ids[0].type == 'out_invoice' else 0,
        #             'account_id': exchange_journal.default_credit_account_id.id,
        #             'move_id': self.account_move.id,
        #             'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else '' ,
        #             # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
        #             # 'amount_currency': round(abs(total_debit - total_credit) / exchange_rate,2) * -1 if self.company_currency_id.id != self.currency_id.id else 0.00,
        #             'tc': exchange_rate,
        #             'balance': round(abs(total_debit - total_credit),2) * (-1 if self.invoice_ids[0].type == 'out_invoice' else 1),
        #             }
        #         vals.append(val)
        self.env['account.move.line'].create(vals)
    
    def reconcile(self):
        return self.env['reconcile.form.wizard']\
            .with_context(active_ids=self.ids, active_model='account.bill.form', active_id=self.id, currency=False if self.currency_id != self.company_currency_id else True)\
            .get_post_date_and_rate()
        # return {
        #     'name': _('Reconcile Form Wizard'),
        #     'res_model': 'reconcile.form.wizard',
        #     'view_mode': 'form',
        #     'view_id': self.env.ref('jp_account_bills_of_exchange.view_reconcile_form_wizard').id,
        #     'context': self.env.context,
        #     'target': 'new',
        #     'type': 'ir.actions.act_window',
        # }

    def reconcile_post_date(self):
        reconcile_date = self.env.context.get('reconcile_date')
        exchange_rate = self.env.context.get('exchange_rate')
        self.create_move(reconcile_date, exchange_rate)
        # self.account_move.date = reconcile_date
        # if self.currency_id != self.env.company.currency_id:
        #     self.account_move.currency_rate = exchange_rate
        #     self.account_move.tc_per = True
        #     for line in self.account_move.line_ids:
        #         line.exchange_rate = exchange_rate
        #         line.tc = exchange_rate
        #     # for line in self.account_move.line_ids:
        #     #     print(line.debit, line.credit, line.tc)
        #     #     print(line.amount_currency * line.tc)
        #     # # Actualiza el asiento con los nuevos tipos de cambio 
        #         # line.with_context(check_move_validity=False)._onchange_currency()
        #     #     line._onchange_price_subtotal()
        #     #     print(line.debit, line.credit, line.tc)
        #     #     print(line.amount_currency * line.tc)
        #     self.account_move.line_ids.with_context(check_move_validity=False)._onchange_currency()
        #     self.account_move._recompute_dynamic_lines(recompute_tax_base_amount=True)
        #     # self.account_move.with_context(check_move_validity=False)._onchange_currency()
        # for line in self.account_move.line_ids:
        #     print(line.debit, line.credit, line.tc)
        #     print(line.amount_currency * line.tc)
        if self.state != 'to_reconcile':
            raise UserError(_('You can\'t reconcile a form in %s state.' %self.state))
        self.check_invoice_and_bills()
        self.state = 'done'
        # # Cambia las fechas de las lineas segun corresponda al asiento recien creado
        # # por que al crear las lineas se modifican las fechas a la cabecera del asiento
        # for inv in self.invoice_ids:
        #     self.account_move.line_ids.filtered(lambda x: x.name == inv.ref).with_context(check_move_validity=False).date = inv.invoice_date
        #     self.account_move.line_ids.filtered(lambda x: x.name == inv.ref).date_maturity = inv.invoice_date_due
        # for bill in self.bill_ids:
        #     self.account_move.line_ids.filtered(lambda x: x.name == bill.bill_number).with_context(check_move_validity=False).date = bill.bill_date_issue
        #     self.account_move.line_ids.filtered(lambda x: x.name == bill.bill_number).date_maturity = bill.bill_date_due
        # # Revisamos si hay diferencia de redondeo por cambio y si no borramos todas 
        # # las diferencias por redondeo
        # debit = sum(self.account_move.line_ids.filtered(lambda x: x.name != _('Currency round difference')).mapped('debit'))
        # credit = sum(self.account_move.line_ids.filtered(lambda x: x.name != _('Currency round difference')).mapped('credit'))
        # difference = float_round(debit - credit, 2)
        # if difference != 0:
        #     if difference < 0:
        #         self.account_move.line_ids.filtered(lambda l: l.name == _('Currency round difference')).with_context(check_move_validity=False).debit = abs(difference)
        #         self.account_move.line_ids.filtered(lambda l: l.name == _('Currency round difference')).with_context(check_move_validity=False).credit = 0
        #     else:
        #         self.account_move.line_ids.filtered(lambda l: l.name == _('Currency round difference')).with_context(check_move_validity=False).debit = 0
        #         self.account_move.line_ids.filtered(lambda l: l.name == _('Currency round difference')).with_context(check_move_validity=False).credit = abs(difference)
        # else:
        #     self.account_move.line_ids.filtered(lambda l: l.name == _('Currency round difference')).unlink()
        # # Actualiza el asiento con los nuevos tipos de cambio
        # self.account_move.with_context(check_move_validity=False)._onchange_currency()
        # for l in self.account_move.line_ids:
        #     print(l.name, l.debit, l.credit)
        #     print(l.amount_currency)
        self.account_move.action_post()
        for invoice in self.invoice_ids:
            if abs(invoice.amount_residual_signed) > 0:
                invoice.bill_form_id = self
                invoice.exchange_amount = invoice.amount_residual
                invoice.exchange_amount_signed = invoice.amount_residual_signed
                for line in self.account_move_line_ids:
                    if self.invoice_ids[0].type == 'out_invoice':
                        if line.credit > 0 and not line.reconciled and\
                            line.name != _('Currency exchange rate difference') and\
                            line.name != _('Retention: ') + self.name and\
                            line.name != _('Currency round difference') and\
                            line.name != _('Balance in favor of the client'):
                            # Pagar la factura
                            # TODO si la cuenta del diario al crear la letra no es la misma que
                            # la factura no va a reconciliar la factura
                            raise_warning = True
                            for inv_line in invoice.line_ids:
                                if inv_line.account_id == self.journal_id.default_credit_account_id:
                                    raise_warning = False
                            if raise_warning:
                                raise UserError (_('The debit account in the journal is different than the account on the invoice. Please change the settings for customer journal in bills of exchange.'))
                            invoice.js_assign_outstanding_line(line.id)
                    else:
                        if line.debit  > 0 and not line.reconciled and\
                            line.name != _('Currency exchange rate difference') and\
                            line.name != _('Retention: ') + self.name and\
                            line.name != _('Currency round difference') and\
                            line.name != _('Balance in favor of the client'):
                            # Pagar la factura
                            invoice.js_assign_outstanding_line(line.id)
            else:
                raise UserError(_('The invoice %s has no residual amount to pay.') %invoice.name)
        for bill in self.bill_ids:
            bill.last_state = bill.state_of_bill
            bill.state_of_bill = 'portfolio' if self.invoice_ids[0].type == 'out_invoice' else 'accepted'
            bill.last_account_id = bill.account_id

    def cancel(self):
        if any(x.state_of_bill not in ['portfolio', 'to_accept'] for x in self.bill_ids) and not self.env.user.login == 'admin':
            raise UserError(_("You can\'t cancel a form with bills in different state than portfolio."))
        self.account_move.button_draft()
        for line in self.account_move_line_ids:
            line.remove_move_reconcile()
        self.account_move.line_ids.unlink()
        self.state = 'draft'
        for bill in self.bill_ids:
            bill.state_of_bill = 'draft'
        for invoice in self.invoice_ids:
            invoice.bill_form_id = False

    @api.onchange('bill_ids', 'invoice_ids')
    def onchange_bill_ids(self):
        self.total_invoices = self.get_total_invoices()

        for bill in self.bill_ids:
            if bill.bill_currency_id != self.company_currency_id:
                bill.bill_amount_total = bill.bill_amount_total_signed / bill.exchange_rate
            else:
                bill.bill_amount_total = bill.bill_amount_total_signed
            # bill.account_id = self.journal_id.default_debit_account_id

        self.total_bills = self.get_total_bills()

    # def update_sequence(self):
    #     seq = self.env['ir.sequence'].search([('code','=','bill.exchange')])
    #     next_number = seq.get_next_char(seq.number_next_actual)
    #     x = 0
    #     for bill in self.bill_ids:
    #         bill.bill_number = str(next_number[:seq.padding]) + str(int(next_number[len(next_number)-seq.padding:]) + x).zfill(4)
    #         x += 1

    def action_form_send_to_bank(self):
        return self.env['account.send.bank']\
            .with_context(active_ids=self.bill_ids, active_model='account.bill', active_id=self.id)\
            .action_send_to_bank()

    def update_sequence_final(self):
        # seq = self.env['ir.sequence'].search([('code','=','bill.exchange')])
        # next_number = seq.get_next_char(seq.number_next_actual)
        # x = 0
        y = 1
        for bill in self.bill_ids:
            # if bill.bill_number == _('Bill'):
                # bill.bill_number = str(next_number[:seq.padding]) + str(int(next_number[len(next_number)-seq.padding:]) + x).zfill(4)
            # if bill.responsable_id == bill.acceptor_id:
            if bill.bill_number == False:
                bill.bill_number = self.name.split('-')[1] + str(y).zfill(2) + '00'
                y += 1
                # x += 1
        # seq.number_next_actual = seq.number_next_actual + x

    # def update_sequence_final_all(self):
    #     # seq = self.env['ir.sequence'].search([('code','=','bill.exchange')])
    #     # next_number = seq.get_next_char(seq.number_next_actual)
    #     # x = 0
    #     for form in self:
    #         y = 1
    #         for bill in form.bill_ids:
    #             if bill.bill_number.split('-')[0] == form.name.split('-')[1]:
    #                 break
    #             # if bill.bill_number == _('Bill'):
    #                 # bill.bill_number = str(next_number[:seq.padding]) + str(int(next_number[len(next_number)-seq.padding:]) + x).zfill(4)
    #             bill.bill_number = form.name.split('-')[1] + str(y).zfill(2) + '00'
    #             y += 1

    def open_send_bank_view(self):
        [action] = self.env.ref('jp_account_bills_of_exchange.action_account_send_bank').read()
        ids = self.send_form_ids.ids
        action['domain'] = [('id', 'in', ids)]
        return action
        
    def correccion_de_conciliaciones(self):
        # for line in self.account_move_line_ids:
        #     if not line.reconciled and line.account_id.reconcile:
        #         lines = line
        #         for send_form in self.send_form_ids:
        #             lines += send_form.account_move_line_ids.filtered(lambda l: l.name == line.name and l.account_id == line.account_id and not l.reconciled)
        #         lines.reconcile()

        # Modificar aceptante en lines de asiento contable **************************************

        for bill in self.bill_ids:
            for line in self.account_move_line_ids:
                if bill.bill_number == line.name:
                    line.partner_id = bill.acceptor_id
            for line in bill.account_move_line_ids:
                line.partner_id = bill.acceptor_id
            if bill.bank_disbursement_id:
                for line in bill.bank_disbursement_id.account_move_line_ids:
                    if line.nro_comp == bill.bill_number:
                        line.partner_id = bill.acceptor_id
                    if line.account_internal_type == 'liquidity':
                        line.partner_id = bill.bank_disbursement_id.journal_id.bank_partner_id
                        line.type_document_id = self.env['einvoice.catalog.01'].search([('code','=','00')])
                        line.nro_comp = bill.send_form_id.name
            if bill.send_form_id:
                for line in bill.send_form_id.account_move_line_ids:
                    if line.nro_comp == bill.bill_number:
                        line.partner_id = bill.acceptor_id
            if bill.protest_payment_id:
                for line in bill.protest_payment_id.account_move_line_ids:
                    if line.nro_comp == bill.bill_number:
                        line.partner_id = bill.acceptor_id