# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from json import dumps
from odoo.exceptions import UserError
import json
from odoo.tools import float_round

class AccountMove(models.Model):
    _inherit = "account.move"

    custom_journal_id = fields.Many2one('account.journal', string='Diario para Aplicacion Anticipo', help='En la aplicacion de anticipo por defecto va el mismo diario, este dato permite cambiar lo aplicado en otro diario')

    def get_move_line_domain(self, vals):
        #Function encapsule the domain to inherit in other future functions
        domain = [
            '|', ('account_id', 'in', vals['pay_term_line_ids'].mapped('account_id').ids),
            ('account_id', 'in', vals['advance_payment_account_id']),
            '|', ('move_id.state', '=', 'posted'), '&', ('move_id.state', '=', 'draft'), ('journal_id.post_at', '=', 'bank_rec'),
            '|',('partner_id', '=', vals['move'].commercial_partner_id.id),
            ('import_number', '=', vals['move'].import_number or ''),
            ('reconciled', '=', False), '|', ('amount_residual', '!=', 0.0),
            ('amount_residual_currency', '!=', 0.0),
        ]
        return domain

    def _compute_payments_widget_to_reconcile_info(self):
        for move in self:
            move.invoice_outstanding_credits_debits_widget = json.dumps(False)
            move.invoice_has_outstanding = False

            if move.state != 'posted' or move.invoice_payment_state != 'not_paid' or not move.is_invoice(include_receipts=True):
                continue
            pay_term_line_ids = move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            
            # Obtener las cuentas de anticipos dese los parametros principales
            # y con eso se pueden mostrar los anticipos para poder aplicar en
            # las facturas
            advance_payment_account_id = []
            mp = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
            if move.is_inbound():
                advance_payment_account_id.append(mp.customer_advance_account_nc.id)
                advance_payment_account_id.append(mp.customer_advance_account_fc.id)
                for account in mp.other_accounts_client.ids:
                    advance_payment_account_id.append(account)
            else:
                advance_payment_account_id.append(mp.supplier_advance_account_nc.id)
                advance_payment_account_id.append(mp.supplier_advance_account_fc.id)
                # advance_payment_account_id.append(mp.supplier_advance_account_receipt_nc.id)
                # advance_payment_account_id.append(mp.supplier_advance_account_receipt_fc.id)
                for account in mp.other_accounts_supplier.ids:
                    advance_payment_account_id.append(account)

            vals = {
                'pay_term_line_ids': pay_term_line_ids,
                'advance_payment_account_id': advance_payment_account_id,
                'move': move,
            }

            domain = self.get_move_line_domain(vals)

            if move.is_inbound():
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                type_payment = _('Outstanding credits')
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                type_payment = _('Outstanding debits')
            info = {'title': '', 'outstanding': True, 'content': [], 'move_id': move.id}
            lines = self.env['account.move.line'].search(domain)
            currency_id = move.currency_id
            if len(lines) != 0:
                for line in lines:
                    # get the outstanding residual value in invoice currency
                    if line.currency_id and line.currency_id == move.currency_id:
                        amount_to_show = abs(line.amount_residual_currency)
                    else:
                        currency = line.company_id.currency_id
                        amount_to_show = currency._convert(abs(line.amount_residual), move.currency_id, move.company_id,
                                                           line.date or fields.Date.today())
                    if float_is_zero(amount_to_show, precision_rounding=move.currency_id.rounding):
                        continue
                    info['content'].append({
                        'journal_name': line.ref or line.move_id.name,
                        'amount': amount_to_show,
                        'currency': currency_id.symbol,
                        'id': line.id,
                        'position': currency_id.position,
                        'digits': [69, move.currency_id.decimal_places],
                        'payment_date': fields.Date.to_string(line.date),
                        'original_currency_id': line.currency_id.symbol if line.currency_id else self.env.company.currency_id.symbol,
                        'original_amount': abs(line.amount_residual_currency),
                        # 'type_change': line.tc,
                    })
                info['title'] = type_payment
                move.invoice_outstanding_credits_debits_widget = json.dumps(info)
                move.invoice_has_outstanding = True

    def js_assign_outstanding_line(self, line_id):
        # for l in self.line_ids:
        #     print(l.account_id.name, l.account_internal_type, l.reconciled)
        #     print(line_id, self.id)
        # Si es nota de credito no se hace la funcion original hasta despues 
        # de creado el asiento de aplicación
        lines = self.env['account.move.line'].browse(line_id)
        if self.type_document_id.code not in ('07','87','97') and lines.move_id.type_document_id.code not in ('07','87','97'):
            res = super(AccountMove, self).js_assign_outstanding_line(line_id)
            move_name = _('Advance payment aplication')
        else:
            move_name = _('Credit Note aplication')
        # for l in self.line_ids:
        #     print(l.account_id.name, l.account_internal_type, l.reconciled)
        #     print(line_id, self.id)
        # Obtener las cuentas de anticipos desde los parametros principales
        # y con eso se pueden mostrar los anticipos para poder aplicar en
        # las facturas
        advance_payment_account_id = []
        mp = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        # if move.is_inbound():
        advance_payment_account_id.append(mp.customer_advance_account_nc)
        advance_payment_account_id.append(mp.customer_advance_account_fc)
        for account in mp.other_accounts_client:
            advance_payment_account_id.append(account)
        # else:
        advance_payment_account_id.append(mp.supplier_advance_account_nc)
        advance_payment_account_id.append(mp.supplier_advance_account_fc)
        # advance_payment_account_id.append(mp.supplier_advance_account_receipt_nc)
        # advance_payment_account_id.append(mp.supplier_advance_account_receipt_fc)
        for account in mp.other_accounts_supplier:
            advance_payment_account_id.append(account)
        
        # Verificamos si esta instalado el modulo de letras
        module_boe = self.env['ir.module.module'].search([('name','=','jp_account_bills_of_exchange')])
        boe = True if module_boe and module_boe.state == 'installed' else False

        # Si es un pago le colocamos el tipo y nro de comprobante
        if lines.payment_id:
            payment = lines[0].payment_id
            payment.type_document_id = self.type_document_id
            payment.nro_comp = self.ref
            
        # Si la cuenta es de anticipo creamos el asiento y cambiamos la linea
        # para que pueda conciliar la factura
        # mp.customer_advance_account_nc or lines.account_id == mp.customer_advance_account_fc or lines.account_id == mp.supplier_advance_account_nc or lines.account_id == mp.supplier_advance_account_fc or lines.account_id == mp.supplier_advance_account_receipt_nc or lines.account_id == mp.supplier_advance_account_receipt_fc
        # TODO Las cuentas de facturas en soles y dolares no deben estar en la lista
        # de parametros principales, hacer la validación TODO
        if lines.account_id in advance_payment_account_id or self.type_document_id.code in ('07','87','97') or lines.move_id.type_document_id.code in ('07','87','97'): 
            vals = []
            exchange_rate = round(self.currency_id._get_conversion_rate(self.currency_id, self.env.company.currency_id, self.env.company, fields.Date.today()),2)
            account_id = lines.account_id
            exc_rate_inv = self.currency_rate
            if self.env.context.get('currency_rate') and self.env.context.get('currency_rate') > 0:
                exc_rate_inv = self.env.context.get('currency_rate')
            
            if self._context.get('payment_date'):
                payment_date = self._context.get('payment_date')
            else:
                payment_date = self.date
            
            # A solicitud de Karen y Edith que los pagos respeten el tipo de cambio de la caja de texto
            # en el widget y no el tipo de cambio del pago.
            # ******************************* A N T E R I O R **********************************
            # currency_rate = self._context.get('currency_rate')
            # if currency_rate and currency_rate > 0 and not lines.payment_id:
            #     exc_rate_pay = currency_rate
            # else:
            #     exc_rate_pay = lines.payment_id.type_change if lines.payment_id else lines.tc
            # ********************************* N U E V O **************************************
            exc_rate_pay = self._context.get('currency_rate')
            # **********************************************************************************

            # Si la factura es PEN
            if self.currency_id == self.env.company.currency_id:
                # Si el pago es PEN			
                if self.env.company.currency_id == lines.currency_id or not lines.currency_id:
                    # El monto a aplicar es el saldo aplicable del pago en soles		
                    amount_to_apply = abs(lines.amount_residual)
                    # Si el monto a aplicar en soles es menor al saldo pendiente de la factura
                    if amount_to_apply < abs(self.amount_residual):	
                        # Se aplica el monto total del pago
                        apply_payment = amount_to_apply
                    else:
                        # Se aplica el saldo pendiente de pago de la factura en soles
                        apply_payment = self.amount_residual
                    # Y el pago en dolares a aplicar es igual a 0 
                    apply_payment_currency = apply_invoice_currency = 0	
                # Si el pago es USD
                else:
                    # Ya no es necesario porque se modifico el modulo para tomar el tipo
                    # de cambio de la fecha automaticamente.
                    #***************************
                    # # Obtenemos el tipo de cambio del pago, pero si se personalizó
                    # # nos quedamos con el personalizado del recuadro
                    # exc_rate_pay = lines.tc if currency_rate == self.currency_rate else currency_rate
                    #***************************
                    # El monto a aplicar es el saldo en moneda del pago por el tipo de cambio obtenido
                    if not exc_rate_pay:
                        exc_rate_pay = 1
                    amount_to_apply = float_round(abs(lines.amount_residual_currency) * exc_rate_pay, 2)
                    # Si el monto en soles a aplicar es menor al monto residual de la factura
                    if amount_to_apply < abs(self.amount_residual):
                        # Se aplica el saldo del pago en dolares por el tipo de cambio obtenido	
                        apply_payment = amount_to_apply #float_round(abs(lines.amount_residual_currency) * exc_rate_pay, 2)
                        # El pago en dolares a aplicar es el saldo del pago en dolares
                        apply_payment_currency = apply_invoice_currency = abs(lines.amount_residual_currency)
                    # Si el monto en soles a aplicar es mayor o igual al monto residual de la factura
                    else:
                        # Se aplica el saldo de la factura en soles	
                        apply_payment = self.amount_residual
                        # Se aplica el saldo de la factura entre el tipo de cambio obtenido
                        apply_payment_currency = apply_invoice_currency = float_round(apply_payment / exc_rate_pay, 2)
                exc_rate_inv = 1
            # Si la factura es USD	
            else:
                # Si el pago es PEN
                if self.env.company.currency_id == lines.currency_id or not lines.currency_id:		
                    # amount_to_apply = float_round(abs(lines.amount_residual) / exc_rate_pay, 2)    
                    # Obtenemos el tipo de cambio del recuadro
                    # exc_rate_pay = currency_rate
                    # El monto a aplicar es el saldo del pago en soles
                    amount_to_apply = abs(lines.amount_residual)
                    amount_to_compare = abs(lines.amount_residual)
                    compare_with = abs(self.amount_residual_signed)
                # Si el pago es USD
                else:
                    # Ya no es necesario porque se modifico el modulo para tomar el tipo
                    # de cambio de la fecha automaticamente.
                    #***************************
                    # # Obtenemos el tipo de cambio del pago, pero si se personalizó
                    # # nos quedamos con el personalizado del recuadro
                    # exc_rate_pay = currency_rate
                    #***************************
                    # El monto a aplicar es el saldo del pago en soles
                    if not exc_rate_pay:
                        exc_rate_pay = 1
                    amount_to_apply = float_round(abs(lines.amount_residual_currency) * exc_rate_pay, 2)
                    amount_to_compare = abs(lines.amount_residual_currency)
                    compare_with = abs(self.amount_residual)
                # Si el monto a aplicar es menor que el saldo de la factura en soles
                if amount_to_compare < compare_with:
                    # apply_payment = float_round(amount_to_apply * exc_rate_pay, 2)
                    # Se aplica el saldo del pago en soles
                    apply_payment = amount_to_apply
                    # Se aplica el saldo del pago en soles entre el tipo de cambio obtenido
                    apply_payment_currency = apply_invoice_currency = float_round(amount_to_apply / exc_rate_pay, 2)
                # Si el monto a aplicar es mayor o igual que el saldo de la facura en soles
                else:
                    # Se aplica el el saldo de la factura por el tipo de cambio obtenido		
                    apply_payment = float_round(abs(self.amount_residual) * exc_rate_pay, 2)
                    # Se aplica el saldo de la factura
                    apply_payment_currency = apply_invoice_currency = self.amount_residual
                # El tipo de cambio para la factura es el tipo de cambio obtenido
                exc_rate_inv = exc_rate_pay
                # Luego convertimos el tipo de cambio del pago a 1 si el pago es PEN
                exc_rate_pay = 1 if self.env.company.currency_id == lines.currency_id or not lines.currency_id else exc_rate_pay
            # El monto a aplicar a la factura es igual al monto a aplicar del pago
            apply_invoice = apply_payment
            if self.custom_journal_id:
                journal = self.custom_journal_id
            else:
                if self.type_document_id.code in ('07','87','97') or lines.move_id.type_document_id.code in ('07','87','97'):
                    if not mp.credit_journal:
                        raise UserError(_('There is no journal for credit notes in company main parameters. Please select one.'))
                    journal = mp.credit_journal
                else:
                    journal = lines.payment_id.journal_id if lines.payment_id else lines.journal_id
            # Asiento de aplicación
            am = self.env['account.move'].create({
                'journal_id': journal.id,
                'name': '/',
                'currency_rate': exc_rate_pay,
                'date': payment_date, # self.date, #fields.Date.today(),
                'invoice_date': self.invoice_date,
                'invoice_date_due': self.invoice_date_due,
                'partner_id': self.partner_id.id,
                # 'ref': _('Invoice payment %s') %self.ref,
                'glosa': _(move_name + ' on %s') %(self.ref if self.type_document_id.code not in ('07','87','97') else lines.move_id.ref),
                'currency_id': self.currency_id.id,
                })
            # Para obtener la secuencia
            to_write ={}
            sequence = am._get_sequence()
            if not sequence:
                raise UserError(_('Please define a sequence on your journal.'))
            # Consume a new number.
            to_write['name'] = sequence.with_context(ir_sequence_date=am.date).next_by_id()
            am.write(to_write)
            # Pago de factura o nota de credito
            val = {
                'move_id': am.id,
                'name': move_name + ' ' + self.ref, #lines.move_id.ref, # if self.type_document_id.code != '07' else self.ref),
                'partner_id': lines.partner_id.id,
                'type_document_id': lines.type_document_id.id,
                'nro_comp': lines.nro_comp,
                #'exchange_rate': lines.tc, #exc_rate_pay, #self.currency_id._get_conversion_rate(self.currency_id, self.env.company.currency_id, self.env.company, fields.Date.today()),
                'debit': apply_payment if self.is_inbound() else 0,
                'credit': 0 if self.is_inbound() else apply_invoice,
                'account_id': account_id.id,
                'currency_id': lines.currency_id.id, # if self.env.company.currency_id != lines.currency_id else lines.currency_id.id,
                'amount_currency': (apply_payment_currency if lines.currency_id else 0) * (1 if self.is_inbound() else -1),
                'balance': apply_payment * (1 if self.is_inbound() else -1),
                'tc': exc_rate_pay, #if lines.currency_id else round(self.currency_id._get_conversion_rate(self.currency_id, self.env.company.currency_id, self.env.company, fields.Date.today()),2),
                'date': lines.date,
                'date_maturity': lines.date_maturity,
            }
            if boe:
                val.update({'exchange_rate': lines.tc,})
            vals.append(val)
            # Factura
            val = {
                'move_id': am.id,
                'name': _('Invoice %s') %lines.move_id.ref, #%(self.ref if self.type_document_id.code != '07' else lines.move_id.ref),
                'partner_id': self.partner_id.id,
                'type_document_id': self.type_document_id.id,
                'nro_comp': self.ref,
                #'exchange_rate': exc_rate_inv, #self.currency_rate,
                'credit': apply_invoice if self.is_inbound() else 0,
                'debit': 0 if self.is_inbound() else apply_payment,
                'account_id': self.line_ids.filtered(lambda line: line.account_internal_type in ('receivable','payable') and not line.reconciled).account_id.id,
                'currency_id': False if self.env.company.currency_id == self.currency_id else (lines.currency_id.id if lines.currency_id else self.currency_id.id),
                'amount_currency': (apply_invoice_currency if self.currency_id != self.env.company.currency_id else 0) * (-1 if self.is_inbound() else 1),
                'balance': apply_invoice * (-1 if self.is_inbound() else 1),
                'tc': exc_rate_inv, #self.currency_rate,
                'date': self.invoice_date,
                'date_maturity': self.invoice_date_due,
            }
            if boe:
                val.update({'exchange_rate': exc_rate_inv})
            vals.append(val)
            # Obtener el diario y las cuentas de diferencia de cambio desde la configuración
            exchange_journal = self.env.company.currency_exchange_journal_id
            total_credit = round(sum(item['credit'] for item in vals),2)
            total_debit = round(sum(item['debit'] for item in vals),2)
            if total_credit > total_debit:
                # Asiento de diferencia de cambio por ganancia
                val = {
                    'move_id': am.id,
                    'name': _('Currency exchange rate difference'),
                    'debit': round(abs(total_debit - total_credit),2),# if self.is_inbound() else 0,
                    'credit': 0.0 ,#if self.is_inbound() else round(abs(total_debit - total_credit),2),
                    'account_id': exchange_journal.default_debit_account_id.id,
                    'balance': round(abs(total_debit - total_credit),2) * (1 if self.is_inbound() else -1),
                    }
                vals.append(val)
            if total_credit < total_debit:
                # Asiento de diferencia de cambio por ganancia
                val = {
                    'move_id': am.id,
                    'name': _('Currency exchange rate difference'),
                    'debit': 0.0, #if self.is_inbound() else round(abs(total_debit - total_credit),2),
                    'credit': round(abs(total_debit - total_credit),2), #if self.is_inbound() else 0,
                    'account_id': exchange_journal.default_credit_account_id.id,
                    'balance': round(abs(total_debit - total_credit),2) * (-1 if self.is_inbound() else 1),
                    }
                vals.append(val)
            
            new_lines = self.env['account.move.line'].create(vals)
            new_lines.filtered(lambda l: l.name == _(move_name) + ' ' + lines.move_id.ref if lines.move_id.ref else '').date = vals[0]['date']
            am.post()
            account_payment = self.env['account.payment'].search([('id','=',lines[0].payment_id.id)])
            # account_payment.reconciled_invoice_ids = [(4, am.id)]
            # Conciliar el pago con el nuevo asiento creado antes de conciliar la factura
            lines_ant = lines
            # lines = new_lines[0]
            # for l in new_lines:
            #     print(l.name)
            #     print(_(move_name) + ' ' + (self.ref if self.type_document_id.code == '07' else lines.move_id.ref))
            lines = new_lines.filtered(lambda l: l.name == _(move_name) + ' ' + self.ref) # (self.ref if self.type_document_id.code == '07' else lines.move_id.ref))
            if account_payment:
                # for l in account_payment.move_line_ids:
                #     print(l.account_internal_type, l.debit, l.credit, l.name, l.account_id)
                lines += account_payment.move_line_ids.filtered(lambda l: l.account_internal_type in ('receivable','payable')) #[0]
            else:
                # Si está instalado el módulo verifica sino saltea para Sixto y otras empresas sin Letras
                bills_of_exchange = self.env['ir.module.module'].search([('name', '=', 'jp_account_bills_of_exchange'),('state', '=', 'installed')])
                if bills_of_exchange:
                    if lines_ant.bill_form_id:
                        lines += lines_ant.bill_form_id.account_move_line_ids.filtered(lambda line: line.account_id == lines.account_id and not line.reconciled and (line.credit > 0 if self.is_inbound() else line.debit > 0))
                    else:
                        lines += lines_ant
                else:
                    lines += lines_ant
            lines.reconcile()
            # Conciliar la factura con el nuevo asiento creado
            # lines = new_lines[1]
            lines = new_lines.filtered(lambda l: l.name == _('Invoice %s') %lines_ant.move_id.ref) #%(self.ref if self.type_document_id.code != '07' else lines_ant.move_id.ref))
            # Si es nota de credito despues de creada la aplicación recien se hace la funcion
            # original
            if self.type_document_id.code in ('07','87','97') or lines_ant.move_id.type_document_id.code in ('07','87','97'):
                res = super(AccountMove, self).js_assign_outstanding_line(lines.id)
            else:
                lines += self.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                lines.reconcile()
        return res

    def button_draft(self):
        payments = self.line_ids.mapped('matched_debit_ids') + self.line_ids.mapped('matched_credit_ids')
        for payment in payments:
            debit_move_id = payment.debit_move_id.move_id
            credit_move_id = payment.credit_move_id.move_id
            if debit_move_id != self and debit_move_id.glosa and (debit_move_id.glosa[:29] == 'Advance payment aplication on' if debit_move_id.glosa else False):
                advance_payment = debit_move_id.line_ids.filtered(lambda x: x.reconciled == True)
                (advance_payment.mapped('matched_debit_ids') + advance_payment.mapped('matched_credit_ids')).unlink()
                debit_move_id.write({'state': 'draft'})
                debit_move_id.with_context(force_delete=True).unlink()
            if credit_move_id != self and (credit_move_id.glosa[:29] == 'Advance payment aplication on' if credit_move_id.glosa else False):
                advance_payment = credit_move_id.line_ids.filtered(lambda x: x.reconciled == True)
                (advance_payment.mapped('matched_debit_ids') + advance_payment.mapped('matched_credit_ids')).unlink()
                credit_move_id.write({'state': 'draft'})
                credit_move_id.with_context(force_delete=True).unlink()
        res = super(AccountMove, self).button_draft()
        return res

    def get_currency_rate(self, date):
        # date = self.env.context.get('date')
        if date and self.currency_id:
            rate = round(self.currency_id._get_conversion_rate(self.currency_id, self.env.company.currency_id, self.env.company, date), 4)
            return rate

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Si se rompe la conciliación tambien debemos borrar el
    # asiento contable de la aplicación creado anteriormente
    def remove_move_reconcile(self):
        move_to_del = self.env['account.move']
        for line in self:
            # for line in self:
            move_id = line.move_id #self.move_id
            # Obtener las cuentas de anticipos desde los parametros principales
            # y con eso se pueden mostrar los anticipos para poder aplicar en
            # las facturas
            mp_advance_accounts = []
            mp = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
            mp_advance_accounts.append(mp.customer_advance_account_nc)
            mp_advance_accounts.append(mp.customer_advance_account_fc)
            mp_advance_accounts.append(mp.supplier_advance_account_nc)
            mp_advance_accounts.append(mp.supplier_advance_account_fc)
            # mp_advance_accounts.append(mp.supplier_advance_account_receipt_nc)
            # mp_advance_accounts.append(mp.supplier_advance_account_receipt_fc)
            for account in mp.other_accounts_client:
                mp_advance_accounts.append(account)
            for account in mp.other_accounts_supplier:
                mp_advance_accounts.append(account)
            # for l in line:
            if self.payment_id:
                self.payment_id.type_document_id = False
                self.payment_id.nro_comp = ''
            to_unlink = self.env['account.partial.reconcile']
            if move_id.type == 'entry': # and move_id.glosa and move_id.glosa[:29] == 'Advance payment aplication on':
                if not self.payment_id:
                    if any(l.account_id in mp_advance_accounts for l in move_id.line_ids) and any(l.reconciled for l in move_id.line_ids):
                        to_unlink = (self.mapped('matched_debit_ids') + self.mapped('matched_credit_ids'))
                        advance_payment = move_id.line_ids.filtered(lambda x: x.reconciled == True)
                        to_unlink += (advance_payment.mapped('matched_debit_ids') + advance_payment.mapped('matched_credit_ids'))
                        move_to_del += move_id
                    if move_id.glosa and move_id.glosa[:len(_('Credit Note aplication'))] == _('Credit Note aplication'):
                        to_unlink = (self.mapped('matched_debit_ids') + self.mapped('matched_credit_ids'))
                        advance_payment = move_id.line_ids.filtered(lambda x: x.reconciled == True)
                        to_unlink += (advance_payment.mapped('matched_debit_ids') + advance_payment.mapped('matched_credit_ids'))
                        move_to_del += move_id
            to_unlink.unlink()
        res = super(AccountMoveLine, self).remove_move_reconcile()
        for m in move_to_del:
            if m.glosa and (m.glosa[:len(_('Advance payment aplication'))] == _('Advance payment aplication') or m.glosa[:len(_('Credit Note aplication'))] == _('Credit Note aplication')):
                m.write({'state': 'draft'})
                to_unlink = self.env['account.partial.reconcile']
                to_unlink = (m.line_ids.mapped('matched_debit_ids') + m.line_ids.mapped('matched_credit_ids'))
                to_unlink.unlink()
                m.with_context(force_delete=True).unlink()
        return res
    