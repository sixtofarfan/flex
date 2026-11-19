from odoo import models, fields, api, _
from odoo.exceptions import  UserError
from odoo.tools import float_round

class AccountBillPartialPayment(models.Model):
    _name = 'account.bill.partial.payment'
    _description = 'Partial payment'


    name = fields.Char(string='Name')
    payment_date = fields.Date(string='Payment Date', required = True)
    bill_id = fields.Many2one('account.bill', string='Bill of exchange')
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.company),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency')
    bill_currency_id = fields.Many2one(comodel_name='res.currency', string='Bill Currency', related='bill_id.bill_currency_id')
    journal_id = fields.Many2one('account.journal', string='Journal payment')
    operation_number = fields.Char(string='Operation number')
    payment_amount = fields.Monetary(string='Payment Amount', currency_field='currency_id', default=0)
    payment_amount_signed = fields.Monetary(string='Payment Amount Signed', currency_field='bill_currency_id', default=0)
    account_move = fields.Many2one('account.move', 'Account Move')
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1)
    
    def unlink(self):
        if self.account_move:
            self.account_move.button_draft()
            self.account_move.with_context(force_delete=True).unlink()
        res = super(AccountBillPartialPayment, self).unlink()
        return res

    def create_move(self, bill):
        vals = []
        val = {}
        payment_date = self.env.context.get('payment_date')
        payment_journal_id = self.env.context.get('payment_journal')
        payment_currency_id = self.env.context.get('payment_currency_id')
        payment_amount = self.env.context.get('payment_amount')
        exchange_rate = self.env.context.get('exchange_rate') if self.env.context.get('exchange_rate') else round(self.get_rates(payment_date), 3)
        operation_number = self.env.context.get('operation_number')
        add_credit_note = self.env.context.get('add_credit_note')
        if self.bill_currency_id != payment_currency_id:
            if payment_currency_id == self.env.company.currency_id:
                payment_amount_signed = float_round(payment_amount / exchange_rate, 2)
            else:
                payment_amount_signed = float_round(payment_amount * exchange_rate, 2)
        else:
            payment_amount_signed = payment_amount
        val = {
            'name': self.env['ir.sequence'].next_by_code('account.protest.payment'),#'PP-' + bill.name,
            'currency_id': bill.bill_currency_id.id,
            'currency_rate': exchange_rate,
            'date': payment_date,
            # 'invoice_date': payment_date,
            'invoice_date': bill.bill_date_issue,
            'journal_id': bill.bill_form_id.journal_id.id if bill.bill_form_id else bill.origin_bill_id.bill_form_id.journal_id.id if bill.origin_bill_id and bill.origin_bill_id.bill_form_id else bill.origin_bill_id.send_form_id.journal_id.id if bill.origin_bill_id.send_form_id else bill.send_form_id.journal_id.id,
            'glosa': _('Protest payment bill %s') %bill.bill_number,
            'type': 'bill',
        }
        protest_payment_account_move = self.env['account.move'].create(val)
        # Crear asientos desde el protesto
        # Asiento de pago de cliente
        # Verificamos primero si la letra no ha sido importada
        if bill.account_move_line_ids:
            item = bill.account_move_line_ids[0]
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
                'ref': 'Imported protested bill',
                'name': 'Protest payment',
                'account_id': bill.account_id.id,
                'journal_id': protest_journal.id,
                'currency_id': bill.bill_currency_id.id,
                'company_id': bill.company_id.id,
                'company_currency_id': bill.company_currency_id.id,
                'exchange_rate': bill.exchange_rate,
                'amount_currency': bill.bill_amount_total * -1 if bill.bill_currency_id != bill.company_currency_id else 0,
                'debit': 0,
                'credit': bill.bill_amount_total_signed,
                'balance': bill.bill_amount_total_signed * -1,
                'date_maturity': bill.bill_date_due,
                'tc': exchange_rate,
            }
            vals.append(val)
            val = {
                'move_id': protest_payment_account_move.id,
                'ref': 'Imported protested bill',
                'name': 'Protest payment',
                'account_id': bill.account_id.id,
                'journal_id': protest_journal.id,
                'currency_id': bill.bill_currency_id.id,
                'company_id': bill.company_id.id,
                'company_currency_id': bill.company_currency_id.id,
                'exchange_rate': bill.exchange_rate,
                'amount_currency': bill.bill_amount_total if bill.bill_currency_id != bill.company_currency_id else 0,
                'debit': bill.bill_amount_total_signed,
                'credit': 0,
                'balance': bill.bill_amount_total_signed,
                'date_maturity': bill.bill_date_due,
                'tc': exchange_rate,
            }
            vals.append(val)
            items = self.env['account.move.line'].create(vals)
            item = items[0]
            vals =[]
        # cc_payment_amount = 0
        # if add_credit_note and bill.protest_debit_note_id.currency_id == payment_currency_id:
        #     if payment_currency_id != bill.company_currency_id:
        #         cc_payment_amount = bill.protest_debit_note_id.amount_residual
        #     else:
        #         cc_payment_amount = bill.protest_debit_note_id.amount_residual
        # else:
        #     cc_payment_amount = bill.protest_debit_note_id.amount_residual
        if bill.bill_currency_id != payment_currency_id:
            if payment_currency_id != bill.company_currency_id: 
                total_amount = payment_amount * exchange_rate
            else:
                total_amount = payment_amount / exchange_rate
        else:
            total_amount = payment_amount
        total_amount_signed = round(total_amount * exchange_rate,2) if bill.company_currency_id != payment_currency_id else payment_amount
        # Obtener el id de Otros documentos en la tabla sunat de tipos de comprobante
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','00')])
        # Si la letra esta en descuento colocamos la responsabilidad en lugar de 
        # la cuenta del banco cuando es un protesto o cartera
        if bill.state_of_bill == 'protested':
            account_id = payment_journal_id.default_debit_account_id
        elif bill.state_of_bill == 'disbursed':
            account_id = bill.send_form_id.journal_id.default_credit_account_id
        else:
            account_id = payment_journal_id.default_debit_account_id
        val = {
            'ref': item.ref,
            'protest_payment_id': bill.protest_payment_id.id,
            'partner_id': bill.responsable_id.id,
            # 'type_document_id': type_document_id.id,
            # 'nro_comp': operation_number,
            'move_id': protest_payment_account_move.id,
            'exchange_rate': exchange_rate,
            'name': _('Customer payment for bill ') + bill.name, #item.name if item.name[:20] != _('Bank charge for bill') else _('Customer payment for bill ') + bill.name,
            'date': payment_date,
            'journal_id': item.journal_id.id ,
            'currency_id': item.currency_id.id,
            'company_id': item.company_id.id,
            'company_currency_id': item.company_currency_id.id,
            'account_id': account_id.id,
            'amount_currency': total_amount * (1 if bill.type_bill == 'receivable' else -1) if bill.company_currency_id != payment_currency_id else 0, #item.amount_currency * -1.0,
            'tc': exchange_rate,
            'balance': total_amount_signed * (1 if bill.type_bill == 'receivable' else -1), #item.balance * -1.0,
            'debit': abs(total_amount_signed) if bill.type_bill == 'receivable' else 0, #item.credit if bill.type_bill == 'receivable' else 0,
            'credit': 0 if bill.type_bill == 'receivable' else abs(total_amount_signed), #0 if bill.type_bill == 'receivable' else item.credit,
            'date_maturity': item.date_maturity,
        }
        vals.append(val)
        # Si el campo add_credit_note es verdadero se agrega la nota de debito del protesto
        # al pago parcial
        if add_credit_note:
            val = {
                'ref': item.ref,
                'protest_payment_id': bill.protest_payment_id.id,
                'partner_id': bill.protest_debit_note_id.partner_id.id,
                'type_document_id': bill.protest_debit_note_id.type_document_id.id,
                'nro_comp': bill.protest_debit_note_id.ref,
                'move_id': protest_payment_account_move.id,
                'exchange_rate': exchange_rate,
                'name': _('Debit note payment ') + bill.protest_debit_note_id.ref, #item.name if item.name[:20] != _('Bank charge for bill') else _('Customer payment for bill ') + bill.name,
                'date': bill.protest_debit_note_id.invoice_date,
                'journal_id': item.journal_id.id ,
                'currency_id': item.currency_id.id,
                'company_id': item.company_id.id,
                'company_currency_id': item.company_currency_id.id,
                'account_id': bill.protest_debit_note_id.line_ids.filtered(lambda l: l.account_internal_type == 'receivable').account_id.id,
                'amount_currency': bill.protest_debit_note_id.amount_residual * (1 if bill.type_bill != 'receivable' else -1) if bill.company_currency_id != bill.protest_debit_note_id.currency_id else 0, #item.amount_currency * -1.0,
                'tc': exchange_rate,
                'balance': bill.protest_debit_note_id.amount_residual_signed * (1 if bill.type_bill != 'receivable' else -1), #item.balance * -1.0,
                'debit': abs(bill.protest_debit_note_id.amount_residual_signed) if bill.type_bill != 'receivable' else 0, #item.credit if bill.type_bill != 'receivable' else 0,
                'credit': 0 if bill.type_bill != 'receivable' else abs(bill.protest_debit_note_id.amount_residual_signed), #0 if bill.type_bill != 'receivable' else item.credit,
                'date_maturity': bill.protest_debit_note_id.invoice_date_due,
            }
            vals.append(val)
        # Asiento de salida de letra
        if bill.account_move_line_ids:
            item = bill.account_move_line_ids.filtered(lambda l: l.account_internal_type in ('receivable', 'payable') and l.debit > 0 and l.reconciled)
        # print(round((payment_amount_signed - bill.protest_debit_note_id.amount_residual if add_credit_note else 0) if abs(item.amount_currency) else item.debit, 2))
        # print(round((payment_amount_signed - bill.protest_debit_note_id.amount_residual if add_credit_note else 0) ,2), abs(item.amount_currency) , item.debit)
        total_amount = round(((payment_amount_signed - bill.protest_debit_note_id.amount_residual) if add_credit_note else payment_amount_signed) if abs(item.amount_currency) else item.debit, 2)
        # total_amount_signed = round(total_amount * item.tc,2) if bill.bill_currency_id != bill.env.company.currency_id else bill.bill_amount_total
        total_amount_signed = round(total_amount * exchange_rate, 2) if bill.bill_currency_id != bill.env.company.currency_id else payment_amount#bill.bill_amount_total
        val = {
            'ref': item.ref,
            'protest_payment_id': bill.protest_payment_id.id,
            'partner_id': bill.responsable_id.id,
            'type_document_id': type_document_id.id,
            'nro_comp': bill.bill_number,
            'move_id': protest_payment_account_move.id,
            'exchange_rate': exchange_rate, #item.tc,
            'name': bill.name, #item.name if item.name[:20] != _('Bank Responsabillity') else bill.name,
            'date': payment_date,
            'journal_id': item.journal_id.id,
            'currency_id': item.currency_id.id,
            'company_id': item.company_id.id,
            'company_currency_id': item.company_currency_id.id,
            'account_id': bill.account_id.id, #item.account_id.id if item.name[:20] != _('Bank Responsabillity') else bill.account_id.id,
            'amount_currency': total_amount * (-1 if bill.type_bill == 'receivable' else 1) if item.amount_currency else 0,
            'tc': exchange_rate, #item.tc,
            'balance': total_amount_signed * (-1 if bill.type_bill == 'receivable' else 1),
            'debit': 0 if bill.type_bill == 'receivable' else total_amount_signed,
            'credit': total_amount_signed if bill.type_bill == 'receivable' else 0,
            'date_maturity': item.date_maturity,
        }
        vals.append(val)
        # Diferencia de cambio
        # Obtener el diario y las cuentas de diferencia de cambio desde la configuración
        exchange_journal = bill.env.company.currency_exchange_journal_id
        total_credit = round(sum(item['credit'] for item in vals),2)
        total_debit = round(sum(item['debit'] for item in vals),2)
        if total_credit > total_debit:
            # Asiento de diferencia de cambio por ganancia
            val = {
                'name': _('Currency exchange rate difference'),
                'protest_payment_id': bill.protest_payment_id.id,
                # 'exchange_rate': exchange_rate,
                'debit': round(abs(total_debit - total_credit),2), # if bill.type_bill == 'receivable' else 0, #if bill.invoice_ids[0].type == 'out_invoice' else 0.0,
                'credit': 0.0, # if bill.type_bill == 'receivable' else round(abs(total_debit - total_credit),2), #if bill.invoice_ids[0].type == 'out_invoice' else round(abs(total_debit - total_credit),2),
                'account_id': exchange_journal.default_debit_account_id.id, #if bill.invoice_ids[0].type == 'out_invoice' else  exchange_journal.default_credit_account_id.id,
                'move_id': protest_payment_account_move.id,
                'currency_id': bill.bill_currency_id.id if bill.company_currency_id.id != bill.bill_currency_id.id else False,
                # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                # 'amount_currency': round(abs(total_debit - total_credit) / exchange_rate,2) * (1.0 if bill.type_bill == 'receivable' else -1.0) if bill.company_currency_id.id != bill.bill_currency_id.id else 0.00, #* (1.0 if bill.invoice_ids[0].type == 'out_invoice' else -1.0) if bill.company_currency_id.id != bill.currency_id.id else 0.00,
                # 'tc': exchange_rate,
                'balance': round(abs(total_debit - total_credit),2) * (1.0 if bill.type_bill == 'receivable' else -1.0), # if bill.company_currency_id.id != bill.bill_currency_id.id else 0.00, #* (1.0 if bill.invoice_ids[0].type == 'out_invoice' else -1.0) if bill.company_currency_id.id != bill.currency_id.id else 0.00,
                }
            vals.append(val)
        if total_credit < total_debit:
            # Asiento de diferencia de cambio por perdida
            val = {
                'name': _('Currency exchange rate difference'),
                'protest_payment_id': bill.protest_payment_id.id,
                # 'exchange_rate': exchange_rate,
                'debit': 0.0, # if bill.type_bill == 'receivable' else abs(round(total_debit - total_credit,2)), #if bill.invoice_ids[0].type == 'out_invoice' else abs(round(total_debit - total_credit,2)),
                'credit': abs(round(total_debit - total_credit,2)), # if bill.type_bill == 'receivable' else 0, #if bill.invoice_ids[0].type == 'out_invoice' else 0.0,
                'account_id': exchange_journal.default_credit_account_id.id, #if bill.invoice_ids[0].type == 'out_invoice' else exchange_journal.default_debit_account_id.id,
                'move_id': protest_payment_account_move.id,
                'currency_id': bill.bill_currency_id.id if bill.company_currency_id.id != bill.bill_currency_id.id else False,
                # A pedido de contabilidad de polimaster no mostrar el monto en dolares en la diferencia de cambio
                # 'amount_currency': round(abs(total_debit - total_credit) / exchange_rate,2) * (-1 if bill.type_bill == 'receivable' else 1) if bill.company_currency_id.id != bill.bill_currency_id.id else 0.00,
                # 'tc': exchange_rate,
                'balance': round(abs(total_debit - total_credit),2) * (-1 if bill.type_bill == 'receivable' else 1),
                }
            vals.append(val)
        # Si la letra ha sido importada borramos la linea, el objeto creado item
        if not bill.account_move_line_ids:
            items.unlink()
        self.env['account.move.line'].create(vals)
        protest_payment_account_move.post()
        self.account_move = protest_payment_account_move
        # Reconciliar asientos
        if bill.account_move_line_ids:
            for line in bill.account_move_line_ids:
                if line.account_id.reconcile and not line.reconciled:
                    lines = line
                    filtered = self.account_move.line_ids.filtered(lambda l: l.account_id == lines[0].account_id and\
                        not l.reconciled and\
                        l.name == line.name or l.name == line.name[:7])
                    if filtered:
                        lines += filtered[0]
                        break
            lines.reconcile()
        else:
            if bill.send_form_id:
                lines = bill.send_form_id.account_move_line_ids.filtered(lambda l: l.account_id == bill.account_id and\
                    not l.reconciled and\
                    l.name == bill.bill_number or l.name == bill.bill_number[:7])
            else:
                lines = bill.bill_form_id.account_move_line_ids.filtered(lambda l: l.account_id == bill.account_id and\
                    not l.reconciled and\
                    l.name == bill.bill_number or l.name == bill.bill_number[:7])
            # for line in bill.send_form_id.account_move_line_ids:
            #     # Si es una letra importada
            #     if line.account_id.reconcile and not line.reconciled:
            #         lines = line
            filtered = self.account_move.line_ids.filtered(lambda l: l.account_id == bill.account_id and\
                not l.reconciled and\
                l.name == bill.bill_number or l.name == bill.bill_number[:7])
            if filtered:
                lines += filtered[0]
                        # break
            lines.reconcile()
        if add_credit_note:
            line1 = bill.protest_debit_note_id.line_ids.filtered(lambda l: l.account_internal_type == 'receivable')
            line2 = protest_payment_account_move.line_ids.filtered(lambda l: l.name == _('Debit note payment ') + bill.protest_debit_note_id.ref)
            lines = line1 + line2
            lines.reconcile()
        # Conciliar la responsabilidad si el pago es una letra en descuento.
        if bill.send_form_id:
            if bill.send_form_id.bank_disbursement_id:
                lines = bill.send_form_id.bank_disbursement_id.account_move_line_ids.filtered(lambda l: l.account_id == account_id and\
                    not l.reconciled and\
                    bill.bill_number in l.name or bill.bill_number[:7] in l.name)
                filtered = self.account_move.line_ids.filtered(lambda l: l.account_id == account_id)
                lines += filtered[0]
            else:
                am = bill.send_form_id.account_move_line_ids.filtered(lambda l: l.account_id == bill.account_id and\
                    not l.reconciled and\
                    l.name == bill.bill_number or l.name == bill.bill_number[:7])
                lines = am.move_id.line_ids.filtered(lambda l: l.account_id == account_id and\
                    not l.reconciled and\
                    bill.bill_number in l.name or bill.bill_number[:7] in l.name and l.credit > 0)
                filtered = self.account_move.line_ids.filtered(lambda l: l.account_id == account_id)
                lines += filtered[0]
            lines.reconcile()
