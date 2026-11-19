# -*- coding: utf-8 -*-
import re
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_round


def _invoice_type_selection(self):
    return self.env['account.move'].fields_get(['type_invoice'])['type_invoice']['selection']


class AccountLetrasPayment(models.Model):
    _inherit = 'account.letras.payment'

    letters_qty = fields.Integer(string='Number of Bills', default=1)
    days_first_due = fields.Integer(string='Days to First Due Date', default=15)
    days_between = fields.Integer(string='Days between Bills', default=15)
    first_letter_number = fields.Char(
        string='First Bill Number',
        help='Number of the first bill; the following ones are consecutive. '
             'Empty: reference of the exchange plus the index.')
    type_invoice = fields.Selection(
        selection=_invoice_type_selection, string='Invoice Type',
        compute='_compute_type_invoice', store=True,
        help='Invoice type of the first invoice of the exchange; it is copied to the bills.')
    total_invoices = fields.Float(string='Total Invoices', digits=(16, 2), compute='_compute_schedule_totals')
    total_letters = fields.Float(string='Total Bills', digits=(16, 2), compute='_compute_schedule_totals')
    schedule_difference = fields.Float(string='Difference', digits=(16, 2), compute='_compute_schedule_totals')

    @api.depends('factura_ids', 'factura_ids.move_id', 'factura_ids.move_id.type_invoice')
    def _compute_type_invoice(self):
        for rec in self:
            first = rec.factura_ids.filtered('move_id')[:1]
            rec.type_invoice = first.move_id.type_invoice or False

    @api.depends('type', 'factura_ids.imp_div', 'letras_manual_ids.imp_div')
    def _compute_schedule_totals(self):
        for rec in self:
            sign = rec._fxo_sign()
            rec.total_invoices = sign * sum(rec.factura_ids.mapped('imp_div'))
            rec.total_letters = -sign * sum(rec.letras_manual_ids.mapped('imp_div'))
            rec.schedule_difference = rec.total_invoices - rec.total_letters

    def _fxo_sign(self):
        """Sign of the invoices in the exchange: vendor invoices are entered as a
        positive amount (debit) and their bills negative (credit); customers the
        other way round."""
        return -1 if (self.type or self.env.context.get('default_type')) == 'out' else 1

    def _fxo_invoice_types(self):
        if (self.type or self.env.context.get('default_type')) == 'out':
            return ('out_invoice', 'out_refund')
        return ('in_invoice', 'in_refund')

    # ------------------------------------------------------------------
    def action_load_invoices(self):
        """Add every pending invoice of the partner that is not in the exchange yet."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Invoices can only be loaded in draft.'))
        if not self.partner_id:
            raise UserError(_('Select the partner first.'))
        moves = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'posted'),
            ('invoice_payment_state', '=', 'not_paid'),
            ('type', 'in', self._fxo_invoice_types()),
            ('id', 'not in', self.factura_ids.mapped('move_id').ids),
        ], order='invoice_date, id')
        if not moves:
            raise UserError(_('The partner has no other pending invoices.'))
        Line = self.env['account.letras.payment.factura']
        self.write({'factura_ids': [(0, 0, Line._fxo_vals_from_move(move, self._fxo_sign())) for move in moves]})
        return True

    def action_generate_schedule(self):
        """Create the bills from the parameters (as in the 19.0 exchange form)."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('The schedule can only be generated in draft.'))
        invoices = self.factura_ids.filtered('move_id')
        if not invoices:
            raise UserError(_('Select at least one invoice to exchange.'))
        if self.letters_qty <= 0:
            raise UserError(_('The number of bills must be greater than zero.'))
        if self.days_first_due <= 0:
            raise UserError(_('The days to the first due date must be greater than zero.'))
        if self.letters_qty > 1 and self.days_between <= 0:
            raise UserError(_('The days between bills must be greater than zero.'))
        if not self.date_exchange:
            raise UserError(_('Set the exchange date first.'))
        currencies = invoices.mapped('currency_id')
        if len(currencies) > 1:
            raise UserError(_('The invoices have different currencies (%s). Exchange one currency at a time.')
                            % ', '.join(currencies.mapped('name')))
        currency = currencies or self.company_id.currency_id
        total = float_round(self.total_invoices, precision_digits=2)
        if total <= 0:
            raise UserError(_('The total to exchange must be greater than zero. Check the column "Importe Div" '
                              'of the invoices.'))
        param = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)], limit=1)
        if not param:
            raise UserError(_('There are no Main Accounting Parameters for the company.'))
        foreign = currency.name != 'PEN'
        if self.type == 'out':
            account = param.customer_letter_account_fc if foreign else param.customer_letter_account_nc
        else:
            account = param.supplier_letter_account_fc if foreign else param.supplier_letter_account_nc
        if not account:
            raise UserError(_('Set the account of bills (%s) in the Main Accounting Parameters.') % currency.name)

        sign = -self._fxo_sign()          # bills have the opposite sign of the invoices
        rate = self.tipo_cambio or 1.0
        qty = self.letters_qty
        base_amount = float_round(total / qty, precision_digits=2)
        commands, accumulated, due = [(5, 0, 0)], 0.0, None
        for index in range(1, qty + 1):
            due = (self.date_exchange + timedelta(days=self.days_first_due)) if index == 1 \
                else due + timedelta(days=self.days_between)
            due_adjusted = due
            while due_adjusted.weekday() >= 5:      # never on Saturday / Sunday
                due_adjusted += timedelta(days=1)
            # The last bill absorbs the rounding difference
            amount = base_amount if index < qty else float_round(total - accumulated, precision_digits=2)
            accumulated += amount
            local = float_round(amount * rate, precision_digits=2) if foreign else amount
            commands.append((0, 0, {
                'nro_letra': self._fxo_letter_number(index),
                'currency_id': currency.id,
                'account_id': account.id,
                'expiration_date': due_adjusted,
                'imp_div': sign * amount,
                'debit': local if sign > 0 else 0.0,
                'credit': local if sign < 0 else 0.0,
                'tipo_cambio': rate,
                'partner_id': self.partner_id.id,
                'date_exchange': self.date_exchange,
                'type': self.type,
                'company_id': self.company_id.id,
                'type_invoice': self.type_invoice,
            }))
        self.write({'letras_manual_ids': commands})
        return True

    def crear_asiento(self):
        """Procesar: el asiento del canje (el de las letras) lleva el tipo de
        factura del canje, el mismo que se copio a cada letra."""
        res = super(AccountLetrasPayment, self).crear_asiento()
        for rec in self:
            if rec.asiento_id and rec.type_invoice and rec.asiento_id.type_invoice != rec.type_invoice:
                rec.asiento_id.write({'type_invoice': rec.type_invoice})
        return res

    def _fxo_letter_number(self, index):
        """Number of the bill ``index`` (1..n). With a first number ending in
        digits the following are consecutive (keeping the zero padding)."""
        self.ensure_one()
        first = (self.first_letter_number or '').strip()
        if first:
            match = re.match(r'^(.*?)(\d+)$', first)
            if match:
                prefix, digits = match.groups()
                return '%s%s' % (prefix, str(int(digits) + index - 1).zfill(len(digits)))
            return '%s-%02d' % (first, index)
        return '%s-%02d' % (self.reference or self.name or _('Bill'), index)


class AccountLetrasPaymentFactura(models.Model):
    _inherit = 'account.letras.payment.factura'

    type_invoice = fields.Selection(related='move_id.type_invoice', string='Invoice Type', readonly=True)

    @api.model
    def _fxo_vals_from_move(self, move, sign):
        refund = move.type in ('in_refund', 'out_refund')
        return {
            'move_id': move.id,
            'type_document_id': move.type_document_id.id,
            'imp_div': (-sign if refund else sign) * move.amount_residual,
        }

    @api.onchange('move_id')
    def _onchange_move_id_fxo(self):
        """The invoice brings its document type and its pending amount."""
        for line in self:
            if not line.move_id:
                continue
            vals = self._fxo_vals_from_move(line.move_id, line.letra_payment_id._fxo_sign())
            line.type_document_id = vals['type_document_id']
            if not line.imp_div:
                line.imp_div = vals['imp_div']


class AccountLetrasPaymentManual(models.Model):
    _inherit = 'account.letras.payment.manual'

    type_invoice = fields.Selection(selection=_invoice_type_selection, string='Invoice Type')

    @api.model_create_multi
    def create(self, vals_list):
        # A bill gets the invoice type of the first invoice of its exchange
        Payment = self.env['account.letras.payment']
        for vals in vals_list:
            if not vals.get('type_invoice') and vals.get('letra_payment_id'):
                vals['type_invoice'] = Payment.browse(vals['letra_payment_id']).type_invoice
        return super(AccountLetrasPaymentManual, self).create(vals_list)
