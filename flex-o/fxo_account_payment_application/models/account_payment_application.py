# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_round
import json


class AccountPaymentApplication(models.Model):
    _name = 'account.payment.application'
    _description = 'Account Payment Application'

    name = fields.Char(string='Referencia', default='/')
    journal_id = fields.Many2one('account.journal', string='Application Journal')
    date = fields.Date(string='Fecha', default=fields.Date.today())
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id)
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    type = fields.Selection([
        ('supplier', 'Compras'),
        ('customer', 'Ventas'),
    ], default='supplier', string='Tipo')
    currency_id = fields.Many2one('res.currency', string='Currency', related='debit_id.currency_id')
    partner_id = fields.Many2one('res.partner', string='Partner')
    debit_id = fields.Many2one('account.move.line', string='Debit')
    # move_ids = fields.Many2many('account.move', 'payment_app_move_rel', string='Move ids')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Aplicado'),
    ], default='draft')
    debit_currency_id = fields.Many2one(string='Debit Currency', readonly=True, related='debit_id.currency_id')
    total_debits = fields.Monetary(string='Total Debitos', currency_field='debit_currency_id')
    total_applied = fields.Monetary(string='Total Aplicado', compute='get_total_inv',
                                    currency_field='debit_currency_id')
    total_net = fields.Monetary(string='Saldo Débito', compute='get_total_net', currency_field='debit_currency_id')
    total_company_currency = fields.Monetary(string='Total en moneda de la Compañía',
                                             currency_field='company_currency_id')
    total_foreign_currency = fields.Float(string='Total en moneda Extranjera')
    application_move = fields.Many2one('account.move', string='Application Move')
    application_lines = fields.One2many('account.payment.application.line', 'application_id', string='Invoices')
    custom_rate = fields.Boolean(string='Custom rate', default=False)
    currency_rate = fields.Float(string='Currency Rate', digits=(12, 4))

    @api.onchange('debit_id')
    def onchange_debit(self):
        for record in self:
            if record.debit_id:
                if record.debit_id.move_id:
                    record.currency_rate = record.debit_id.move_id.currency_rate

    '''
    @api.onchange('date','currency_id')
    def _onchange_date(self):
        # currency_rate = self.env['res.currency.rate'].search([('name','=',self.date),('currency_id','=',self.currency_id.id),('company_id','=',self.company_id.id)],limit=1)
        # TODO revisar con Sixto como obtner tipo de cambio por ahora esta en duro
        currency_rate = self.env['res.currency.rate'].search([('name','=',self.date),('currency_id.name','=','USD'),('company_id','=',self.company_id.id)],limit=1)
        self.currency_rate = currency_rate.sell_rate if currency_rate else 0
    '''

    def get_total_currency(self):
        total_company_currency = total_foreign_currency = 0
        if self.state == 'draft':
            for rec in self:
                for move in self.application_lines:
                    if move.currency_id == self.env.company.currency_id:
                        total_company_currency += move.invoice.amount_residual_signed
                    else:
                        total_foreign_currency += move.invoice.amount_residual
            self.total_company_currency = total_company_currency
            self.total_foreign_currency = total_foreign_currency

    @api.depends('total_debits', 'total_applied')
    def get_total_net(self):
        total_moves = 0
        for rec in self:
            for move in rec.application_lines:
                total_moves += move.application_amount
            rec.total_net = rec.total_debits - abs(total_moves) * (-1 if self.type == 'customer' else 1)

    @api.onchange('debit_id')
    def get_total_debits(self):
        if self.state != 'done':
            if not self.debit_id.currency_id or self.debit_id.currency_id == self.env.company.currency_id:
                self.total_debits = self.debit_id.amount_residual
            else:
                self.total_debits = self.debit_id.amount_residual_currency

    @api.depends('application_lines')
    def get_total_inv(self):
        for rec in self:
            if rec.application_lines:
                total = sum(rec.application_lines.mapped('application_amount'))
            else:
                total = 0
            rec.total_applied = total

    @api.onchange('application_lines', 'debit_id')
    def verify_application_amounts(self):
        total_apply = 0
        app_balance = max_apply = abs(self.total_debits)
        for move in self.application_lines:
            total_apply += move.application_amount
            if total_apply > max_apply and self.type == 'customer':
                move.application_amount = app_balance
            if abs(total_apply) > max_apply and self.type == 'supplier':
                move.application_amount = app_balance
            move.application_balance = app_balance - abs(move.application_amount)
            if move.application_balance < 0:
                move.application_balance = 0
            app_balance -= move.application_amount
        self.get_total_currency()

    def apply_payments(self):
        vals = []
        total = total_payment = 0
        total_max = abs(self.debit_id.amount_residual)
        for move in self.application_lines:
            if self.debit_id.move_id.currency_id != move.currency_id:
                if self.debit_id.move_id.currency_id == self.env.company.currency_id:
                    total_balance = move.total_balance * self.currency_rate
                else:
                    total_balance = move.total_balance / self.currency_rate
            else:
                total_balance = move.total_balance
            # if move.application_amount > total_balance:
            #     raise UserError(_('You can\'t pay more than the balance. %s') % move.name)

        self.application_move = self.env['account.move'].create({
            'name': '/',
            'journal_id': self.journal_id.id,
            'date': self.date,
            'glosa': _('Payment application %s') % self.name,
            'currency_rate': self.currency_rate,
            'type': 'entry',
        })
        # Buscamos las cuentas puente de parametros principales para no duplicar lineas
        # y evitar error con los asientos de apertura
        main_parameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        bridge_accounts = main_parameter.bridge_account_ids
        # for invoice in self.move_ids:
        for line in self.application_lines:
            total_currency = 0
            account = line.invoice.line_ids.filtered(lambda l: l.account_internal_type in (
                'payable', 'receivable') and l.account_id not in bridge_accounts).account_id
            # if self.currency_id == self.company_currency_id:
            if (self.currency_id.id == False or self.currency_id == self.company_currency_id) and line.invoice.currency_id == self.company_currency_id:
                # total_signed = sum(line.invoice.line_ids.filtered(lambda l: l.account_internal_type in ('payable','receivable') and l.account_id not in bridge_accounts).mapped('amount_residual'))
                total_signed = line.application_amount
                total = total_signed
            elif (self.currency_id.id == False or self.currency_id == self.company_currency_id) and line.invoice.currency_id != self.company_currency_id:
                total_currency = float_round(line.application_amount / self.currency_rate, 2)
                # total = float_round(line.application_amount * self.currency_rate, 2)

                total = float_round(line.application_amount, 2)

            else:
                if self.currency_rate == 0 and line.invoice.currency_id != self.company_currency_id:
                    raise UserError(_('Currency rate is 0'))
                # total_currency (line.invoice.line_ids.filtered(lambda l: l.account_internal_type in ('payable','receivable') and l.account_id not in bridge_accounts).mapped('amount_residual_currency'))
                total_currency = line.application_amount if self.currency_id == line.currency_id else 0
                total = float_round(line.application_amount * self.currency_rate, 2)

            if sum(val['credit'] for val in vals) + total > total_max:
                total = total_max - sum(val['credit'] for val in vals)
                if total < 0:
                    total = 0
            if sum(val['debit'] for val in vals) + total > total_max:
                total = total_max - sum(val['debit'] for val in vals)
                if total < 0:
                    total = 0
                # if line.invoice.currency_id != self.company_currency_id and total > 0:
                # 	total_currency = total / self.currency_rate
            if total != 0:
                val = {
                    'move_id': self.application_move.id,
                    'partner_id': self.partner_id.id,
                    'type_document_id': line.invoice.type_document_id.id,
                    'nro_comp': line.invoice.ref,
                    'account_id': account.id,
                    'currency_id': line.invoice.currency_id.id if line.invoice.currency_id != self.company_currency_id else False,
                    'amount_currency': total_currency * (-1 if self.type == 'customer' else 1) if total_currency else 0,
                    'balance': abs(total) * (-1 if self.type == 'customer' else 1),
                    'debit': 0 if self.type == 'customer' else abs(total),
                    'credit': abs(total) if self.type == 'customer' else 0,
                    'tc': self.currency_rate,
                }
                vals.append(val)
        total_payment_currency = ((abs(sum(val['credit' if self.type == 'customer' else 'debit'] for val in vals)) / self.currency_rate) if self.currency_rate > 0 else 0) if self.debit_id.move_id.currency_id != self.env.company.currency_id else 0
        total_payment = abs(sum(val['credit' if self.type == 'customer' else 'debit'] for val in vals))
        val = {
            'move_id': self.application_move.id,
            'partner_id': self.debit_id.partner_id.id,
            'type_document_id': self.debit_id.type_document_id.id,
            'nro_comp': self.debit_id.nro_comp,
            'account_id': self.debit_id.account_id.id,
            'currency_id': self.debit_id.currency_id.id if self.debit_id.currency_id != self.company_currency_id else '',
            'amount_currency': total_payment_currency if total_payment_currency else 0,
            'balance': abs(total_payment) * (1 if self.type == 'customer' else -1),
            'debit': total_payment if self.type == 'customer' else 0,
            'credit': 0 if self.type == 'customer' else total_payment,
            'tc': self.currency_rate,
        }
        vals.append(val)
        self.env['account.move.line'].create(vals)
        self.application_move.post()
        # Conciliamos la linea del debito con el total a aplicar recien creado
        reconcile_lines = self.env['account.move.line']
        reconcile_lines = self.application_move.line_ids.filtered(lambda l: (l.debit if self.type == 'customer' else l.credit) > 0)
        reconcile_lines += self.debit_id
        reconcile_lines.reconcile()
        # Conciliamos las facturas con las lineas creadas
        # for move in self.move_ids:
        for line in self.application_lines:
            reconcile_lines = self.env['account.move.line']
            reconcile_lines += line.invoice.line_ids.filtered(lambda l: not l.reconciled and l.amount_residual != 0 and l.account_id not in bridge_accounts and (l.debit if self.type == 'customer' else l.credit) > 0 and l.nro_comp == line.invoice.ref)
            reconcile_lines += self.application_move.line_ids.filtered(lambda l: (l.credit if self.type == 'customer' else l.debit) > 0 and l.nro_comp == line.invoice.ref)
            reconcile_lines.reconcile()
        self.state = 'done'

    def set_draft(self):
        self.application_lines.invoice.action_remove_move_reconcile()
        self.application_move.button_draft()
        self.application_move.with_context(force_delete=True).unlink()
        self.state = 'draft'

    @api.onchange('type', 'partner_id')
    def get_debit_id_domain(self):
        domain_debit = []
        mp = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        advance_payment_account_id = []
        if self.type == 'customer':
            advance_payment_account_id.append(mp.customer_advance_account_nc.id)
            advance_payment_account_id.append(mp.customer_advance_account_fc.id)
            for account in mp.other_accounts_client.ids:
                advance_payment_account_id.append(account)
        else:
            advance_payment_account_id.append(mp.supplier_advance_account_nc.id)
            advance_payment_account_id.append(mp.supplier_advance_account_fc.id)
            for account in mp.other_accounts_supplier.ids:
                advance_payment_account_id.append(account)
        domain_debit = [
            ('account_id', 'in', advance_payment_account_id),
            '|', ('move_id.state', '=', 'posted'), '&', ('move_id.state', '=', 'draft'),
            ('journal_id.post_at', '=', 'bank_rec'),
            ('reconciled', '=', False), '|', ('amount_residual', '!=', 0.0),
            ('amount_residual_currency', '!=', 0.0),
        ]
        if self.partner_id:
            domain_debit.insert(6, ('partner_id', '=', self.partner_id.id))
        return {
            'domain': {
                'debit_id': domain_debit
            }
        }

    @api.model
    def create(self, vals):
        res = super(AccountPaymentApplication, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('seq_payment_application')
        res.name = seq or '/'
        return res

    def get_wizard(self):
        if self.currency_rate == 0:
            raise UserError(_('Currency rate can\'t be 0'))
        return {
            'name': _('Get Invoices'),
            'res_model': 'get.payment.invoices.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('fxo_account_payment_application.view_get_payment_invoices_wizard').id,
            'context': {'partner_id': ('partner_id', '=', self.partner_id.id) if self.partner_id else (
                'partner_id', '!=', self.partner_id.id)},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class AccountPaymentApplicationLine(models.Model):
    _name = 'account.payment.application.line'
    _description = 'Account Payment Application Line'

    application_id = fields.Many2one('account.payment.application', string='Payment Application')
    invoice = fields.Many2one('account.move', string='Invoice')
    name = fields.Char(string='Name', related='invoice.ref', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', related='invoice.partner_id')
    currency_id = fields.Many2one('res.currency', string='Currency', related='invoice.currency_id', readonly=True)
    total_invoice = fields.Monetary(string='Total Invoice', currency_field='currency_id',
                                    related='invoice.amount_total', readonly=True)
    total_balance = fields.Monetary(string='Total Balance', currency_field='currency_id',
                                    related='invoice.amount_residual', readonly=True)
    currency_rate = fields.Float(string='Currency Rate', digits=(12, 4), related='invoice.currency_rate', readonly=True)
    application_amount = fields.Float(string='Monto Aplicacion')
    application_balance = fields.Float(string='Saldo Aplicacion', readonly=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, related='invoice.state')
