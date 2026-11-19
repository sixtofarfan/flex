from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from datetime import datetime, timedelta, date
from odoo.tools import float_round

class AdvancedBillForm(models.Model):
    _name = 'account.advanced.bill.form'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Advanced Bill of Exchange Form'
    _order = 'exchange_date desc, name desc, id desc'

    name = fields.Char('Form number', copy=False, readonly=True, default=(lambda x: _('New')))
    exchange_date = fields.Date('Exchange Date', default=fields.Date.context_today, tracking=True)
    gloss = fields.Char('Gloss', required=True)
    bill_ids = fields.One2many('advanced.bill.lines', 'advanced_form_id', 'Bills', tracking=True)
    custom_exchange_rate = fields.Boolean(string='Custom Exchange Rate')
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1, tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='State', default='draft', tracking=True)
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.company),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, states={'draft': [('readonly', False)]},string='Currency',default=(lambda self: self.env.user.company_id.currency_id))
    journal_id = fields.Many2one('account.journal', string='Journal for Bills of Exchange')
    bridge_account_id = fields.Many2one('account.account', string='Destination account')
    type_form = fields.Char(string="Form Type", default='3')
    # bank_position = fields.Selection(string='Bank Position', selection=[('collection', 'Collection'), ('discount', 'Discount'), ('guarantee', 'Guarantee'),],)
    # portfolio = fields.Boolean(string='Portfolio')
    # protest_bills = fields.Boolean(string='Protest bills')
    bill_form_id = fields.Many2one('account.bill.form', string='Bill Form')
    # send_form_id = fields.Many2one('account.send.bank', string='Send Form')
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
      string='State', tracking=True, default='portfolio')
    partner_id = fields.Many2one('res.partner', string='Partner')
    bills_qty = fields.Integer('Bills quantity', default=1)
    days_due_first = fields.Integer('Expiration days of 1st Bill', default=15)
    range_bill = fields.Integer('Range of days between bills', default=15)
    guarantee_id = fields.Many2one('res.partner', string='Guarantee')
    acceptor_id = fields.Many2one('res.partner', string='Acceptor')
    creditor_id = fields.Many2one(comodel_name='res.partner', string='Creditor')
    advanced_amount = fields.Monetary(string='Advanced Amount', currency_field='currency_id', default=0)
    retention_percentage = fields.Float(string='Retention percentage (%)', tracking=True)
    apply_retention = fields.Boolean(string='Apply retentions')
    total_retention = fields.Monetary('Total retencion', currency_field='currency_id', default=0)
    total_retention_signed = fields.Monetary('Total retencion Signed', currency_field='company_currency_id', default=0)
    import_number = fields.Char(string='Import N°', copy=False)

    @api.onchange('gloss')
    def _onchange_gloss(self):
        if self.bill_form_id.account_move:
            self.bill_form_id.account_move.glosa = self.gloss

    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('account.advanced.bill.form') or _('New')
        values.update({'type_form': '3' if self._context.get('type_import') == '1' else '4'})
        return super(AdvancedBillForm, self).create(values)
        
    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.bank_position = self.journal_id.bank_position
        self.currency_id = self.journal_id.currency_id if self.journal_id.currency_id else self.env.company.currency_id

    @api.onchange('currency_id','exchange_date','custom_exchange_rate')
    def onchange_currency_id(self):
        if self.currency_id and self.currency_id != self.env.user.company_id.currency_id:
            rates = self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id),('name','=',self.exchange_date or fields.Date.context_today)])
            if not rates:
                rates = self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id)], order='name desc', limit=1)
        if not self.custom_exchange_rate:
            if self.currency_id.id == self.company_currency_id.id:
                self.exchange_rate = 1
            else:
                self.exchange_rate = self.currency_id._convert(1, self.company_id.currency_id, self.company_id, self.exchange_date or fields.Date.context_today, False)
        self.onchange_retention()
        for bill in self.bill_ids:
            bill.exchange_rate = self.exchange_rate

    @api.onchange('apply_retention','retention_percentage','total_invoices')
    def onchange_retention(self):
        self.set_total_retention()
    
    def set_total_retention(self):
        if self.apply_retention:
            if self.advanced_amount <= 0:
                raise UserError(_('The amount shoul not be 0 or less to apply retention'))
            self.total_retention = self.advanced_amount * (self.retention_percentage / 100)
            self.total_retention_signed = self.advanced_amount  * self.exchange_rate * (self.retention_percentage / 100)
            # self.total_bills = self.total_bills - self.total_retention
        else:
            self.total_retention = 0

    def import_lines(self):
        return self.env['import.lines.wizard']\
            .with_context(active_ids=self.ids, active_model='account.advanced.bill.form', active_id=self.id)\
            .import_lines()
    
    def clear_lines(self):
        self.bill_ids.unlink()

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
            'invoice_date': self.exchange_date,
            'journal_id': self.journal_id.id,
            'glosa': self.gloss,
            'type': 'bill',
            'currency_rate': self.exchange_rate,
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
            if line.creditor_id:
                if self._context.get('type_import') == '1':
                    creditor_id = self.env.company.partner_id
                else:
                    creditor_id = self.env['res.partner'].search([('name', '=', line.creditor_id)])
                if not creditor_id:
                    msg += 'The creditor partner ' + line.creditor_id + ' doesn\'t exist in the database\n'
            else:
                if self._context.get('type_import') != '1':
                    msg += 'The creditor partner doesn\'t exist in the database\n'
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
                    ('creditor_id', '=', creditor_id.id),\
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
                'creditor_id': creditor_id.id if not self.partner_id else self.partner_id.id if self.partner_id else self.env.company.partner_id.id,
                'guarantee_id': guarantee_id.id if line.guarantee_id else False,
                'bill_date_issue': line.bill_date_issue,
                'bill_date_due': line.bill_date_due,
                'bill_currency_id': self.currency_id.id,
                'bill_amount_total': line.bill_amount_total,
                'exchange_rate': line.exchange_rate,
                'bill_amount_total_signed': line.bill_amount_total_signed,
                'state_of_bill': 'portfolio' if self._context.get('type_import') == '1' else 'accepted',
                'type_bill': 'receivable' if self._context.get('type_import') == '1' else 'payable',
                'is_advanced_payment': True,
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
                'partner_id': acceptor_id.id if self._context.get('type_import') == '1' else self.partner_id.id,
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
        advanced_amount_signed = float_round(self.advanced_amount * self.exchange_rate, 2)
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','00')])
        val = {
            'bill_form_id': form_id.id,
            'ref': self.import_number,
            'move_id': account_move_id.id,
            'partner_id': self.partner_id.id,
            'type_document_id': type_document_id.id,
            'nro_comp': self.import_number, # self.name + (_(' Import N° ') + self.import_number if self.import_number else ''),#line.bill_number,
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
            total_amount_currency = sum(item['debit'] if self._context.get('type_import') == '1' else item['credit'] for item in vals_aml)
            total_debit = sum(item['amount_currency'] if item['credit'] else 0 for item in vals_aml) if self._context.get('type_import') == '1' else sum(item['amount_currency'] if item['debit'] else 0 for item in vals_aml)
            difference = abs(total_amount_currency) - abs(float_round(total_debit * self.exchange_rate, 2))

            for i in range(8,1,-1):
                difference = round(difference,i)

            if float_round(difference,2) < 0:
                # Asiento de diferencia por redondeo ganancia
                print(self._context.get('type_import'))
                val = {
                    'partner_id': self.partner_id.id,
                    'type_document_id': type_document_id.id,
                    'nro_comp': self.import_number,
                    'bill_form_id': form_id.id,
                    'name': _('Currency round difference'),
                    'debit': 0,#float_round(abs(difference),2) if self._context.get('type_import') == '1' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'credit': float_round(abs(difference),2),#0.0 if self._context.get('type_import') == '1' else float_round(abs(difference),2), #if self.invoice_ids[0].type == 'out_invoice' else float_round(abs(total_debit - total_credit),2),
                    'account_id': round_journal.default_credit_account_id.id,# if self._context.get('type_import') == '1' else round_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                    'move_id': account_move_id.id,
                    # 'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                    # 'amount_currency': float_round(abs(difference) / self.exchange_rate,2) * -1 if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    'balance': float_round(abs(difference),2) * -1, # if self.company_currency_id.id != self.currency_id.id else 0.00, #* (1.0 if self.invoice_ids[0].type == 'out_invoice' else -1.0) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    'date_maturity': self.exchange_date,
                    }
                vals_aml.append(val)
            if float_round(difference,2) > 0:
                # Asiento de diferencia por redondeo perdida
                val = {
                    'partner_id': self.partner_id.id,
                    'type_document_id': type_document_id.id,
                    'nro_comp': self.import_number,
                    'bill_form_id': form_id.id,
                    'name': _('Currency round difference'),
                    'debit': abs(float_round(difference,2)),#0.0 if self._context.get('type_import') == '1' else abs(float_round(difference,2)), #if self.invoice_ids[0].type == 'out_invoice' else abs(float_round(total_debit - total_credit,2)),
                    'credit': 0, #abs(float_round(difference,2)) if self._context.get('type_import') == '1' else 0, #if self.invoice_ids[0].type == 'out_invoice' else 0.0,
                    'account_id': round_journal.default_debit_account_id.id,# if self._context.get('type_import') == '1' else round_journal.default_credit_account_id.id, #if self.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                    'move_id': account_move_id.id, 
                    # 'currency_id': self.currency_id.id if self.company_currency_id.id != self.currency_id.id else False,
                    # 'amount_currency': float_round(abs(difference) / self.exchange_rate,2) if self.company_currency_id.id != self.currency_id.id else 0.00,
                    'balance': float_round(abs(difference),2), # if self.company_currency_id.id != self.currency_id.id else 0.00,
                    'date_maturity': self.exchange_date,
                    }
                vals_aml.append(val)
        self.env['account.move.line'].create(vals_aml)
        # Forzamos la fecha de las lineas de la letra
        # TODO al crear el asiento se cambia la fecha de la linea
        # por la fecha del asiento
        for line in account_move_id.line_ids:
            for bill in self.bill_ids:
                if line.name == bill.bill_number:
                    line.date = bill.bill_date_issue
        account_move_id.post()
        for line in account_move_id.line_ids:
            line.amount_residual = line.balance
            line.amount_residual_currency = line.amount_currency
        bill_ids = self.env['account.bill'].create(vals)
        self.bill_form_id.bill_ids = [(6,0, bill_ids.ids)]
        self.state = 'done'

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
        # self.update_form()
        if self.advanced_amount:
            # Obtener el tipo de cambio para la fecha de intercambio de letras
            self.onchange_currency_id()
            if self.advanced_amount > 0:
                bill_date_due = datetime.strptime(str(self.exchange_date), '%Y-%m-%d') + timedelta(days=(self.days_due_first))  
                # Cambia la fecha para evitar sabados, domingos y feriados.
                bill_date_due_changed = self.change_bill_date(bill_date_due)
                advanced_amount = self.advanced_amount - self.total_retention
                bill_amount = float_round((self.advanced_amount - self.total_retention) / self.bills_qty,2)
                bill_amount_signed = float_round(bill_amount * self.exchange_rate,3)
                aux = bill_amount
                result = []
                result.append((0, 0,
                {'bill_date_due':bill_date_due_changed,
                'bill_date_issue':self.exchange_date,
                # 'responsable_id':self.partner_id.name,
                'guarantee_id':self.guarantee_id.name,
                # 'acceptor_id':self.acceptor_id.name if self.acceptor_id else self.partner_id.name,
                'responsable_id': self.partner_id.name if self._context.get('type_import') == '1' else self.env.company.partner_id.name,
                'acceptor_id': (self.acceptor_id.name if self.acceptor_id else self.partner_id.name) if self._context.get('type_import') == '1' else self.env.company.partner_id.name,
                'creditor_id': (self.creditor_id.name if self.creditor_id else self.partner_id.name) if self._context.get('type_import') == '1' else self.env.company.partner_id.name,
                'bill_currency_id':self.currency_id.name,
                'bill_amount_total':bill_amount,
                'bill_amount_total_signed':bill_amount_signed,
                'exchange_rate':self.exchange_rate,
                'account_id': self.journal_id.default_debit_account_id.code, # if self._context.get('type_import') == '1' else self.journal_id.default_credit_account_id.code,
                'type_bill': 'receivable' if self._context.get('type_import') == '1' else 'payable',}))
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
                    bill_amount_signed = float_round(bill_amount * self.exchange_rate,3)
                    result.append((0, 0,
                    {'bill_date_due':bill_date_due_changed,
                    'bill_date_issue':self.exchange_date,
                    # 'responsable_id':self.partner_id.name,
                    'guarantee_id':self.guarantee_id.name,
                    # 'acceptor_id':self.acceptor_id.name if self.acceptor_id else self.partner_id.name,
                    'responsable_id': self.partner_id.name if self._context.get('type_import') == '1' else self.env.company.partner_id.name,
                    'acceptor_id': (self.acceptor_id.name if self.acceptor_id else self.partner_id.name) if self._context.get('type_import') == '1' else self.env.company.partner_id.name,
                    'bill_currency_id':self.currency_id.name,
                    'bill_amount_total':bill_amount,
                    'bill_amount_total_signed':bill_amount_signed,
                    'exchange_rate':self.exchange_rate,
                    'account_id':self.journal_id.default_debit_account_id.code, # if self._context.get('type_import') == '1' else self.journal_id.default_credit_account_id.code,
                    'type_bill': 'receivable' if self._context.get('type_import') == '1' else 'payable',}))

                self.bill_ids = result
            self.update_sequence_final()

    def update_sequence_final(self):
        y = 1
        for bill in self.bill_ids:
            bill.bill_number = 'A' + self.name.split('-')[1] + '-' + str(y).zfill(2) + '-00'
            y += 1

    def download_template(self):
        return {
                'type' : 'ir.actions.act_url',
                'url': '/web/binary/download_template_import_bills?model=account.advanced.bill.form&id=%s'%(self.id),
                'target': 'new',
                }

    def cancel(self):
        if any(l.matched_credit_ids or l.matched_debit_ids for l in self.bill_form_id.account_move_line_ids):
            raise UserError(_('This account move have partial or full reconciled lines. Please broke conciliations before cancel this form.'))
        for l in self.bill_form_id.bill_ids:
            print(l.state_of_bill)
        if self._context.get('type_import') == '1':
            if any(x.state_of_bill != 'portfolio' for x in self.bill_form_id.bill_ids):
                raise UserError(_("You can\'t cancel an advanced form with bills in different state than the state portfolio."))
        else:
            if any(x.state_of_bill != 'accepted' for x in self.bill_form_id.bill_ids):
                raise UserError(_("You can\'t cancel an advanced form with bills in different state than the state accepted."))
        bill_form = self.bill_form_id
        bill_form.account_move.button_draft()
        bill_form.account_move.with_context(force_delete=True).unlink()
        for bill in bill_form.bill_ids:
            bill.state_of_bill = 'draft'
            bill.unlink()
        bill_form.state = 'draft'
        bill_form.unlink()
        self.state = 'draft'

class AdvancedBillLines(models.Model):
    _name = 'advanced.bill.lines'
    _description = 'Advanced Bill Lines'

    advanced_form_id = fields.Many2one('account.advanced.bill.form', string='Advanced Bill Form')
    bill_number = fields.Char('Bill Number')
    bank_number = fields.Char('Unique Number')
    account_id = fields.Char(string='Account')
    responsable_id = fields.Char(string='Responsable')
    acceptor_id = fields.Char(string='Acceptor')
    creditor_id = fields.Char(string='Creditor')
    guarantee_id = fields.Char(string='Guarantee')
    bill_date_issue = fields.Date(string='Issue date')
    bill_date_due = fields.Date(string='Due date')
    bill_currency_id = fields.Char(string='Currency')
    bill_amount_total = fields.Float(string='Amount', digits=(12, 2))
    exchange_rate = fields.Float(string='Exchange rate', digits=(12, 4))
    bill_amount_total_signed = fields.Float(string='Amount Signed', digits=(12, 2))
    state_of_bill = fields.Char('State')
    type_bill = fields.Char('Type')

    @api.onchange('bill_amount_total','exchange_rate')
    def onchange_bill_amount_total(self):
        if self.bill_currency_id != self.env.company.currency_id.name:
            self.bill_amount_total_signed = self.bill_amount_total * self.exchange_rate
        else:
            self.bill_amount_total_signed = self.bill_amount_total