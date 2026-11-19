# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#from _typeshed import Self
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json
from odoo.tools import float_round

class PaymentRequest(models.Model):
    _name = "fxo.payment.request"

    name = fields.Char(string='Numero de socilitud', default='/', copy=False)
    line_id = fields.One2many(comodel_name='fxo.payment.request.line', inverse_name='payment_request_id', string='Lineas', states={'done': [('readonly', True)], 'confirm': [('readonly', True)]})
    state = fields.Selection(string='Estado', selection=[
        ('draft', 'Borrador'), 
        ('confirm', 'Confirmado'),
        ('done','Aprobado'),
        ('payed', 'Pagado'),
    ], default='draft')
    partner_id  = fields.Many2one(comodel_name='res.partner', string='Proveedor', states={'done': [('readonly', True)], 'confirm': [('readonly', True)]})
    date_request = fields.Date(string='Fecha Solicitud', default=fields.Date.today(), states={'done': [('readonly', True)], 'confirm': [('readonly', True)]})
    user_request = fields.Many2one(comodel_name='res.users', string='Solicitante', states={'done': [('readonly', True)], 'confirm': [('readonly', True)]})
    user_paymen = fields.Many2one(comodel_name='res.users', string='Registro de Pago', states={'done': [('readonly', True)], 'confirm': [('readonly', True)]})
    company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company, states={'done': [('readonly', True)], 'confirm': [('readonly', True)]})
    journal_id = fields.Many2one('account.journal', string='Diario de Pago', domain=[('type', 'in', ['bank', 'cash'])])
    
    bank_id  = fields.Many2one(comodel_name='res.partner.bank', string='Cuenta Bancaria', states={'done': [('readonly', True)], 'confirm': [('readonly', True)]})
    paid_to  = fields.Many2one(comodel_name='res.partner', string='Girado a', states={'done': [('readonly', True)], 'confirm': [('readonly', True)]})
    p_detraction = fields.Float(string='% Detraccion')
    
    observation = fields.Text(string='Observaciones')
    supplier_observation  = fields.Text(string='Observacion Proveedor')

    id_loges = fields.Char(string='Id Loges')

    catalog_payment_id = fields.Many2one('einvoice.catalog.payment', string='Medio de Pago')

    invoice_ids = fields.Many2many('account.move', 'payment_request_move_rel', copy=False)
    invoice_count = fields.Integer(compute='_compute_invoice_count')

    payment_ids = fields.Many2many('account.payment', 'payment_request_payment_rel', copy=False)
    payment_count = fields.Integer(compute='_compute_payment_count')

    move_line_ids = fields.One2many('account.move.line', 'matched_request_id', copy=False)
    move_line_count = fields.Integer(compute='_compute_move_line_count')

    move_ids = fields.One2many(comodel_name='account.move', inverse_name='request_id', string='Asientos Contable')
    move_count = fields.Integer(compute='_compute_move_count')

    #JGB
    move_line = fields.One2many('account.move.line', 'request_id', string='Facturas')
    type_payment  = fields.Selection(string='Tipo de Pago', selection=[('O', 'Operativa'), ('A', 'Administrativa'),],default='A')



    order_id = fields.Many2one('sale.order', string='Nro. de Operacion')
    internal_ref = fields.Char(related='order_id.internal_ref', string='Referencia Interna', store=True)
    internal_ref_child = fields.Char(related='order_id.internal_ref_child',string="#Referencia hija")
    amount_total = fields.Float(compute='_compute_amount_total', string='Monto Total', store=True)
    sustained = fields.Float(compute='_compute_sustained', string='Monto Sustentado')
    residual = fields.Float(compute='_compute_residual', string='Saldo')
    free = fields.Float(compute='_compute_free', string='Asiento Libre')
    payment_date = fields.Date(string='Fecha Contable', default=fields.Date.today())
    issue_date = fields.Date(string='Fecha Emision', default=fields.Date.today())
    reference_number = fields.Char(string='Numero de Comprobate')
    op_number = fields.Char(string='Nro. Op. Caja')
    date_due = fields.Date(string='Fecha Vencimiento', default=fields.Date.today())
    type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo de Documento', default=lambda self: self.env['einvoice.catalog.01'].search([('code', '=', '00')]).id)
    communication = fields.Char(string='Circular', compute='get_communication')
    indepent_move_id = fields.Many2one('account.move', string='Asiento Contable Libre')
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id.id if self.env.company.currency_id else None)


   
    
    @api.depends('line_id.partner_id', 'order_id', 'line_id.product_id')
    def get_communication(self):
        for rec in self:
            rec.communication = '{0}{1}{2}'.format(
                rec.line_id[0].partner_id.name if rec.line_id else '',
                rec.order_id.name if rec.order_id else '',
                rec.line_id[0].product_id.name if rec.line_id else '',
            )

    @api.onchange('currency_id', 'journal_id')
    def get_currency(self):
        if self.journal_id:
            self.currency_id = self.journal_id.currency_id if self.journal_id.currency_id else self.env.company.currency_id
        for line in self.line_id:
            line.currency_id = self.currency_id

    def get_confirm(self):
        self.state = 'confirm'

    @api.depends('line_id.amount')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_id.mapped('amount')) if rec.line_id else 0

    @api.depends('line_id.amount_invoiced')
    def _compute_sustained(self):
        for rec in self:
            rec.sustained = sum(rec.line_id.mapped('amount_invoiced')) if rec.line_id else 0

    @api.depends('amount_total', 'sustained', 'free')
    def _compute_residual(self):
        for rec in self:
            rec.residual =  rec.free - rec.sustained
 
    @api.depends('move_line')
    def _compute_free(self):
        for rec in self:
            rec.free = 0
            for line in rec.move_line:
                if line.account_id.user_type_id.type == "liquidity" and line.move_id.state != "draft":
                    if self.currency_id.name == "USD":
                        rec.free += line.amount_currency * -1
                    else :
                        rec.free += abs(line.credit) - abs(line.debit)

    @api.model
    def create(self, vals):
        res = super(PaymentRequest, self).create(vals)
        if res.line_id:
            lines = res.line_id.filtered(lambda l: l.doc_number)
            line = lines[0]
            if line.doc_number:
                res.order_id = line.doc_number
        return res

    def write(self, vals):
        if 'line_id' in vals:
            for line in vals['line_id']:
                if line[2] and 'doc_number' in line[2]:
                    vals['order_id'] = line[2]['doc_number']
        return super(PaymentRequest, self).write(vals)

    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(self.invoice_ids)

    def _compute_payment_count(self):
        for record in self:
            record.payment_count = len(self.payment_ids)

    def _compute_move_line_count(self):
        for rec in self:
            rec.move_line_count = len(self.move_line_ids)
    
    def _compute_move_count(self):
        for rec in self:
            rec.move_count = len(self.move_ids)

    @api.constrains('indepent_move_id')
    def constrains_indepent_move_id(self):
        if self.indepent_move_id.id:
            self.indepent_move_id.request_id = self.id

    def get_request_invoices(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "views": [[False, "tree"],[False, "form"]],
            "domain": [['id', 'in', self.invoice_ids.ids]],
            "name": "Facturas",
        }

    def get_request_payments(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "views": [[False, "tree"],[False, "form"]],
            "domain": [['id', 'in', self.payment_ids.ids]],
            "name": "Pagos",
        }

    def get_account_move(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "context" : "{'default_request_id':"+ str(self.id) + "}",
            "views": [[self.env.ref('account.view_move_tree').id, "tree"],[False, "form"]],
            "domain": [['id', 'in', self.move_ids.ids]],
            "name": "Asiento Contable",
        }


    def get_request_lines(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move.line",
            "views": [[self.env.ref('account.view_move_line_tree').id, "tree"],[False, "form"]],
            "domain": [['id', 'in', self.move_line_ids.ids]],
            "name": "Apuntes",
        }

    def get_invoices_gen_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "invoice.payment.wizard",
            "views": [(False, "form")],
            "context": self._context,
            "name": "Generacion de Facturas",
            "target": "new",
        }
    
    def apply_payments_wizard(self):
            return {
            "type": "ir.actions.act_window",
            "res_model": "apply.payment.wizard",
            "views": [(False, "form")],
            "context": self._context,
            "name": "Generacion de Facturas",
            "target": "new",
        }

    def apply_payments(self):
        # return self.invoice_ids.action_assign_payments()
        entry = self.create_payment_entry()
        self.apply_payments_entry(entry)

    def create_payment_entry(self,apply_payments = False,date=False):
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        currency_rate = self.currency_id._get_conversion_rate(self.currency_id, self.env.company.currency_id, self.env.company, self.indepent_move_id.date)#fields.Date.today())
        #payment_date = fields.Date.today()
        val = {}
        vals = []
        # Asiento de aplicación
        invoices = list(inv.ref for inv in self.invoice_ids)
        journal = self.invoice_ids[0].custom_journal_id if self.invoice_ids[0].custom_journal_id else self.invoice_ids[0].journal_id
        am = self.env['account.move'].create({
            'journal_id': journal.id,
            'name': journal.sequence_id.with_context(ir_sequence_date=date).next_by_id(),
            'currency_rate': currency_rate,
            'date': fields.Date.today(),
            'invoice_date': fields.Date.today(),
            'partner_id': self.partner_id.id,
            'glosa': '%s%s%s' % (
                self.partner_id.name if self.partner_id else '', 
                self.order_id.name if self.order_id else '',
                self.line_id[0].product_id.name if self.line_id[0].product_id else '',
            ),#_('Aplication on %s') %(invoices),
            'currency_id': self.currency_id.id,
            })

        for inv in self.invoice_ids:
            if self.residual < 0 and not self.residual >= -1:
                amount = self.amount_total if self.currency_id != self.env.company.currency_id else 0
                amount_signed = float_round(abs(self.amount_total) * currency_rate, 2) if self.currency_id != self.env.company.currency_id else abs(self.amount_total)
            else:
                amount = inv.amount_residual if self.currency_id != self.env.company.currency_id else 0
                amount_signed = float_round(abs(inv.amount_residual) * currency_rate, 2) if self.currency_id != self.env.company.currency_id else abs(inv.amount_residual)
            # Pago de factura o nota de credito
            val = {
                'move_id': am.id,
                'name': _('Invoice %s') %inv.ref, #lines.move_id.ref, # if inv.type_document_id.code != '07' else inv.ref),
                'partner_id': inv.partner_id.id,
                'type_document_id': inv.type_document_id.id,
                'nro_comp': inv.ref ,#if self.type_payment == 'O' else inv.name,#lines.nro_comp,
                #'exchange_rate': lines.tc, #exc_rate_pay, #inv.currency_id._get_conversion_rate(inv.currency_id, inv.env.company.currency_id, inv.env.company, fields.Date.today()),
                'debit': amount_signed,
                'credit': 0,
                'account_id': inv.line_ids.filtered(lambda l: l.account_internal_type in ['receivable','payable']).account_id.id,
                'currency_id': self.currency_id.id if inv.env.company.currency_id != self.currency_id else '',
                'amount_currency': amount if self.currency_id != self.env.company.currency_id else 0,# * -1,
                'balance': amount_signed,
                'tc': currency_rate if self.currency_id != self.env.company.currency_id else 1, #if lines.currency_id else round(inv.currency_id._get_conversion_rate(inv.currency_id, inv.env.company.currency_id, inv.env.company, fields.Date.today()),2),
                'date': self.indepent_move_id.date,
                'date_maturity': fields.Date.today(),
                'order_id': self.order_id.id if self.order_id else None,
                'request_id': self.id,
            }
            vals.append(val)
        # Monto a aplicar en facturas
        line_to_apply = self.indepent_move_id.line_ids.filtered(lambda l: l.account_internal_type in ['receivable','payable'])
        if self.residual > 0 and not self.residual <= 1:
            amount = self.sustained
            amount_signed = float_round(abs(self.sustained) * currency_rate, 2) if self.currency_id != self.env.company.currency_id else abs(self.sustained)
        else:
            amount = line_to_apply.amount_currency
            amount_signed = float_round(line_to_apply.amount_currency * currency_rate, 2) if self.currency_id != self.env.company.currency_id else (line_to_apply.debit if line_to_apply.debit > 0 else line_to_apply.debit)
        val = {
            'move_id': am.id,
            'name': '%s' % line_to_apply.name,
            # %(self.ref if self.type_document_id.code != '07' else lines.move_id.ref),
            #'name': _('Move %s') %self.indepent_move_id.ref, #%(self.ref if self.type_document_id.code != '07' else lines.move_id.ref),
            'partner_id': self.partner_id.id,
            #'type_document_id': self.type_document_id.id if self.type_document_id else None,
            'type_document_id': line_to_apply.type_document_id.id if line_to_apply.type_document_id else None,
            #'nro_comp': self.indepent_move_id.ref,
            'nro_comp': line_to_apply.nro_comp ,
            'credit': amount_signed,
            'debit': 0,
            'account_id': line_to_apply.account_id.id,
            'currency_id': line_to_apply.currency_id.id if self.currency_id != self.env.company.currency_id else '',
            'amount_currency': amount * -1 if self.currency_id != self.env.company.currency_id else 0,
            'balance': amount_signed * -1,
            'tc': currency_rate if self.currency_id != self.env.company.currency_id else 1, #self.currency_rate,
            'date': line_to_apply.date,
            'date_maturity': fields.Date.today(),
            'order_id': self.order_id.id if self.order_id else None,
            'request_id': self.id,
        }

        vals.append(val)
        # Diferencia por redondeo
        # Obtener el diario y las cuentas de redondeo desde la configuración
        params = self.env['ir.config_parameter'].sudo()
        round_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.round_boe_journal_id'))
        #round_journal = self.env['account.journal'].search([('id','=',round_boe_journal_id)])   
        #if not round_journal:
            #raise UserError(_('Round Journal not configured in settings.'))
        #else:
            #if not round_journal.default_credit_account_id:
                #raise UserError(_('Round Journal credit account not configured in settings.'))
            #if not round_journal.default_debit_account_id:
                #raise UserError(_('Round Journal debit account not configured in settings.'))
        total_debit = float_round(sum(item['debit'] for item in vals),2)
        total_credit = float_round(sum(item['credit'] for item in vals),2)
        difference = (abs(total_credit) - (total_debit))
        if MainParameter.adjustment_amount == 0 and difference != 0:
            raise UserError(_('Adjustment amount can\'t be 0. Please enter adjustment amount in main parameters -> payment request'))
        if difference > 0 and difference <= MainParameter.adjustment_amount:
            if not MainParameter.adjust_account_id:
                raise UserError('Falta configurar Cuenta de Ajuste Debito en Parametros Principales')
            # Asiento de diferencia por redondeo ganancia
            val = {
                'name': _('Currency round difference'),
                'debit': abs(float_round(difference,2)),
                'credit': 0.0,
                'account_id': MainParameter.adjust_account_id.id,
                'move_id': am.id,
                'balance': float_round(abs(difference),2),
                }
            vals.append(val)
        if difference < 0 and difference >= - MainParameter.adjustment_amount:
            # Asiento de diferencia por redondeo perdida
            if not MainParameter.adjust_account_credit_id:
                raise UserError('Falta configurar Cuenta de Ajuste Credito en Parametros Principales')
            val = {
                'name': _('Currency round difference'),
                'debit': 0.0,
                'credit': float_round(abs(difference),2),
                'account_id': MainParameter.adjust_account_credit_id.id,
                'move_id': am.id,
                'balance': float_round(abs(difference),2) * -1,
                }
            vals.append(val)
        self.env['account.move.line'].create(vals)
        am.action_post()
        return am

    def apply_payments_entry(self, entry):
        # Conciliar facturas
        for inv in self.invoice_ids:
            # line = inv.line_ids.filtered(lambda l: l.account_internal_type in ['receivable','payable'])
            lines = inv.line_ids.filtered(lambda l: l.account_internal_type in ['receivable','payable'])
            # line1 = entry.line_ids.filtered(lambda l: l.account_id == lines.account_id and l.nro_comp == inv.ref)
            lines += entry.line_ids.filtered(lambda l: l.account_id == lines.account_id and l.nro_comp == inv.ref)
            lines.reconcile()
        # Conciliar asiento indepent
        lines = self.indepent_move_id.line_ids.filtered(lambda l: l.account_internal_type in ['receivable','payable'])
        lines += entry.line_ids.filtered(lambda l: l.account_id == lines.account_id and not l.reconciled)
        lines.reconcile()
        
    def get_moves_gen_wizard(self):
        if self.residual <= 0:
            raise UserError('Para utilizar esta funcion el saldo debe ser mayor a cero')
        Payment = self.payment_ids[0]
        context = self._context.copy()
        context.update({
            'default_amount_nc': float_round(self.residual * Payment.type_change, 2) if Payment.currency_id.name == 'USD' else self.residual,
            'default_amount_fc': self.residual if Payment.currency_id.name == 'USD' else float_round(self.residual / Payment.type_change, 2),
            'default_currency_rate': Payment.type_change,
            'default_type_document_id': Payment.type_document_id.id,
            'default_number': Payment.nro_comp,
            'default_account_id': Payment.destination_account_id.id,
            'default_currency_id': Payment.currency_id.id,
            'default_partner_id': Payment.partner_id.id,
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "move.payment.wizard",
            "views": [(False, "form")],
            "context": context,
            "name": "Generacion de Asientos",
            "target": "new",
        }

    @api.constrains('line_id')
    def _verify_currency(self):
        for record in self:
            if any(line.currency_id != record.line_id[0].currency_id for line in record.line_id):
                raise UserError('No se puede utilizar monedas distintas en las lineas')

    def set_confirm(self):
        for record in self:
            if record.state == 'draft':
                if record.line_id:    
                    if any(l.partner_id.credit_balance < 0 for l in record.line_id):
                        record.state = 'confirm'
                    else:
                        record.state = 'done'
                    if record.name == '/':
                        record.name = self.env['ir.sequence'].next_by_code('seq_payment_request') or '/'
                    lines = record.line_id.filtered(lambda l: l.doc_number)
                    if lines:
                        record.order_id = lines[0].doc_number
                else:
                    raise UserError('Necesita lineas para confirmar')

    def set_done(self):
        for record in self:
            User = self.env['res.user.credit.limit'].search([('user_id', '=', self.env.user.id)])
            over_rate = (1 + User.order_over_rate/100) if User and User.order_over_rate > 0 else 1
            if any(l.partner_id.credit_balance < -(l.partner_id.credit_limit2 * over_rate) for l in record.line_id):
                raise UserError('Es necesario que todos los clientes tengan credito positivo para Aprobar esta solicitud')
            else:
                record.state = 'done'
            if record.line_id:
                lines = record.line_id.filtered(lambda l: l.doc_number)
                if lines:
                    record.order_id = lines[0].doc_number

    def set_draft(self):
        if self.indepent_move_id:
            self.indepent_move_id.button_draft()
            self.indepent_move_id.action_change_name()
            self.indepent_move_id.unlink()
        self.state = 'draft'

    def delete_sequence(self):
        for rec in self:
            rec.name = '/'

    def get_payment_wizard(self):
        return {
            'name': 'Registro de Pagos',
            'type': 'ir.actions.act_window',
            'res_model': 'fxo.payment.request.wizard',
            'views': [(self.env.ref('fxo_payment_request.view_fxo_payment_request_wizard_form').id, 'form')],
            'target': 'new'
        }
    
    def aditional_payment(self):
        line = self.line_id[0]
        import pytz
        if not self.env.user.partner_id.tz:
            raise UserError('Es necesario que configure la zona horaria en el partner del usuario que esta utilizando')
        tz = pytz.timezone(self.env.user.partner_id.tz)
        date_tz = pytz.utc.localize(fields.Datetime.now()).astimezone(tz).strftime('%Y-%m-%d')
        destination_account_id = None
        if line.currency_id.name == 'PEN':
            destination_account_id = line.product_id.product_tmpl_id.account_destination_nc_id
        else:
            destination_account_id = line.product_id.product_tmpl_id.account_destination_fc_id
        if self.env.company.currency_id == self.currency_id:
            currency_rate = 1
        else:
            currency_rate = line.currency_id._get_conversion_rate(line.currency_id, self.env.company.currency_id, self.env.company, fields.Date.today())
        payment = self.env['account.payment'].create({
            'payment_method_id': 2,
            'payment_type': 'outbound',
            'product_id': line.product_id.id,
            'partner_id': self.partner_id.id,
            'partner_type': 'supplier',
            'destination_account_id': destination_account_id.id if destination_account_id else None,
            'amount': abs(self.residual),
            'cash_nro_comp': self.name,
            'currency_id': line.currency_id.id,
            'payment_date': date_tz,
            'order_id': line.doc_number.id,
            'request_id': self.id,
            'request_line_id': line.id,
            'catalog_payment_id': self.catalog_payment_id.id if self.catalog_payment_id else None,
            'journal_id': self.journal_id.id,
            'type_change': currency_rate,
            'type_document_id': self.env['einvoice.catalog.01'].search([('code', '=', '00')]).id,
            'nro_comp': self.name,
        })
        self.payment_ids = [(4, payment.id)]

    def generate_payments(self):
        import pytz
        if not self.env.user.partner_id.tz:
            raise UserError('Es necesario que configure la zona horaria en el partner del usuario que esta utilizando')
        tz = pytz.timezone(self.env.user.partner_id.tz)
        date_tz = pytz.utc.localize(fields.Datetime.now()).astimezone(tz).strftime('%Y-%m-%d')
        payments = []
        for line in self.line_id:
            MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
            destination_account_id = None
            if line.currency_id.name == 'PEN':
                destination_account_id = line.product_id.product_tmpl_id.account_destination_nc_id
            else:
                destination_account_id = line.product_id.product_tmpl_id.account_destination_fc_id
            currency_rate = line.currency_id._get_conversion_rate(line.currency_id, self.env.company.currency_id, self.env.company, fields.Date.today())
            payment = self.env['account.payment'].create({
                'payment_method_id': 2,
                'payment_type': 'outbound',
                'product_id': line.product_id.id,
                'partner_id': self.partner_id.id,
                'partner_type': 'supplier',
                'destination_account_id': destination_account_id.id if destination_account_id else None,
                'amount': line.amount,
                'cash_nro_comp': self.name,
                'currency_id': line.currency_id.id,
                'payment_date': date_tz,
                'order_id': line.doc_number.id,
                'request_id': self.id,
                'request_line_id': line.id,
                'catalog_payment_id': self.catalog_payment_id.id if self.catalog_payment_id else None,
                'journal_id': self.journal_id.id,
                'type_change': currency_rate,
                'type_document_id': self.env['einvoice.catalog.01'].search([('code', '=', '00')]).id,
                'nro_comp': self.name,
            })
            payments.append(payment.id)
            line.payment_id = payment.id
        self.payment_ids = [(6, 0, payments)]
        self.payment_date = date_tz

    def generate_indepent_move(self):
        if self.indepent_move_id:
            self.indepent_move_id.button_draft()
            self.indepent_move_id.action_change_name()
            self.indepent_move_id.unlink()
        if self.currency_id.name == 'PEN':
            if any(not l.product_id.account_destination_nc_id for l in self.line_id):
                raise UserError('Falta configurar cuenta de destino Soles en alguno de los productos de las lineas')
            Accounts = self.line_id.mapped('product_id.account_destination_nc_id')
        else:
            if any(not l.product_id.account_destination_fc_id for l in self.line_id):
                raise UserError('Falta configurar cuenta de destino Dolares en alguno de los productos de las lineas')
            Accounts = self.line_id.mapped('product_id.account_destination_fc_id')
        lines = []
        debit_amount, credit_amount = 0, 0
        global_cr = 1
        for acc in Accounts:
            if self.currency_id.name == 'PEN':
                Lines = self.line_id.filtered(lambda l: l.product_id.account_destination_nc_id == acc)
            else:
                Lines = self.line_id.filtered(lambda l: l.product_id.account_destination_fc_id == acc)
            partner = Lines.mapped('partner_id')[0]
            agent = Lines.mapped('agent_id')
            doc_number = Lines.mapped('doc_number')
            global_doc_number = doc_number
            if self.currency_id.name == 'PEN':
                currency_rate = 1
                amount = sum(Lines.mapped('amount'))
                amount_currency = 0
            else:
                currency_rate = self.currency_id._get_conversion_rate(self.currency_id, self.env.company.currency_id, self.env.company, self.payment_date if self.payment_date else fields.Date.today())
                global_cr = currency_rate
                amount_currency = sum(Lines.mapped('amount'))
                amount = float_round(amount_currency * currency_rate, 2)

            lines.append((0, 0, {
                'debit': amount,
                'credit': 0,
                'account_id': acc.id,
                'partner_id': self.partner_id.id if not agent else agent[0].id,
                'currency_id': None if self.env.company.currency_id == self.currency_id else self.currency_id.id,
                'tc': currency_rate,
                'amount_currency': amount_currency,
                'type_document_id': self.type_document_id.id if self.type_document_id else None,
                'nro_comp': doc_number[0].name if doc_number else '',
                'name': 'Pago de Solicitud %s' % self.name,
                'request_id': self.id,
                'order_id': doc_number[0].id if doc_number else None,
            }))
            debit_amount += amount
        aux = sum(self.line_id.mapped('amount'))
        if self.currency_id.name == 'PEN':
            total = aux
            total_currency = 0
            for line in self.line_id:
                line.payment_total = total
        else:
            total = float_round(aux * global_cr, 2)
            total_currency = aux
            for line in self.line_id:
                line.payment_total = total_currency
        total_line = {
            'debit': 0,
            'credit': total,
            'account_id': self.journal_id.default_credit_account_id.id,
            'partner_id': self.partner_id.id,
            'currency_id': None if self.env.company.currency_id == self.currency_id else self.currency_id.id,
            'tc': global_cr,
            'amount_currency': -total_currency,
            'type_document_id': self.type_document_id.id if self.type_document_id else None,
            'nro_comp': self.op_number,
            'date_maturity': self.date_due,
            'name': 'Pago de Solicitud %s' % self.name,
            'request_id': self.id,
            'order_id': global_doc_number[0].id if global_doc_number else None,
        }
        credit_amount = total
        lines.append((0, 0, total_line))
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        if not MainParameter.adjust_account_id:
            raise UserError('No se ha configurado una cuenta de ajuste en Parametros Principales de Contabilidad en la pestaña Solicitud de Pago')
        difference = debit_amount - credit_amount
        if difference != 0:
            if debit_amount > credit_amount:
                extra_line = {
                    'account_id': MainParameter.adjust_account_id.id,
                    'debit': 0,
                    'credit': abs(difference),
                    'name': 'Ajuste por redondeo',
                }
            else:
                extra_line = {
                    'account_id': MainParameter.adjust_account_id.id,
                    'debit': abs(difference),
                    'credit': 0,
                    'name': 'Ajuste por redondeo',
                }
            lines.append((0, 0, extra_line))

        Move = self.env['account.move'].create({
            'partner_id': self.partner_id.id,
            'glosa': self.communication,
            'date': self.payment_date if self.payment_date else fields.Date.today(),
            'invoice_date': self.issue_date if self.issue_date else fields.Date.today(),
            'type': 'entry',
            'ref': global_doc_number[0].name if global_doc_number else None,
            'currency_rate': global_cr,
            'journal_id': self.journal_id.id,
            'td_payment_id': self.catalog_payment_id.id if self.catalog_payment_id else None,
            'line_ids': lines,
        })
        Move.line_ids.filtered(lambda l: l.debit == 0 and l.credit == 0).unlink()
        Move.post()
        if self.type_payment == "A":
            for item in  Move.line_ids:
                if int(item.debit) > 0:
                    item.nro_comp = Move.name

        self.indepent_move_id = Move.id
        self.state = 'payed'
        return self.env['popup.it'].get_message('Se genero el asiento correctamente')

class PaymentRequestLine(models.Model):
    _name = "fxo.payment.request.line"
    
    name = fields.Char(string='Descripcion')
    id_loges = fields.Char(string='Id Loges')
    partner_id  = fields.Many2one(comodel_name='res.partner', string='Cliente')
    doc_type = fields.Many2one(comodel_name='sale.order.type', string='Tipo de documento')
    doc_number = fields.Many2one(comodel_name='sale.order',string=' Nro. de Operacion')
    internal_ref = fields.Char(related='doc_number.internal_ref',string='Referencia Interna')
    type_id = fields.Many2one(related='doc_number.type_id',comodel='sale.order.type',readonly=True)
    internal_ref_child = fields.Char(related='doc_number.internal_ref_child',string="#Referencia hija",readonly=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Producto')
    currency_id = fields.Many2one("res.currency", string="Moneda de pago")
    amount = fields.Float(string='Monto')
    payment_request_id = fields.Many2one(comodel_name='fxo.payment.request', string='Solicitud', ondelete='cascade')
    payment_id = fields.Many2one('account.payment', string='Pago')
    move_line_ids = fields.One2many('account.move.line', 'request_line_id', string='Facturas')



    amount_invoiced = fields.Float(compute='get_amount_invoiced', string='Total Sustentado')
    company_id = fields.Many2one('res.company', related='payment_request_id.company_id', store=True)
    agent_id = fields.Many2one('res.partner', string='Agente')

    @api.depends('move_line_ids')
    def get_amount_invoiced(self):
        for rec in self:
            if rec.move_line_ids:
                Lines = rec.move_line_ids.filtered(lambda l: l.move_id.state == 'posted')
                rec.amount_invoiced = sum(Lines.mapped('price_total'))
            else:
                rec.amount_invoiced = 0
    
class AccountPayment(models.Model):
    _inherit = 'account.payment'

    request_id = fields.Many2one('fxo.payment.request', string='Solicitud de Pago')
    request_line_id = fields.Many2one('fxo.payment.request.line', string='Linea de Solicitud')
    product_id = fields.Many2one('product.product', string='Producto')
    journal_code = fields.Char(related='journal_id.code', string='Codigo de Diario', store=True)

    def post(self):
        res = super(AccountPayment, self).post()
        Doc = self.env['einvoice.catalog.01'].search([('code', '=', '00')])
        for rec in self:
            if rec.request_id:
                rec.request_id.state = 'payed'
                for line in rec.move_line_ids:
                    line.request_id = rec.request_id.id
                    line.product_id = rec.product_id.id
                    line.type_document_id = Doc.id
                    line.nro_comp = rec.request_id.name
                    if line.credit > 0:
                        line.partner_id = rec.request_id.partner_id.id
                if not rec.type_document_id:
                    rec.type_document_id = Doc.id
                if not rec.nro_comp:
                    rec.nro_comp = rec.request_id.name
            if rec.request_line_id:
                rec.request_line_id.payment_total = rec.amount
            Moves = rec.mapped('move_line_ids.move_id')
            for move in Moves:
                move.currency_rate = rec.type_change
            if any(move.state == 'draft' for move in Moves):
                for move in Moves:
                    if move.state == 'draft':
                        move.post()
        return res

    def _prepare_payment_moves(self):
        all_move_vals = super(AccountPayment, self)._prepare_payment_moves()
        if self.order_id:
            for move_val in all_move_vals:
                for line in move_val['line_ids']:
                    line[2]['order_id'] = self.order_id.id 
        return all_move_vals

    def get_op_number_wizard(self):
        return {
            'name': 'Nro de Operacion de Caja',
            'type': 'ir.actions.act_window',
            'res_model': 'payment.op.wizard',
            'views': [(self.env.ref('fxo_payment_request.view_payment_op_wizard_form').id, 'form')],
            'context': self._context,
            'target': 'new'
        }

class AccountMove(models.Model):
    _inherit = 'account.move'

    request_id = fields.Many2one('fxo.payment.request', string='Solicitud de Pago')
    request_filter = fields.Boolean(string='Filtro por Solicitud + Producto')

    # def js_assign_outstanding_line(self, line_id):
    #     res = super(AccountMove, self).js_assign_outstanding_line(line_id)
    #     MoveLine = self.env['account.move.line'].browse(line_id)
    #     Lines = self.invoice_line_ids.filtered(lambda l: l.order_id)
    #     if MoveLine and Lines:
    #         for line in MoveLine.move_id.line_ids:
    #             if line.account_id.reconcile:
    #                 line.order_id = Lines[0].order_id.id
    #     return res

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        for line in res.line_ids:
            if line.product_id and line.product_id.expense_analytic_account_id:
                line.analytic_account_id = line.product_id.expense_analytic_account_id
        return res

    def action_post(self):
        res = super(AccountMove, self).action_post()
        lines_with = self.line_ids.filtered(lambda l: l.order_id)
        lines_without = self.line_ids.filtered(lambda l: not l.order_id)
        if lines_with and lines_without:
            for line in lines_without:
                line.order_id = lines_with[0].order_id.id
        if self.request_id.id :
            for item in self.line_ids:
                item.request_id = self.request_id.id 
        return res

    def action_assign_payments(self):
        log = ''
        moves = self.filtered(lambda inv: inv.state == 'posted' and inv.amount_residual > 0)
        if not moves:
            raise UserError('Las facturas seleccionadas no tienen monto para aplicar pagos o no estan publicadas revise los documentos seleccionados')
        for rec in moves:
            rec._compute_payments_widget_to_reconcile_info()
            out = json.loads(rec.invoice_outstanding_credits_debits_widget)
            if out:
                out_mapped = list(map(lambda x: x['amount'], out['content']))
                for line in list(map(lambda x: x['id'], out['content'])):
                    MoveLine = self.env['account.move.line'].browse(line)
                    if rec.amount_residual > 0:
                        currency_rate = rec.currency_id._get_conversion_rate(rec.currency_id, self.env.company.currency_id, self.env.company, fields.Date.today())
                        payment_date = fields.Date.today()
                        print('vars', currency_rate, payment_date)
                        rec.with_context({
                            'currency_rate': currency_rate,
                            'payment_date': payment_date,
                        }).js_assign_outstanding_line(line)
        return self.env['popup.it'].get_message('Se aplicaron los pagos correctamente')

    def get_move_line_domain(self, vals):
        domain = super(AccountMove, self).get_move_line_domain(vals)
        if vals['move'].request_id:
            if vals['move'].request_filter:
                Products = vals['move'].mapped('invoice_line_ids.product_id')
                domain = [
                    '|', ('account_id', 'in', vals['pay_term_line_ids'].mapped('account_id').ids),
                    ('account_id', 'in', vals['advance_payment_account_id']),
                    ('request_id', '=', vals['move'].request_id.id),
                    ('product_id', 'in', Products.ids),
                    '|', ('move_id.state', '=', 'posted'), '&', ('move_id.state', '=', 'draft'), ('journal_id.post_at', '=', 'bank_rec'),
                    ('reconciled', '=', False), '|', ('amount_residual', '!=', 0.0),
                    ('amount_residual_currency', '!=', 0.0),
                ]
            else:
                domain = [
                    '|', ('account_id', 'in', vals['pay_term_line_ids'].mapped('account_id').ids),
                    ('account_id', 'in', vals['advance_payment_account_id']),
                    ('request_id', '=', vals['move'].request_id.id),
                    '|', ('move_id.state', '=', 'posted'), '&', ('move_id.state', '=', 'draft'), ('journal_id.post_at', '=', 'bank_rec'),
                    ('reconciled', '=', False), '|', ('amount_residual', '!=', 0.0),
                    ('amount_residual_currency', '!=', 0.0),
                ]
        return domain

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    request_id = fields.Many2one('fxo.payment.request', string='Solicitud de Pago', help='Solicitud de Pago para filtro de Aplicaciones de Debitos')
    matched_request_id = fields.Many2one('fxo.payment.request', string='Solicitud de Pago', help='Solicitud de Pago para referenciar Apuntes Contables libres')
    request_line_id = fields.Many2one('fxo.payment.request.line', string='Linea de Solicitud de Pago')