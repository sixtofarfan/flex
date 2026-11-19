from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from . import amount_to_text_es
from datetime import datetime, timedelta, date
from odoo.tools import float_round

TYPE2JOURNAL = {'out_invoice':'sale',
 'in_invoice':'purchase',
 'out_refund':'sale',
 'in_refund':'purchase'}

class RefinancingForm(models.Model):
    _name = 'account.refinancing.form'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Refinancing Form'
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

    name = fields.Char('Form number', copy=False, readonly=True, default=(lambda x: _('New')))
    partner_id = fields.Many2one('res.partner', 'Partner', tracking=True)
    exchange_date = fields.Date('Refinancing Date', default=fields.Date.context_today, tracking=True)
    refinancing_rate = fields.Float(string='Refinancing rate', digits=(12, 2))
    gloss = fields.Char('Gloss', required=True)
    reference = fields.Char('Reference')
    bill_ids = fields.One2many('account.bill', 'refinancing_form_id', 'Bills of Exchange', tracking=True)
    overdue_bill_ids = fields.Many2many('account.bill', string='Overdue Bills of Exchange', tracking=True)
    invoice_ids = fields.Many2many('account.move', string='Invoices', tracking=True)
    account_move_line_ids = fields.One2many('account.move.line', 'refinancing_form_id', string='Account move lines')
    custom_exchange_rate = fields.Boolean(string='Custom Exchange Rate')
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1, tracking=True)
    account_move = fields.Many2one('account.move', 'Account Move')
    state = fields.Selection([('draft', 'Draft'), ('to_reconcile', 'To Reconcile'), ('done', 'Done')], string='State', default='draft', tracking=True)
    retention_percentage = fields.Float(string='Retention percentage (%)', tracking=True)
    apply_retention = fields.Boolean(string='Apply retentions')
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.company),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, states={'draft': [('readonly', False)]},string='Currency',default=(lambda self: self.env.user.company_id.currency_id))
    total_retention = fields.Monetary('Total retencion', currency_field='currency_id', default=0)
    total_retention_signed = fields.Monetary('Total retencion Signed', currency_field='company_currency_id', default=0)
    total_exchange = fields.Monetary('Total exchange', currency_field='company_currency_id', default=0)
    total_invoices = fields.Monetary('Total Invoices', currency_field='company_currency_id', default=0)
    total_overdue = fields.Monetary('Total Overdue', currency_field='company_currency_id', default=0)
    total_bills = fields.Monetary('Total Bills', currency_field='company_currency_id', default=0)
    bills_qty = fields.Integer('Bills quantity', default=1)
    days_due_first = fields.Integer('Expiration days of 1st Bill', default=15)
    range_bill = fields.Integer('Range of days between bills', default=15)
    guarantee_id = fields.Many2one('res.partner', string='Guarantee')
    acceptor_id = fields.Many2one('res.partner', string='Acceptor')
    journal_id = fields.Many2one('account.journal', string='Journal for Bills of Exchange',default=_get_default_journal_id)
    type_form = fields.Char(string="Form Type", default='1')
    send_form_ids = fields.Many2many('account.send.bank', string='Send to Bank Forms')
    interest_lp_ids = fields.One2many('interest.late.payment', 'refinancing_form_id', 'Interest for Late Payment', tracking=True)
    interest_or_ids = fields.One2many('interest.on.refinancing', 'refinancing_form_id', 'Interest on Refinancing', tracking=True)
    # apply_invoices = fields.Boolean(string='Apply Invoices')
    debit_note_lp_id = fields.Many2one('account.move', string='Debit note interest for late payment')
    debit_note_or_id = fields.Many2one('account.move', string='Debit note interest on refinancing')
    add_dn = fields.Boolean(string='Add debit invoices')
    
    @api.onchange('gloss')
    def _onchange_gloss(self):
        if self.account_move:
            self.account_move.glosa = self.gloss
            
    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        # self.bank_position = self.journal_id.bank_position
        self.currency_id = self.journal_id.currency_id if self.journal_id.currency_id else self.env.company.currency_id

    @api.onchange('invoice_ids')
    def _check_form_type(self):
        if self.invoice_ids:
            # if self.invoice_ids[0].type == 'out_invoice':
            self.type_form = '1'
            # else:
            #     self.type_form = False
    
    def get_exchange_rate(self, amount, currency, company, date):
        return self.currency_id._convert(amount, currency, company, date, False)

    @api.onchange('currency_id','exchange_date','custom_exchange_rate')
    def onchange_currency_id(self):
        if self.currency_id != self.env.user.company_id.currency_id:
            rates = self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id),('name','=',self.exchange_date or fields.Date.context_today)])
            if not rates:
                rates = self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id)], order='name desc', limit=1)
                # if rates:
                #     self.exchange_rate = round(1/rates.rate,3)
                #     return {
                #         'warning': {'title': _("Exchange Rate"), 'message': _('There is no exchange rate for that date. All the journal entries will be calculated with this rate %s from %s') %(round(1/rates.rate,3),datetime.strftime(rates.name, "%d/%m/%Y")),},
                #         }
                # else:
                #     raise UserError(_('There is no exchange rate for that date. All the journal entries will be calculated with this rate %s') %self.exchange_rate)
        if not self.custom_exchange_rate:
            if self.currency_id.id == self.company_currency_id.id:
                self.exchange_rate = 1
            else:
                self.exchange_rate = self.get_exchange_rate(1, self.company_id.currency_id, self.company_id, self.exchange_date or fields.Date.context_today)
        self.onchange_retention()

    @api.onchange('apply_retention','retention_percentage','total_invoices')
    def onchange_retention(self):
        self.set_total_retention()

    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('account.refinancing.form') or _('New')
        return super(RefinancingForm, self).create(values)

    def get_total_overdue(self):
        total_overdue_bills = 0
        if self.overdue_bill_ids:
            for line in self.overdue_bill_ids:
                partial_payments = 0
                for payment in line.partial_payment_ids:
                    partial_payments += payment.payment_amount_signed 
                total_overdue_bills += line.bill_amount_total - partial_payments
        return round(total_overdue_bills,2)

    def get_total_invoices(self):
        total_invoices = 0
        if self.invoice_ids:
            for line in self.invoice_ids:
                if line.type_document_id.code == '08' and self.add_dn:
                    total_invoices += line.amount_residual
                else:
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
            self.total_retention = (self.get_total_invoices() if self.add_dn else 0 + self.get_total_overdue()) * (self.retention_percentage / 100)
            self.total_retention_signed = (self.get_total_invoices() if self.add_dn else 0 + self.get_total_overdue()) * self.exchange_rate * (self.retention_percentage / 100)
            self.total_bills = self.total_bills - self.total_retention
        else:
            self.total_retention = 0
        self.update_bills()

    def validate_bills_and_invoices(self):
        # res = super(RefinancingForm, self).write(vals)
        if self.state != 'done':
            total_invoices = self.get_total_invoices() + self.get_total_overdue()
            total_bills = self.get_total_bills()
 
            if round(total_bills,2) + self.total_retention > total_invoices:
                raise ValidationError('Bills total is greather than invoices total.')

        # return res

    def unlink(self):
        for refinancing_form in self:
            if refinancing_form.state != 'draft' and not self._context.get('force_delete'):
                raise UserError(_("You cannot delete an entry which has been posted once."))
            refinancing_form.account_move_line_ids.unlink()
            refinancing_form.bill_ids.unlink()
        return super(RefinancingForm, self).unlink()

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
        for bill in self.bill_ids:
            total_invoices = (self.total_invoices if self.add_dn else 0) + self.total_overdue - self.total_retention
            if not self.add_dn:
                bill.bill_amount_total = round(total_invoices / self.bills_qty,2)
                bill.bill_amount_signed = round(bill.bill_amount_total * self.exchange_rate, 2)
        self.calculate_interest()

    def create_bills(self):
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
        if self.total_invoices or self.total_overdue:
            # Obtener el tipo de cambio para la fecha de intercambio de letras
            self.onchange_currency_id()
            # Obtener el diario y las cuentas desde la configuración
            # if self.invoice_ids[0].type == 'out_invoice':
            # Obtener la cuenta de letras de cliente desde la configuración
            params = self.env['ir.config_parameter'].sudo()
            customer_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.customer_boe_journal_id'))
            self.journal_id = self.env['account.journal'].search([('id','=',customer_boe_journal_id)])
            if not self.journal_id:
                raise UserError('You must configure the Bill of Exchange Journal in settings.')
            if self.total_invoices > 0 or self.total_overdue > 0:
                bill_date_due = datetime.strptime(str(self.exchange_date), '%Y-%m-%d') + timedelta(days=(self.days_due_first))  
                # Cambia la fecha para evitar sabados, domingos y feriados.
                bill_date_due_changed = self.change_bill_date(bill_date_due)
                total_invoices = self.total_invoices + self.total_overdue - self.total_retention
                bill_amount = round(total_invoices / self.bills_qty,2)
                bill_amount_signed = round(bill_amount * self.exchange_rate, 2)
                aux = bill_amount
                result = []
                result.append((0, 0,
                {'bill_date_due':bill_date_due_changed + timedelta(days=1),
                'bill_date_issue':self.exchange_date + timedelta(days=1),
                # 'bill_form_id':self.id,
                'refinancing_form_id':self.id,
                'responsable_id':self.partner_id.id,
                'guarantee_id':self.guarantee_id.id,
                'acceptor_id':(self.acceptor_id.id if self.acceptor_id else self.partner_id.id),# if self.invoice_ids[0].type == 'out_invoice' else self.env.company.partner_id.id,
                'bill_currency_id':self.currency_id.id,
                'bill_amount_total':bill_amount,
                'bill_amount_total_signed':bill_amount_signed,
                'exchange_rate':self.exchange_rate,
                'account_id': self.journal_id.default_debit_account_id.id, # if self.invoice_ids[0].type == 'out_invoice' else self.journal_id.default_credit_account_id.id,
                'type_bill': 'receivable',# if self.invoice_ids[0].type == 'out_invoice' else 'payable',
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
                    bill_amount_signed = round(bill_amount * self.exchange_rate,2)
                    result.append((0, 0,
                    {'bill_date_due':bill_date_due_changed + timedelta(days=1),
                    'bill_date_issue':self.exchange_date + timedelta(days=1),
                    # 'bill_form_id':self.id,
                    'refinancing_form_id':self.id,
                    'responsable_id':self.partner_id.id,
                    'guarantee_id':self.guarantee_id.id,
                    'acceptor_id':(self.acceptor_id.id if self.acceptor_id else self.partner_id.id),# if self.invoice_ids[0].type == 'out_invoice' else self.env.company.partner_id.id,
                    'bill_currency_id':self.currency_id.id,
                    'bill_amount_total':bill_amount,
                    'bill_amount_total_signed':bill_amount_signed,
                    'exchange_rate':self.exchange_rate,
                    'account_id':self.journal_id.default_debit_account_id.id, # if self.invoice_ids[0].type == 'out_invoice' else self.journal_id.default_credit_account_id.id,
                    'type_bill': 'receivable',# if self.invoice_ids[0].type == 'out_invoice' else 'payable',
                    'amount_text':amount_to_text_es.amount_to_text(bill_amount, self.currency_id.name)}))

                self.bill_ids = result
            # Calcula los intereses
            self.calculate_interest()
            self.update_sequence()

    def add_dn_bill(self):
        self.add_dn = not self.add_dn
        bill_date_due = self.bill_ids[len(self.bill_ids)-1].bill_date_due + timedelta(days=(self.range_bill))
        # Cambia la fecha para evitar sabados, domingos y feriados.
        bill_date_due_changed = self.change_bill_date(bill_date_due) 
        self.bill_ids = [(0, 0, 
            {'is_from_dn': True,
            'bill_date_due':bill_date_due_changed + timedelta(days=1),
            'bill_date_issue':self.exchange_date + timedelta(days=1),
            'refinancing_form_id':self.id,
            'responsable_id':self.partner_id.id,
            'guarantee_id':self.guarantee_id.id,
            'acceptor_id':(self.acceptor_id.id if self.acceptor_id else self.partner_id.id),# if self.invoice_ids[0].type == 'out_invoice' else self.env.company.partner_id.id,
            'bill_currency_id':self.currency_id.id,
            'bill_amount_total':self.get_total_invoices(),
            'bill_amount_total_signed': self.get_total_invoices() * self.exchange_rate,
            'exchange_rate':self.exchange_rate,
            'account_id':self.journal_id.default_debit_account_id.id, # if self.invoice_ids[0].type == 'out_invoice' else self.journal_id.default_credit_account_id.id,
            'type_bill': 'receivable',# if self.invoice_ids[0].type == 'out_invoice' else 'payable',
            'amount_text':amount_to_text_es.amount_to_text(self.get_total_invoices(), self.currency_id.name)})]
        # self.update_sequence()
    
    def del_dn_bill(self):
        self.add_dn = not self.add_dn
        for bill in self.bill_ids:
            if bill.is_from_dn:
                bill.unlink()

    def calculate_interest(self):
        # Cargamos los intereses por mora a la vista
        self.interest_lp_ids.unlink()
        val={}
        vals=[]
        for bill in self.overdue_bill_ids:
            days = (self.exchange_date - bill.bill_date_due).days
            val = {
                    'refinancing_form_id': self.id,
                    'document_type': 'bill',
                    'document_type_sunat': False,
                    'amount': bill.bill_amount_total,
                    'original_due_date':bill.bill_date_due,
                    'new_due_date': self.exchange_date,
                    'days': days,
                    'refinancing_rate': self.refinancing_rate,
                    'currency_id': bill.bill_currency_id.id,
                    # Formula financiera para el calculo de intereses proporcionada por polimaster
                    'interest': (((self.refinancing_rate / 100 + 1) ** (days/360)) - 1) * bill.bill_amount_total,
                    # 'document_state': bill.state_of_bill,
                }
            vals.append(val)
        self.env['interest.late.payment'].create(vals)
        # Cargamos los intereses por refinanciamiento a la vista
        self.interest_or_ids.unlink()
        val={}
        vals=[]
        for bill in self.bill_ids:
            days = (bill.bill_date_due - (self.exchange_date + timedelta(days=1))).days
            val = {
                    'refinancing_form_id': self.id,
                    'document_type': 'bill',
                    'document_type_sunat': False,
                    'amount': bill.bill_amount_total,
                    'original_due_date': self.exchange_date + timedelta(days=1),
                    'new_due_date': bill.bill_date_due,
                    'days': days,
                    'refinancing_rate': self.refinancing_rate,
                    'currency_id': bill.bill_currency_id.id,
                    # Formula financiera para el calculo de intereses proporcionada por polimaster
                    'interest': (((self.refinancing_rate / 100 + 1) ** (days/360)) - 1) * bill.bill_amount_total,
                    # 'document_state': bill.state_of_bill,
                }
            vals.append(val)
        self.env['interest.on.refinancing'].create(vals)
        # if self.refinancing_rate <= 0:
        #     raise UserError(_('Intereset rate must be greather than zero.'))

    def clear_interest(self):
        if self.debit_note_lp_id or self.debit_note_or_id and self.debit_note_lp_id.state == 'posted' or self.debit_note_or_id.state == 'posted':
            raise UserError(_('The interests allready have debit notes created and posted. You must first cancel this debit notes to clear interest.'))
        self.debit_note_lp_id = False
        self.debit_note_or_id = False
        self.interest_lp_ids.unlink()
        self.interest_or_ids.unlink()

    def update_form(self):
        self.total_invoices = self.get_total_invoices()
        self.total_overdue = self.get_total_overdue()
        self.total_bills = self.get_total_bills()
        self.set_total_retention()

    def process(self):
        self.validate_bills_and_invoices()
        if self.state != 'draft':
            raise UserError(_('You can\'t process a form in %s state.' %self.state))
        if not self.bill_ids:
            raise UserError(_('There is no bills to exchange for invoices.'))
        val = {}
        vals = []
        val = {
            'name': self.name,
            'currency_id': self.currency_id.id,
            'date': self.exchange_date,
            'invoice_date': self.exchange_date,
            'journal_id': self.journal_id.id,
            'glosa': self.gloss,
            'type': 'bill',
            'currency_rate': self.exchange_rate,
        }
        if not self.account_move:
            self.account_move = self.env['account.move'].create(val)
        # Entrega los numeros finales
        # self.update_sequence_final()
        # Letras nuevas
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
        for bill in self.bill_ids:
            val = {
                'ref': self.name,
                'refinancing_form_id': self.id,
                'move_id': self.account_move.id,
                'partner_id': bill.acceptor_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': bill.bill_number,
                'exchange_rate': self.exchange_rate,
                'name': bill.bill_number,
                'date': self.exchange_date,
                'journal_id': self.journal_id.id,
                'currency_id': bill.bill_currency_id.id if bill.company_currency_id.id != bill.bill_currency_id.id else False,
                'company_id': bill.company_id.id,
                'company_currency_id': bill.company_currency_id.id,
                'account_id': self.journal_id.default_debit_account_id.id, # if self.invoice_ids[0].type == 'out_invoice' else self.journal_id.default_credit_account_id.id,
                'debit': float_round(bill.bill_amount_total * (self.exchange_rate if bill.company_currency_id.id != bill.bill_currency_id.id else 1), 2), #bill.bill_amount_total_signed, # if bill.state_of_bill == 'disbursed' else 0,
                'amount_currency': bill.bill_amount_total if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
                'tc': self.exchange_rate,
                'balance': bill.bill_amount_total * (self.exchange_rate if bill.company_currency_id.id != bill.bill_currency_id.id else 1), #bill.bill_amount_total_signed ,# * (-1 if bill.state_of_bill == 'disbursed' else 1), # if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
                'credit':  0, # if bill.state_of_bill == 'disbursed' else bill.bill_amount_total_signed,
                'date_maturity': bill.bill_date_due,
            }
            vals.append(val)
        # Letras que se refinancian
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','LE')])
        for bill in self.overdue_bill_ids:
            val = {
                'ref': self.name,
                # 'bill_form_id': self.id,
                'partner_id': bill.acceptor_id.id,
                'type_document_id': type_document_id.id,
                'nro_comp': bill.bill_number,
                'refinancing_form_id': self.id,
                'move_id': self.account_move.id,
                'exchange_rate': self.exchange_rate,
                'name': bill.bill_number,
                'date': self.exchange_date,
                'journal_id': self.journal_id.id,
                'currency_id': bill.bill_currency_id.id if bill.company_currency_id.id != bill.bill_currency_id.id else False,
                'company_id': bill.company_id.id,
                'company_currency_id': bill.company_currency_id.id,
                'account_id': bill.account_id.id, #self.journal_id.default_debit_account_id.id, # if self.invoice_ids[0].type == 'out_invoice' else self.journal_id.default_credit_account_id.id,
                'debit': 0, #if self.invoice_ids[0].type == 'out_invoice' else 0,
                'amount_currency': bill.bill_amount_total * -1 if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
                'tc':  self.exchange_rate, #bill.exchange_rate,
                'balance': float_round(bill.bill_amount_total * (self.exchange_rate if bill.company_currency_id.id != bill.bill_currency_id.id else 1) * -1, 2), #bill.bill_amount_total_signed * -1, # if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
                'credit':  float_round(bill.bill_amount_total * (self.exchange_rate if bill.company_currency_id.id != bill.bill_currency_id.id else 1), 2), #bill.bill_amount_total_signed, #if self.invoice_ids[0].type == 'out_invoice' else bill.bill_amount_total_signed,
                'date_maturity': bill.bill_date_due,
            }
            vals.append(val)
            bill.state_of_bill = 'refinanced'
        # Facturas
        for invoice in self.invoice_ids:
            val = {
                'ref': self.name,
                # 'bill_form_id': self.id,
                'partner_id': invoice.partner_id.id,
                'type_document_id': invoice.type_document_id.id,
                'nro_comp': invoice.ref,
                'refinancing_form_id': self.id,
                'move_id': self.account_move.id,
                'exchange_rate':  self.exchange_rate, #invoice.amount_total_signed / invoice.amount_total if self.currency_id != self.env.user.company_id.currency_id else 0, 
                'name': invoice.name,
                'date': self.exchange_date,
                'journal_id': self.journal_id.id,
                'company_id': invoice.company_id.id,
                'currency_id': invoice.currency_id.id if invoice.company_currency_id.id != invoice.currency_id.id else False,
                'company_currency_id' : invoice.company_currency_id.id,
                'account_id': self.journal_id.default_credit_account_id.id,
                'amount_currency': invoice.amount_residual * -1 if invoice.company_currency_id.id != invoice.currency_id.id else 0,
                'tc':  self.exchange_rate, #invoice.currency_rate, # amount_total_signed / invoice.amount_total if self.currency_id != self.env.user.company_id.currency_id else 0, 
                'balance': float_round(invoice.amount_residual * (self.exchange_rate if invoice.company_currency_id.id != invoice.currency_id.id else 1) * -1, 2),#invoice.amount_residual_signed * -1, #* (-1 if self.invoice_ids[0].type == 'out_invoice' else 1),
                'debit': 0,# if self.invoice_ids[0].type == 'out_invoice' else abs(invoice.amount_residual_signed),
                'credit': float_round(abs(invoice.amount_residual) * (self.exchange_rate if invoice.company_currency_id.id != invoice.currency_id.id else 1), 2), #abs(invoice.amount_residual_signed),# if self.invoice_ids[0].type == 'out_invoice' else 0,
                'date_maturity': invoice.invoice_date_due,
                }
            vals.append(val)
        # Retención
        if self.apply_retention:
            # Obtener la cuenta de retenciones desde la configuración
            params = self.env['ir.config_parameter'].sudo()
            retention_boe_account_id = int(params.get_param('jp_account_bills_of_exchange.retention_boe_account_id'))
            retention_account_id = self.env['account.account'].search([('id','=',retention_boe_account_id)])
            val = {
                'ref': _('Retention: ') + self.name,
                # 'bill_form_id': self.id,
                'refinancing_form_id': self.id,
                'move_id': self.account_move.id,
                'exchange_rate': self.exchange_rate,
                'name': _('Retention: ') + self.name,
                'date': self.exchange_date,
                'journal_id': self.journal_id.id,
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                'company_currency_id' : self.company_currency_id.id,
                'account_id': retention_account_id.id,
                'amount_currency': self.total_retention if self.company_currency_id.id != self.currency_id.id else 0,
                'tc': self.exchange_rate,
                'balance': self.total_retention_signed,# * (1 if self.invoice_ids[0].type == 'out_invoice' else -1),
                'debit': self.total_retention_signed,# if self.invoice_ids[0].type == 'out_invoice' else 0,
                'credit': 0,# if self.invoice_ids[0].type == 'out_invoice' else self.total_retention_signed,
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
        if self.company_currency_id.id != self.currency_id.id:
        #     total_debit =  sum(item['debit'] for item in vals) #/ self.exchange_rate
        #     total_credit = sum(item['amount_currency'] * self.exchange_rate if item['credit'] else 0 for item in vals)
        # else:
            total_debit = sum(item['debit'] for item in vals)
            total_credit = sum(item['credit'] for item in vals)
            difference = abs(total_credit) - (total_debit)
            if difference > 0:
                # Asiento de diferencia por redondeo ganancia
                val = {
                    'name': _('Currency round difference'),
                    # 'bill_form_id': self.id,
                    'refinancing_form_id': self.id,
                    # 'exchange_rate': self.exchange_rate,
                    'debit': abs(difference),# if self.invoice_ids[0].type == 'out_invoice' else 0, #round(abs(difference) * self.exchange_rate, 2),
                    'credit': 0.0,# if self.invoice_ids[0].type == 'out_invoice' else abs(difference),
                    'account_id': round_journal.default_debit_account_id.id,
                    'move_id': self.account_move.id,
                    # 'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                    # 'amount_currency': abs(difference) / self.exchange_rate if self.company_currency_id.id != self.currency_id.id else 0.00,
                    # 'tc': self.exchange_rate,
                    'balance': difference,# * (1 if self.invoice_ids[0].type == 'out_invoice' else -1), #round(abs(difference) * self.exchange_rate, 2), # if self.company_currency_id.id != self.currency_id.id else 0.00,
                    }
                vals.append(val)
            if difference < 0:
                # Asiento de diferencia por redondeo perdida
                val = {
                    'name': _('Currency round difference'),
                    # 'bill_form_id': self.id,
                    'refinancing_form_id': self.id,
                    # 'exchange_rate': self.exchange_rate,
                    'debit': 0.0,# if self.invoice_ids[0].type == 'out_invoice' else abs(difference),
                    'credit': abs(difference),# if self.invoice_ids[0].type == 'out_invoice' else 0, #round(abs(difference) * self.exchange_rate,2), 
                    'account_id': round_journal.default_credit_account_id.id,
                    'move_id': self.account_move.id,
                    # 'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                    # 'amount_currency': (abs(difference) / self.exchange_rate) * -1 if self.company_currency_id.id != self.currency_id.id else 0.00,
                    # 'tc': self.exchange_rate,
                    'balance': difference * -1,# * (-1 if self.invoice_ids[0].type == 'out_invoice' else 1), #round(abs(difference) * self.exchange_rate ,2) * -1, # if self.company_currency_id.id != self.currency_id.id else 0.00,
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
                # 'bill_form_id': self.id,
                'refinancing_form_id': self.id,
                # 'exchange_rate': self.exchange_rate,
                'debit': round(abs(total_debit - total_credit),2),# if self.invoice_ids[0].type == 'out_invoice' else 0,
                'credit': 0.0,# if self.invoice_ids[0].type == 'out_invoice' else round(abs(total_debit - total_credit),2),
                'account_id': exchange_journal.default_debit_account_id.id,
                'move_id': self.account_move.id,
                # 'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                # 'amount_currency': round(abs(total_debit - total_credit) / self.exchange_rate,2)  if self.company_currency_id.id != self.currency_id.id else 0.00,
                # 'tc': self.exchange_rate,
                'balance': round(abs(total_debit - total_credit),2),# * (1 if self.invoice_ids[0].type == 'out_invoice' else -1), # if self.company_currency_id.id != self.currency_id.id else 0.00, 
                }
            vals.append(val)
        if total_credit < total_debit:
            # Asiento de diferencia de cambio por perdida
            val = {
                'name': _('Currency exchange rate difference'),
                # 'bill_form_id': self.id,
                'refinancing_form_id': self.id,
                # 'exchange_rate': self.exchange_rate,
                'debit': 0.0,# if self.invoice_ids[0].type == 'out_invoice' else abs(round(total_debit - total_credit,2)),
                'credit': abs(round(total_debit - total_credit,2)),# if self.invoice_ids[0].type == 'out_invoice' else 0,
                'account_id': exchange_journal.default_credit_account_id.id,
                'move_id': self.account_move.id,
                # 'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                # 'amount_currency': round(abs(total_debit - total_credit) / self.exchange_rate,2) * -1 if self.company_currency_id.id != self.currency_id.id else 0.00,
                # 'tc': self.exchange_rate,
                'balance': round(abs(total_debit - total_credit),2) * -1,#(-1 if self.invoice_ids[0].type == 'out_invoice' else -1),
                }
            vals.append(val)
        self.env['account.move.line'].create(vals)
        self.state = 'to_reconcile'
        for bill in self.bill_ids:
            bill.state_of_bill = 'to_accept'

    def reconcile(self):
        return self.env['reconcile.form.wizard']\
            .with_context(active_ids=self.ids, active_model='account.refinancing.form', active_id=self.id, currency=False if self.currency_id != self.company_currency_id else True)\
            .get_post_date_and_rate()

    def reconcile_post_date(self):
        reconcile_date = self.env.context.get('reconcile_date')
        exchange_rate = self.env.context.get('exchange_rate')
        self.account_move.date = reconcile_date
        if self.currency_id != self.env.company.currency_id:
            self.account_move.currency_rate = exchange_rate
            for line in self.account_move.line_ids:
                line.exchange_rate = exchange_rate
                line.tc = exchange_rate
            # Actualiza el asiento con los nuevos tipos de cambio
            self.account_move.with_context(check_move_validity=False)._onchange_currency()
        if self.state != 'to_reconcile':
            raise UserError(_('You can\'t reconcile a form in %s state.' %self.state))
        self.state = 'done'
        self.account_move.action_post()
        for invoice in self.invoice_ids:
            if abs(invoice.amount_residual_signed) > 0:
                invoice.exchange_amount = invoice.amount_residual
                invoice.exchange_amount_signed = invoice.amount_residual_signed
                for line in self.account_move_line_ids:
                    # if self.invoice_ids[0].type == 'out_invoice':
                    if line.credit > 0 and not line.reconciled and\
                        line.name != _('Currency exchange rate difference') and\
                        line.name != _('Retention: ') + self.name and\
                        line.name != _('Currency round difference'):
                        # Pagar la factura
                        invoice.js_assign_outstanding_line(line.id)
            else:
                raise UserError(_('The invoice %s has no residual amount to pay.') %invoice.name)
        # for bill in self.overdue_bill_ids:
        #     for line in self.account_move_line_ids:
        #         # if self.invoice_ids[0].type == 'out_invoice':
        #         if line.credit > 0 and not line.reconciled and\
        #             line.name != _('Currency exchange rate difference') and\
        #             line.name != _('Retention: ') + self.name and\
        #             line.name != _('Currency round difference'):
        #             # Pagar la factura
        #             invoice.js_assign_outstanding_line(line.id)
        for bill in self.bill_ids:
            bill.last_state = bill.state_of_bill
            bill.state_of_bill = 'portfolio' # if self.invoice_ids[0].type == 'out_invoice' else 'accepted'
            bill.last_account_id = bill.account_id

    def cancel(self):
        if any(x.state_of_bill not in ['portfolio', 'to_accept'] for x in self.bill_ids):
            raise UserError(_("You can\'t cancel a form with bills in different state than portfolio."))
        self.account_move.button_draft()
        self.account_move_line_ids.unlink()
        self.state = 'draft'
        for bill in self.bill_ids:
            bill.state_of_bill = 'draft'

    @api.onchange('bill_ids','invoice_ids')
    def onchange_bill_ids(self):
        self.total_invoices = self.get_total_invoices()
        self.total_bills = self.get_total_bills()
        # self.calculate_interest()

    def update_sequence(self):
        # seq = self.env['ir.sequence'].search([('code','=','bill.exchange')])
        # next_number = seq.get_next_char(seq.number_next_actual)
        # x = 0
        y = 1
        for bill in self.bill_ids:
            # if bill.bill_number == _('Bill'):
                # bill.bill_number = str(next_number[:seq.padding]) + str(int(next_number[len(next_number)-seq.padding:]) + x).zfill(4)
            if bill.responsable_id == bill.acceptor_id:
                bill.bill_number = 'R' + self.name.split('-')[1] + str(y).zfill(2) + '00'
                y += 1
                # x += 1
        # seq.number_next_actual = seq.number_next_actual + x

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
        # for bill in self.bill_ids:
        #     bill.bill_number = str(next_number[:seq.padding]) + str(int(next_number[len(next_number)-seq.padding:]) + x).zfill(4)
        #     x += 1
        # seq.number_next_actual = seq.number_next_actual + x
        y = 1
        for bill in self.bill_ids:
            # if bill.bill_number == _('Bill'):
                # bill.bill_number = str(next_number[:seq.padding]) + str(int(next_number[len(next_number)-seq.padding:]) + x).zfill(4)
            if bill.responsable_id == bill.acceptor_id:
                bill.bill_number = 'R' + self.name.split('-')[1] + str(y).zfill(2) + '00'
                y += 1

    def open_send_bank_view(self):
        [action] = self.env.ref('jp_account_bills_of_exchange.action_account_send_bank').read()
        ids = self.send_form_ids.ids
        action['domain'] = [('id', 'in', ids)]
        return action

    def debit_note_wizard_lp(self):
        # Agregar un wizard para los gastos administrativos
        return self.env['admin.interest']\
            .with_context(active_ids=self.ids, active_model='account.refinancing.form', active_id=self.id, type='lp')\
            .get_debit_note_data()

    def debit_note_wizard_or(self):
        # Agregar un wizard para los gastos administrativos
        return self.env['admin.interest']\
            .with_context(active_ids=self.ids, active_model='account.refinancing.form', active_id=self.id, type='or')\
            .get_debit_note_data()

class InterestLatePayment(models.Model):
    _name = 'interest.late.payment'
    _description = 'Interest for Late Payment'

    refinancing_form_id = fields.Many2one('account.refinancing.form', string='Refinancing Form')
    document_type = fields.Selection([('bill', 'Bill'),('invoice','Invoice')], string='Document Type')
    document_type_sunat = fields.Many2one('einvoice.catalog.01', string='Sunat Document Type')
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    original_due_date = fields.Date(string='Original Due Date')
    new_due_date = fields.Date(string='New Due Date')
    days = fields.Integer(string='Days')
    refinancing_rate = fields.Float(string='Refinancing Rate', digits=(12, 2))
    currency_id = fields.Many2one('res.currency', string='Currency')
    interest = fields.Monetary(string='Interest', currency_field='currency_id')
    # document_state = fields.Char(string='Document State')

class InterestOnRefinancing(models.Model):
    _name = 'interest.on.refinancing'
    _description = 'Interest On Refinancing'
    
    refinancing_form_id = fields.Many2one('account.refinancing.form', string='Refinancing Form')
    document_type = fields.Selection([('bill', 'Bill'),('invoice','Invoice')], string='Document Type')
    document_type_sunat = fields.Many2one('einvoice.catalog.01', string='Sunat Document Type')
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    original_due_date = fields.Date(string='Original Due Date')
    new_due_date = fields.Date(string='New Due Date')
    days = fields.Integer(string='Days')
    refinancing_rate = fields.Float(string='Refinancing Rate', digits=(12, 2))
    currency_id = fields.Many2one('res.currency', string='Currency')
    interest = fields.Monetary(string='Interest', currency_field='currency_id')
    # document_state = fields.Char(string='Document State')

class InterestAdministrative(models.TransientModel):
    _name = 'admin.interest'
    _description = 'Interest Administrative'

    interest_administrative = fields.Float(string='Interest Administrative', digits=(12, 2))

    def get_debit_note_data(self):
        active_id = self.env.context.get('active_id')
        if not active_id:
            return ''

        return {
            'name': _('Interest Administrative'),
            'res_model': 'admin.interest',
            'view_mode': 'form',
            'view_id': self.env.ref('jp_account_bills_of_exchange.view_admin_interest_wizard').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def create_debit_note_data(self):
        active_id = self.env.context.get('active_id')
        type = self.env.context.get('type')
        ref_form = self.env['account.refinancing.form'].search([('id','=',active_id)])
        if not active_id:
            return ''

        # Creamos la nota de débito con los datos del refinanciamiento
        # Obtener el diario de gastos financieros
        params = self.env['ir.config_parameter'].sudo()
        bank_interests_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.bank_interests_boe_journal_id'))
        journal_id = self.env['account.journal'].search([('id','=',bank_interests_boe_journal_id)])
        type_document = self.env['einvoice.catalog.01'].search([('code','=','08')], limit=1)
        debit_note_type = self.env['einvoice.catalog.10'].search([('code','=','01')], limit=1)
        b = ref_form.overdue_bill_ids[0]
        val = {
            'ref': '',
            'date': ref_form.exchange_date,
            'invoice_date': ref_form.exchange_date,
            # 'journal_id': ref_form.overdue_bill_ids[0].bill_form_id.invoice_ids[0].journal_id.id,
            'type': 'out_invoice',
            'currency_id': ref_form.currency_id.id,
            'partner_id': ref_form.partner_id.id,
            'type_document_id': type_document.id,
            'debit_note_type_id': debit_note_type.id,
            'pe_debit_note_code': debit_note_type.id,
            'glosa': (_('Interest on refinancing form %s') if type == 'lp' else _('Interest on refinancing form %s')) % ref_form.name,
            'invoice_line_ids': [(0, 0,
            {
                'name': _('Interest for late payment') if type == 'lp' else _('Interest on refinancing'),
                'quantity': 1,
                'account_id': journal_id.default_credit_account_id.id,
                'price_unit': sum(line.interest for line in ref_form.interest_lp_ids) if type == 'lp' else sum(line.interest for line in ref_form.interest_or_ids),
                'tax_ids': [(6, 0, [self.env.company.account_sale_tax_id.id])],
            }),(0, 0,  
            {
                'name': _('Interest administrative'),
                'quantity': 1,
                'account_id': journal_id.default_credit_account_id.id,
                'price_unit': self.interest_administrative,
                'tax_ids': [(6, 0, [self.env.company.account_sale_tax_id.id])],
            })]
        }
        account_move = self.env['account.move'].create(val)
        if type == 'lp':
            ref_form.debit_note_lp_id = account_move.id
        else:
            ref_form.debit_note_or_id = account_move.id

        # Cambia las cuentas de las lineas
        for line in account_move.invoice_line_ids:
                line.account_id = journal_id.default_debit_account_id.id,

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
