from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    # account_move_line_ids = fields.Many2one('account.move.line', string='Account move line ids')
    
    def get_line(self):
        return self.env['get.invoices.lines.wizard'].with_context(active_ids=self.ids, active_model='account.move', active_id=self.id, debit_credit=self.env.context.get('type_line')).get_invoices_lines_wizard()

    def get_lines(self):
        return self.env['get.lines.wizard'].with_context(active_ids=self.ids, active_model='account.move', active_id=self.id, debit_credit=self.env.context.get('type_line')).get_lines_wizard()

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        for rec in self:
            for line in rec.line_ids:
                if line.account_line_id:
                    line.date = line.account_line_id.date
        return res

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    account_line_id = fields.Many2one('account.move.line', string='Account line', copy=False)
    account_line_realted_id = fields.One2many('account.move.line', 'account_line_id', string='Account line related')

    @api.onchange('account_line_id')
    def _onchange_account_line_id(self):
        self.type_document_id = self.account_line_id.type_document_id
        self.nro_comp = self.account_line_id.nro_comp
        self.import_number = self.account_line_id.import_number
        self.date = self.account_line_id.date
        if not self.move_id.is_invoice(include_receipts=True):
            self.partner_id = self.account_line_id.partner_id
            self.name = self.account_line_id.name
            self.account_id = self.account_line_id.account_id
            self.currency_id = self.account_line_id.currency_id
            if self.currency_id:
                self.amount_currency = self.account_line_id.amount_currency #* (-1 if self.account_line_id.credit > 0 else 1)
            else:
                self.debit = self.account_line_id.debit
                self.credit = self.account_line_id.credit
        # self.tc = self.move_id.currency_rate,
        # self.debit = self.account_line_id.amount_total * self.move_id.currency_rate if self.account_line_id.debit > 0 else 0,#(sum(self.account_line_id.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).mapped('debit')) if self.account_line_id.type in ('in_invoice','in_refund') else sum(self.account_line_id.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).mapped('credit'))) if debit_credit == 'debit' else 0,
        # self.credit = self.account_line_id.amount_total * self.move_id.currency_rate if self.account_line_id.credit > 0 else 0,#(sum(invoice.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).mapped('credit')) if invoice.type in ('out_invoice','out_refund') else sum(invoice.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).mapped('debit'))) if debit_credit == 'credit' else 0,
				