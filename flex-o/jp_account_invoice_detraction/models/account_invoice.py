from odoo import fields, models, api, _

class AccountInvoice(models.Model):
    _inherit = 'account.move'
    detraction_privisioned = fields.Boolean(string='Is detraction provisioned?', default=False, copy=False)

    def cancel_privisioned_detraction(self):
        payment_ids = self.env['account.payment'].search([('invoice_ids', 'in', self.id)])
        payments = self.env['account.payment']
        payments_to_show = self.env['account.payment']
        for pay in payment_ids:
            if pay.journal_id.type == 'bank':
                if pay.journal_id.bank_account_id.type_of_account == '2':
                    payments += pay
            else:
                payments_to_show += pay

        self.detraction_privisioned = False
        if payments:
            payments.unreconcile()
            payments.action_draft()
            # TODO Copiado de la version 12.0, revisar implicancias
            for rec in payments:
                for move in rec.move_line_ids.mapped('move_id'):
                    if rec.invoice_ids:
                        move.line_ids.remove_move_reconcile()
                    if move.state != 'draft':
                        move.button_cancel()
                    move.unlink()
            payments.cancel()
        return True