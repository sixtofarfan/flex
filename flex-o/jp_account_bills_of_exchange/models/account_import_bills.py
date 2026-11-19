from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_round

class ImportBillForm(models.Model):
    _name = 'account.import.bill.form'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Import Bill of Exchange Form'

    name = fields.Char('Form number', copy=False, readonly=True, default=(lambda x: _('New')))
    exchange_date = fields.Date('Exchange Date', default=fields.Date.context_today, tracking=True)
    gloss = fields.Char('Gloss', required=True)
    account_move_ids = fields.One2many('account.move', 'import_form_id', 'Account Moves')
    bill_ids = fields.One2many('import.bill.lines', 'import_form_id', 'Import Bills', tracking=True)
    custom_exchange_rate = fields.Boolean(string='Custom Exchange Rate')
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1, tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='State', default='draft', tracking=True)
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.company),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, states={'draft': [('readonly', False)]},string='Currency',default=(lambda self: self.env.user.company_id.currency_id))
    journal_id = fields.Many2one('account.journal', string='Journal for Bills of Exchange')
    bridge_account_id = fields.Many2one('account.account', string='Bridge account')
    type_form = fields.Char(string="Form Type", default='3')
    bank_position = fields.Selection(string='Bank Position', selection=[('collection', 'Collection'), ('discount', 'Discount'), ('guarantee', 'Guarantee'),],)
    portfolio = fields.Boolean(string='Portfolio')
    protest_bills = fields.Boolean(string='Protest bills')
    bill_form_id = fields.Many2one('account.bill.form', string='Bill Form')
    send_form_id = fields.Many2one('account.send.bank', string='Send Form')
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
      string='State', tracking=True,)
    partner_id = fields.Many2one('res.partner', string='Partner')
    closure_rate = fields.Float(string='Clousure Exchange Rate', digits='Exchange Rate', default=1, tracking=True,
        help="""This rate would be used to create the new lines of responsability, 
                that way we can have and exchange diference whenever the bill it's
                payed, protested or renewed"""
    )
    
    @api.onchange('gloss')
    def _onchange_gloss(self):
        if self.bill_form_id.account_move:
            self.bill_form_id.account_move.glosa = self.gloss
        if self.send_form_id.account_move:
            self.send_form_id.account_move.glosa = self.gloss

    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('account.import.bill.form') or _('New')
        self.type_form = '3' if self._context.get('type_import') == '1' else '4'
        return super(ImportBillForm, self).create(values)

    @api.onchange('portfolio')
    def _onchange_portfolio(self):
        if self.portfolio:
            # Obtener el diario y las cuentas desde la configuración
            # print(self._context.get('type_import'))
            # if self._context.get('type_import') == '1':
            #     # Obtener la cuenta de letras de cliente desde la configuración
            #     params = self.env['ir.config_parameter'].sudo()
            #     customer_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.customer_boe_journal_id'))
            # else:
            #     # Obtener la cuenta de letras de cliente desde la configuración
            #     params = self.env['ir.config_parameter'].sudo()
            #     customer_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.supplier_boe_journal_id'))
            # self.journal_id = self.env['account.journal'].search([('id','=',customer_boe_journal_id)])
            self.state_of_bill = 'portfolio'
        # else:
        #     self.journal_id = False

    @api.onchange('protest_bills')
    def _onchange_protest_bills(self):
        if self.protest_bills:
            # # Obtener la cuenta de letras de cliente desde la configuración
            # params = self.env['ir.config_parameter'].sudo()
            # protests_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.protests_boe_journal_id'))
            # self.journal_id = self.env['account.journal'].search([('id','=',protests_boe_journal_id)])
            self.state_of_bill = 'protested'
        # else:
        #     self.journal_id = False

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.bank_position = self.journal_id.bank_position
        self.currency_id = self.journal_id.currency_id if self.journal_id.currency_id else self.env.company.currency_id

    def import_lines(self):
        return self.env['import.lines.wizard']\
            .with_context(active_ids=self.ids, active_model='account.import.bill.form', active_id=self.id)\
            .import_lines()
    
    def clear_lines(self):
        self.bill_ids.unlink()

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
                'url': '/web/binary/download_template_import_bills?model=account.import.bill.form&id=%s'%(self.id),
                'target': 'new',
                }

    def cancel(self):
        if any(x.state_of_bill not in self.state_of_bill for x in self.send_form_id.bill_ids):
            raise UserError(_("You can\'t cancel an import form with bills in different state than the state of importation \'%s\'.") %self.state_of_bill)
        if self.portfolio:
            bill_form = self.bill_form_id
        else:
            bill_form = self.send_form_id
        self.account_move_ids.button_draft()
        self.account_move_ids.with_context(force_delete=True).unlink()
        for bill in bill_form.bill_ids:
            bill.state_of_bill = 'draft'
            bill.unlink()
        bill_form.state = 'draft'
        bill_form.unlink()
        self.state = 'draft'

class ImportBillLines(models.Model):
    _name = 'import.bill.lines'
    _description = 'Import Bill Lines'

    import_form_id = fields.Many2one('account.import.bill.form', string='Import Form')
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
