# -*- coding: utf-8 -*-

import logging
import traceback

from ast import literal_eval
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import ustr
from odoo.tools import float_round
from dateutil.relativedelta import relativedelta
import datetime, calendar
from datetime import date, timedelta

_logger = logging.getLogger(__name__)


class res_partner(models.Model):
    _inherit = 'res.partner'

    serie_id_default = fields.Many2one('it.invoice.serie', 'Serie para Facturacion')
    type_document_default = fields.Many2one('einvoice.catalog.01', 'Tipo Documento para Facturacion')


class account_move_line_extra(models.Model):
    _name = 'account.move.line.extra'

    move_id = fields.Many2one('account.move', 'Factura')
    product_id = fields.Many2one('product.product', 'Producto')
    name = fields.Char('Nombre')
    product_uom = fields.Many2one('uom.uom', 'UM')
    qty = fields.Float('Cantidad')
    price_unit = fields.Float('Precio Unitario')
    price_subtotal = fields.Float('Precio SubTotal')


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    circuit_number = fields.Char('Nro Circuito')
    subscription_line_id = fields.Many2one('sale.subscription.line')
    service_id = fields.Char(string='Service ID')
    partner_street_destination_header = fields.Many2one('res.partner', string='Direccion Cabecera')


class AccountMoveLineCustom(models.Model):
    _name = 'account.move.line.custom'
    _description = 'Account Move Line Custom'

    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note')], default=False, help="Technical field for UX purpose.")
    move_id = fields.Many2one('account.move', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Producto')
    name = fields.Char(string='Descripcion')
    account_id = fields.Many2one('account.account', string='Cuenta')
    quantity = fields.Float(string='Cantidad')
    product_uom_id = fields.Many2one('uom.uom', string='UdM')
    price_unit = fields.Float(string='Precio')
    discount = fields.Float(string='Desc.%')
    price_subtotal = fields.Float(string='Subtotal')
    circuit_number = fields.Char(string='Nro Circuito')
    tax_ids = fields.Many2many('account.tax', string='Impuestos')
    partner_street_destination = fields.Many2one(comodel_name='res.partner', string='Destination address')
    partner_street_destination_header = fields.Many2one(comodel_name='res.partner', string='Address Header')


class account_move(models.Model):
    _inherit = 'account.move'

    extra_lines_ids = fields.One2many('account.move.line.extra', 'move_id', 'Extra')
    custom_line_ids = fields.One2many('account.move.line.custom', 'move_id')

    @api.constrains('ref', 'type', 'type_document_id')
    def _check_duplicate_customer_reference(self):
        moves = self.filtered(lambda move: move.is_sale_document() and move.ref)
        if not moves:
            return

        self.env["account.move"].flush([
            "ref", "type", "invoice_date",
            "company_id", "type_document_id",
        ])

        self._cr.execute('''
            SELECT move2.id
            FROM account_move move
            INNER JOIN account_move move2 ON
                    move2.ref = move.ref
                    AND move2.type_document_id = move.type_document_id
                    AND move2.company_id = move.company_id
                    AND move2.type = move.type
                    AND move2.id != move.id
                    AND move2.state != 'draft'
                    AND move.state != 'draft'
            WHERE move.id IN %s
        ''', [tuple(moves.ids)])
        duplicated_moves = self.browse([r[0] for r in self._cr.fetchall()])
        if duplicated_moves:
            raise ValidationError(
                _('Referencia de cliente duplicada detectada. Probablemente registró dos veces la misma factura / factura rectificativa del cliente:\n%s') % "\n".join(
                    duplicated_moves.mapped(lambda m: "%(ref)s - %(type_document)s" % {'ref': m.ref,
                                                                                       'type_document': m.type_document_id.name})
                ))

    def _reverse_moves(self, default_values_list=None, cancel=False):
        moves = super(account_move, self)._reverse_moves(default_values_list=default_values_list, cancel=cancel)
        for move in moves:
            print('move', move)
            if self.custom_line_ids:
                for custom in self.custom_line_ids:
                    print('custom', custom)
                    val = {
                        'move_id': move.id,
                        'display_type': custom.display_type,
                        'product_id': custom.product_id.id if custom.product_id else None,
                        'name': custom.name if custom.name else '',
                        'account_id': custom.account_id.id if custom.account_id else None,
                        'quantity': custom.quantity if custom.quantity else 0,
                        'product_uom_id': custom.product_uom_id.id if custom.product_uom_id else None,
                        'price_unit': custom.price_unit if custom.price_unit else 0,
                        'discount': custom.discount if custom.discount else 0,
                        'tax_ids': [(6, 0, custom.tax_ids.ids)] if custom.tax_ids else None,
                        'price_subtotal': custom.price_subtotal if custom.price_subtotal else 0,
                        'circuit_number': custom.circuit_number if custom.circuit_number else 0,
                    }
                    print('val', val)
                    self.env['account.move.line.custom'].create(val)
        return moves


class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'

    def _prepare_default_values(self, move):
        default_values = super(AccountDebitNote, self)._prepare_default_values(move)
        Move = self.env['account.move'].browse(self._context.get('active_id'))
        if Move.custom_line_ids:
            vals = []
            for custom in Move.custom_line_ids:
                print('custom', custom)
                val = {
                    'display_type': custom.display_type,
                    'product_id': custom.product_id.id if custom.product_id else None,
                    'name': custom.name if custom.name else '',
                    'account_id': custom.account_id.id if custom.account_id else None,
                    'quantity': custom.quantity if custom.quantity else 0,
                    'product_uom_id': custom.product_uom_id.id if custom.product_uom_id else None,
                    'price_unit': custom.price_unit if custom.price_unit else 0,
                    'discount': custom.discount if custom.discount else 0,
                    'tax_ids': [(6, 0, custom.tax_ids.ids)] if custom.tax_ids else None,
                    'price_subtotal': custom.price_subtotal if custom.price_subtotal else 0,
                    'circuit_number': custom.circuit_number if custom.circuit_number else 0,
                }
                vals.append((0, 0, val))
            default_values['custom_line_ids'] = vals
        default_values['doc_invoice_relac'] = [(0, 0, {
            'type_document_id': Move.type_document_id.id,
            'date': Move.invoice_date,
            'nro_comprobante': Move.ref,
            'amount_currency': Move.amount_total,
            'amount': Move.amount_total * Move.currency_rate,
            'bas_amount': Move.amount_untaxed * Move.currency_rate,
            'tax_amount': Move.amount_total * Move.currency_rate - Move.amount_untaxed * Move.currency_rate,
        })]
        return default_values


class ValidateAccountMove(models.TransientModel):
    _inherit = "validate.account.move"

    def validate_move(self):
        context = dict(self._context or {})
        moves = self.env['account.move'].browse(context.get('active_ids'))
        move_to_post = moves.filtered(lambda m: m.state == 'draft').sorted(lambda m: (m.date, m.ref or '', m.id))
        if not move_to_post:
            raise UserError(_('There are no journal items in the draft state to post.'))
        for i in move_to_post:
            i.action_post()
        return {'type': 'ir.actions.act_window_close'}


class sale_subscription_time_line(models.Model):
    _name = 'sale.subscription.time.line'
    _order = 'id desc'

    product_id = fields.Many2one('product.product', 'Producto')
    name = fields.Char('Descripcion')
    qty = fields.Float('cantidad Minutos')
    uom_id = fields.Many2one('uom.uom', 'Unid. Medida', relation='product_id.uom_id')
    price_unit = fields.Float('Precio Unitario')
    price_subtotal = fields.Float('Valor Venta')
    invoice_date = fields.Date('Fecha Facturación')
    state = fields.Selection([('draft', 'Borrador'), ('done', 'Facturado')], 'Estado', default='draft')
    subscription_id = fields.Many2one('sale.subscription', 'Subscription')


class sale_subscription_line(models.Model):
    _inherit = 'sale.subscription.line'

    circuit_number = fields.Char('Nro Circuito')
    stop_date = fields.Date('Fecha Finalizacion')
    move_line_ids = fields.One2many('account.move.line', 'subscription_line_id')
    fees_number = fields.Integer(string='Numero de Cuotas', compute=None)
    invoiced_fees = fields.Integer(string='Cuotas Facturadas', compute='get_invoiced_fees')
    fees_to_invoice = fields.Integer(string='Cuotas a Facturar', compute='get_fees_to_invoice')
    qty_months = fields.Integer(string='Numero de Meses')
    date_prom_stop = fields.Date(string='Fecha Fin Promocion', compute='get_date_prom_stop')
    currency_id = fields.Many2one(related='analytic_account_id.pricelist_id.currency_id', string='Currency', store=True)
    partner_id = fields.Many2one('res.partner', related='analytic_account_id.partner_id', store=True)

    @api.depends('discount', 'stop_date')
    def get_date_prom_stop(self):
        for rec in self:
            if rec.discount > 0 and rec.stop_date:
                rec.date_prom_stop = rec.stop_date + relativedelta(months=rec.qty_months) - timedelta(days=1)
            else:
                rec.date_prom_stop = None

    @api.depends('move_line_ids')
    def get_invoiced_fees(self):
        for rec in self:
            posted_lines = rec.move_line_ids.filtered(lambda l: l.move_id.state == 'posted')
            rec.invoiced_fees = len(posted_lines) if posted_lines else 0

    @api.depends('fees_number', 'invoiced_fees')
    def get_fees_to_invoice(self):
        for rec in self:
            rec.fees_to_invoice = rec.fees_number - rec.invoiced_fees


class sale_subscription(models.Model):
    _inherit = 'sale.subscription'

    minutes_adds = fields.Boolean('Tiene Minutos Adicionales', default=False)
    time_lines_ids = fields.One2many('sale.subscription.time.line', 'subscription_id', 'Minutos Adicionales')
    custom_invoice_line_ids = fields.One2many('sale.subscription.line.custom', 'analytic_account_id')
    type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo de Documento')
    serie_id = fields.Many2one('it.invoice.serie', string='Serie')
    journal_id = fields.Many2one('account.journal', string='Diario')
    client_order_ref = fields.Char('Doc.Referencia')
    date_due = fields.Date(string='Fecha Vencimiento',
                           help="Fecha de vencimiento, dato referencial sólo informativo para contratos de tipo indefinido que se factuará por siempre aún esté vencido")
    user2_id = fields.Many2one('res.users', string='Post-Venta', related='partner_id.user2_id')

    def recurring_invoice(self):
        res = super(sale_subscription, self).recurring_invoice()
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        if MainParameter.first_day_sub and self.invoice_count == 1:
            self.recurring_next_date = date(self.recurring_next_date.year, self.recurring_next_date.month, 1)
        if self.invoice_count == 0:
            self.recurring_next_date = self.date_start
        return res

    @api.model
    def create(self, vals):
        res = super(sale_subscription, self).create(vals)
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        if MainParameter.serie_control_ids:
            ControlLine = MainParameter.serie_control_ids.filtered(
                lambda l: res.partner_id.l10n_latam_identification_type_id in l.l10n_latam_identification_type_ids)
            if ControlLine and ControlLine.serie_id and ControlLine.journal_id and ControlLine.type_document_id:
                res.type_document_id = ControlLine.type_document_id.id
                res.serie_id = ControlLine.serie_id.id
                res.journal_id = ControlLine.journal_id.id
            else:
                raise UserError('No se ha encontrado una linea con el mismo tipo de documento del cliente \
                    en Parametros Principales en la pestaña Suscripciones en la compañia %s' % self.env.company.name)
        else:
            raise UserError('No se ha configurado lineas de serie en Parametros Principales en la pestaña \
                Suscripciones en la compañia %s' % self.env.company.name)
        res.recurring_next_date = res.date_start
        return res

    def _recurring_create_invoice(self, automatic=False):
        # self = self.filtered(lambda t: not t.minutes_adds)
        auto_commit = self.env.context.get('auto_commit', True)
        cr = self.env.cr
        invoices = self.env['account.move']
        current_date = datetime.date.today()
        imd_res = self.env['ir.model.data']
        template_res = self.env['mail.template']
        if len(self) > 0:
            if automatic:
                subscriptions = self.filtered(
                    lambda s: s.template_id.payment_mode != 'manual' and s.stage_id.in_progress)
            else:
                subscriptions = self
        else:
            domain = [('recurring_next_date', '<=', current_date), ('in_progress', '=', True)]
            subscriptions = self.search(domain)
        if subscriptions:
            sub_data = subscriptions.read(fields=['id', 'company_id'])
            for company_id in set(data['company_id'][0] for data in sub_data):
                sub_ids = [s['id'] for s in sub_data if s['company_id'][0] == company_id]
                subs = self.with_context(company_id=company_id, force_company=company_id).browse(sub_ids)
                context_invoice = dict(self.env.context, type='out_invoice', company_id=company_id,
                                       force_company=company_id)
                for subscription in subs:
                    subscription = subscription[
                        0]  # Trick to not prefetch other subscriptions, as the cache is currently invalidated at each iteration
                    if automatic and auto_commit:
                        cr.commit()
                    # payment + invoice (only by cron)
                    if subscription.template_id.payment_mode in ['validate_send_payment',
                                                                 'success_payment'] and subscription.recurring_total and automatic:
                        try:
                            payment_token = subscription.payment_token_id
                            tx = None
                            if payment_token:
                                # se crean los valores de la factura
                                invoice_values = subscription.with_context(
                                    lang=subscription.partner_id.lang)._prepare_invoice()
                                if 'invoice_line_ids' in invoice_values:
                                    if len(invoice_values['invoice_line_ids']) > 0:
                                        # se crea la factura
                                        new_invoice = self.env['account.move'].with_context(context_invoice).create(
                                            invoice_values)
                                        new_invoice.invoice_payment_term_id = self.partner_id.property_payment_term_id.id
                                        new_invoice.message_post_with_view(
                                            'mail.message_origin_link',
                                            values={'self': new_invoice, 'origin': subscription},
                                            subtype_id=self.env.ref('mail.mt_note').id)
                                        new_invoice.onchange_serie_id()
                                        new_invoice._get_currency_rate()
                                        tx = subscription._do_payment(payment_token, new_invoice, two_steps_sec=False)[
                                            0]
                                        # commit change as soon as we try the payment so we have a trace somewhere
                                        if auto_commit:
                                            cr.commit()
                                        if tx.renewal_allowed:
                                            subscription.send_success_mail(tx, new_invoice)
                                            msg_body = _(
                                                'Automatic payment succeeded. Payment reference: <a href=# data-oe-model=payment.transaction data-oe-id=%d>%s</a>; Amount: %s. Invoice <a href=# data-oe-model=account.move data-oe-id=%d>View Invoice</a>.') % (
                                                           tx.id, tx.reference, tx.amount, new_invoice.id)
                                            subscription.message_post(body=msg_body)
                                            if subscription.template_id.payment_mode == 'validate_send_payment':
                                                subscription.validate_and_send_invoice(new_invoice)
                                            if auto_commit:
                                                cr.commit()
                                        else:
                                            _logger.error('Fail to create recurring invoice for subscription %s',
                                                          subscription.code)
                                            if auto_commit:
                                                cr.rollback()
                                            new_invoice.unlink()
                            if tx is None or not tx.renewal_allowed:
                                amount = subscription.recurring_total
                                date_close = (
                                        subscription.recurring_next_date +
                                        relativedelta(days=subscription.template_id.auto_close_limit or
                                                           15)
                                )
                                close_subscription = current_date >= date_close
                                email_context = self.env.context.copy()
                                email_context.update({
                                    'payment_token': subscription.payment_token_id and subscription.payment_token_id.name,
                                    'renewed': False,
                                    'total_amount': amount,
                                    'email_to': subscription.partner_id.email,
                                    'code': subscription.code,
                                    'currency': subscription.pricelist_id.currency_id.name,
                                    'date_end': subscription.date,
                                    'date_close': date_close
                                })
                                if close_subscription:
                                    model, template_id = imd_res.get_object_reference('sale_subscription',
                                                                                      'email_payment_close')
                                    template = template_res.browse(template_id)
                                    template.with_context(email_context).send_mail(subscription.id)
                                    _logger.debug(
                                        "Sending Subscription Closure Mail to %s for subscription %s and closing subscription",
                                        subscription.partner_id.email, subscription.id)
                                    msg_body = _(
                                        'Automatic payment failed after multiple attempts. Subscription closed automatically.')
                                    subscription.message_post(body=msg_body)
                                    subscription.set_close()
                                else:
                                    model, template_id = imd_res.get_object_reference('sale_subscription',
                                                                                      'email_payment_reminder')
                                    msg_body = _('Automatic payment failed. Subscription set to "To Renew".')
                                    if (datetime.date.today() - subscription.recurring_next_date).days in [0, 3, 7, 14]:
                                        template = template_res.browse(template_id)
                                        template.with_context(email_context).send_mail(subscription.id)
                                        _logger.debug(
                                            "Sending Payment Failure Mail to %s for subscription %s and setting subscription to pending",
                                            subscription.partner_id.email, subscription.id)
                                        msg_body += _(' E-mail sent to customer.')
                                    subscription.message_post(body=msg_body)
                                    subscription.set_to_renew()
                            if auto_commit:
                                cr.commit()
                        except Exception:
                            if auto_commit:
                                cr.rollback()
                            # we assume that the payment is run only once a day
                            traceback_message = traceback.format_exc()
                            _logger.error(traceback_message)
                            last_tx = self.env['payment.transaction'].search([('reference', 'like',
                                                                               'SUBSCRIPTION-%s-%s' % (subscription.id,
                                                                                                       datetime.date.today().strftime(
                                                                                                           '%y%m%d')))],
                                                                             limit=1)
                            error_message = "Error during renewal of subscription %s (%s)" % (subscription.code,
                                                                                              'Payment recorded: %s' % last_tx.reference if last_tx and last_tx.state == 'done' else 'No payment recorded.')
                            _logger.error(error_message)
                            self.env['sale.subscription.log'].create({
                                'sale_subscription_id': subscription.id,
                                'error': 'Error durante la renovacion de la suscripcion. Pago Grabado: %s' % last_tx.reference if last_tx and last_tx.state == 'done' else 'No se guardo pago',
                                'date': fields.Datetime.now(),
                                'invoice_date': subscription.recurring_next_date,
                                'template_id': subscription.template_id.id,
                            })

                    # invoice only
                    elif subscription.template_id.payment_mode in ['manual'] and not automatic:
                        try:
                            invoice_values = subscription.with_context(
                                lang=subscription.partner_id.lang)._prepare_invoice()
                            if 'invoice_line_ids' in invoice_values:
                                if len(invoice_values['invoice_line_ids']) > 0:
                                    new_invoice = self.env['account.move'].with_context(context_invoice).create(
                                        invoice_values)
                                    new_invoice.invoice_payment_term_id = self.partner_id.property_payment_term_id.id
                                    new_invoice.message_post_with_view(
                                        'mail.message_origin_link',
                                        values={'self': new_invoice, 'origin': subscription},
                                        subtype_id=self.env.ref('mail.mt_note').id)
                                    invoices += new_invoice
                                    next_date = subscription.recurring_next_date or current_date
                                    rule, interval = subscription.recurring_rule_type, subscription.recurring_interval
                                    new_date = subscription._get_recurring_next_date(rule, interval, next_date,
                                                                                     subscription.recurring_invoice_day)
                                    # When `recurring_next_date` is updated by cron or by `Generate Invoice` action button,
                                    # write() will skip resetting `recurring_invoice_day` value based on this context value
                                    subscription.with_context(skip_update_recurring_invoice_day=True).write(
                                        {'recurring_next_date': new_date})
                                    if subscription.template_id.payment_mode == 'validate_send':
                                        subscription.validate_and_send_invoice(new_invoice)
                                    if automatic and auto_commit:
                                        cr.commit()
                        except Exception:
                            if automatic and auto_commit:
                                cr.rollback()
                                _logger.exception('Fail to create recurring invoice for subscription %s',
                                                  subscription.code)
                                self.env['sale.subscription.log'].create({
                                    'sale_subscription_id': subscription.id,
                                    'error': 'Fallo al crear Factura para la Suscripcion',
                                    'date': fields.Datetime.now(),
                                    'invoice_date': subscription.recurring_next_date,
                                    'template_id': subscription.template_id.id,
                                })
                            else:
                                raise
                    elif subscription.template_id.payment_mode in ['draft_invoice', 'validate_send']:
                        try:
                            invoice_values = subscription.with_context(
                                lang=subscription.partner_id.lang)._prepare_invoice()
                            if 'invoice_line_ids' in invoice_values:
                                if len(invoice_values['invoice_line_ids']) > 0:
                                    # del invoice_values['collection_id']
                                    # del invoice_values['invoice_period_id']
                                    new_invoice = self.env['account.move'].with_context(context_invoice).create(
                                        invoice_values)
                                    new_invoice.message_post_with_view(
                                        'mail.message_origin_link',
                                        values={'self': new_invoice, 'origin': subscription},
                                        subtype_id=self.env.ref('mail.mt_note').id)
                                    invoices += new_invoice
                                    next_date = subscription.recurring_next_date or current_date
                                    rule, interval = subscription.recurring_rule_type, subscription.recurring_interval
                                    new_date = subscription._get_recurring_next_date(rule, interval, next_date,
                                                                                     subscription.recurring_invoice_day)
                                    # When `recurring_next_date` is updated by cron or by `Generate Invoice` action button,
                                    # write() will skip resetting `recurring_invoice_day` value based on this context value
                                    subscription.with_context(skip_update_recurring_invoice_day=True).write(
                                        {'recurring_next_date': new_date})
                                    if subscription.template_id.payment_mode == 'validate_send':
                                        subscription.validate_and_send_invoice(new_invoice)
                                    if automatic and auto_commit:
                                        cr.commit()
                        except Exception:
                            if automatic and auto_commit:
                                cr.rollback()
                                _logger.exception('Fail to create recurring invoice for subscription %s',
                                                  subscription.code)
                                self.env['sale.subscription.log'].create({
                                    'sale_subscription_id': subscription.id,
                                    'error': 'Fallo al crear Factura para la Suscripcion',
                                    'date': fields.Datetime.now(),
                                    'invoice_date': subscription.recurring_next_date,
                                    'template_id': subscription.template_id.id,
                                })
                            else:
                                raise
        # buscar las lneas de la pestaña apuntes Contables
        CustomLines = subscriptions.mapped('custom_invoice_line_ids')
        for i in invoices:
            if not i.invoice_line_ids or i.amount_total == 0:
                i.unlink()
                continue
            c_lines = CustomLines.filtered(lambda l: l.analytic_account_id.code == i.invoice_origin)
            for c_line in c_lines:
                if c_line:
                    line = {
                        'move_id': i.id,
                        'product_id': c_line.product_id.id,
                        'account_id': c_line.product_id.property_account_income_id.id if c_line.product_id.property_account_income_id else None,
                        'name': c_line.name,
                        'quantity': c_line.quantity,
                        'product_uom_id': c_line.uom_id.id,
                        'price_unit': c_line.price_unit,
                        'discount': c_line.discount,
                        'price_subtotal': c_line.price_subtotal,
                        'circuit_number': c_line.circuit_number,
                        'tax_ids': [(6, 0, c_line.product_id.taxes_id.ids)],
                    }
                    self.env['account.move.line.custom'].create(line)
            MainParameter = self.env['main.parameter'].search([('company_id', '=', i.company_id.id)], limit=1)
            sus = None
            total = 0
            if len(i.line_ids) > 0:
                for lineas_invoice in i.line_ids:
                    if lineas_invoice.subscription_id.id:
                        sus = lineas_invoice.subscription_id
                    total += lineas_invoice.debit
                if MainParameter.product_invoices.id and MainParameter.name_product_invoices:
                    data = {
                        'move_id': i.id,
                        'product_id': MainParameter.product_invoices.id,
                        'name': MainParameter.name_product_invoices,
                        'product_uom': MainParameter.product_invoices.uom_id.id,
                        'qty': 1,
                        'price_unit': total,
                        'price_subtotal': total,
                    }
                    self.env['account.move.line.extra'].create(data)
            i.onchange_serie_id()
            i._get_currency_rate()
        # for i in self:
        #	i.recurring_next_date = i.recurring_next_date - datetime.timedelta(days=i.recurring_next_date.day-1)
        return invoices

    # TODO Encontrar mejor manera sin sobre escribir la función
    # con esto se puede obtener el siguiente numero, se envia a nubefact
    # y se agregan los archivos pdf y xml al mail
    # Ing. Jean Paul Casis
    def validate_and_send_invoice(self, invoice):
        self.ensure_one()
        if invoice.state != 'posted':
            invoice.post()
        email_context = self.env.context.copy()
        email_context.update({
            'total_amount': invoice.amount_total,
            'email_to': self.partner_id.email,
            'code': self.code,
            'currency': self.pricelist_id.currency_id.name,
            'date_end': self.date,
        })

        # ************* Agregado a la nueva función ****************
        # estas son funciones que ya existen y deben tener su dependencia
        next_number = self.serie_id.sequence_id.next_by_id()
        if not self.serie_id.sequence_id.prefix:
            raise UserError("No existe un prefijo configurado en la secuencia de la serie.")
        invoice.ref = next_number
        invoice.send_ebill()
        if invoice.xml_version:
            vals = invoice.get_xml_vals()
            email_context.update(vals)

        if invoice.serie_id.is_cpe and invoice.pe_cpe_id:
            vals = invoice.get_cpe_vals()
            email_context.update(vals)
        # **********************************************************

        _logger.debug("Sending Invoice Mail to %s for subscription %s", self.partner_id.email, self.id)
        self.template_id.invoice_mail_template_id.with_context(email_context).send_mail(invoice.id)
        invoice.invoice_sent = True
        if hasattr(invoice, "attachment_ids") and invoice.attachment_ids:
            invoice._message_set_main_attachment_id([(4, id) for id in invoice.attachment_ids.ids])

    def _prepare_invoice_data(self):
        res = super(sale_subscription, self)._prepare_invoice_data()
        if 'force_company' in self.env.context:
            company = self.env['res.company'].browse(self.env.context['force_company'])
        else:
            company = self.company_id
        MainParameter = self.env['main.parameter'].search([('company_id', '=', company.id)], limit=1)
        res['type_document_id'] = self.type_document_id.id
        res['serie_id'] = self.serie_id.id
        res['journal_id'] = self.journal_id.id
        res['collection_id'] = self.partner_id.collection_id.id
        if self.team_id:
            res['team_id'] = self.team_id.id
        if self.recurring_next_date:
            Period = self.env['account.period'].search([
                ('date_start', '<=', self.recurring_next_date),
                ('date_end', '>=', self.recurring_next_date),
                ('is_opening_close', '=', False)
            ])
            if Period:
                res['invoice_period_id'] = Period.id
            else:
                raise UserError('No se ha encontrado periodo para la fecha {0}'.format(self.recurring_next_date))
        if MainParameter.glosa:
            res['glosa'] = MainParameter.glosa
        else:
            raise UserError('No se ha configurado una glosa en Parametros Principales en la pestaña \
                Suscripcion en la compañia %s' % company.name)
        return res

    def discount_process(self, line):
        # Function to get discount based on billing method
        next_date = line.analytic_account_id.recurring_next_date  # Fecha de la próxima factura
        stop_date = line.stop_date  # Fecha de instalacion
        prom_date = line.date_prom_stop  # Fehca fin de Promocion
        last_date = None
        message = no_prom_message = ''
        next_val = stop_val = total = prom_val = no_prom_total = 0
        if next_date and stop_date:
            next_val = next_date.year + next_date.month
            stop_val = stop_date.year + stop_date.month
        if prom_date:
            prom_val = prom_date.year + prom_date.month
        if line.discount > 0 and stop_date and next_date:
            if next_val == stop_val:
                last_day = calendar.monthrange(stop_date.year, stop_date.month)[1]
                last_date = date(stop_date.year, stop_date.month, last_day)
                res_days = last_day - stop_date.day
                total = (line.price_unit / 30) * res_days * (line.discount / 100)  # 100 %30 = 70
                message = 'Promocion {0}%'.format(line.discount)
            elif next_val > stop_val and next_val == prom_val and prom_date:
                last_day = calendar.monthrange(prom_date.year, prom_date.month)[1]
                last_date = date(prom_date.year, prom_date.month, last_day)
                prom_days = abs((prom_date - next_date).days + 1)
                no_prom_days = last_day - prom_days
                total = (line.price_unit / 30) * prom_days * (line.discount / 100)
                no_prom_total = (line.price_unit / 30) * no_prom_days
                message = 'Servicio con {0} dias Promocion {1}%\n'.format(prom_days, line.discount)
                no_prom_message = 'Servicio sin promocion {0} dias: {1}'.format(no_prom_days,
                                                                                float_round(no_prom_total, 2))

        if next_val == stop_val:
            last_day = calendar.monthrange(stop_date.year, stop_date.month)[1]
            last_date = date(stop_date.year, stop_date.month, last_day)

            message = '\nProrrateo del %s al %s\n%s' % (
                line.stop_date.strftime('%d/%m/%Y'), last_date.strftime('%d/%m/%Y') if last_date else '', message)
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)], limit=1)
        val = {
            'message': message if message else '',
            'total': total if total else 0,
        }
        if MainParameter.billing_method == 'first':
            val.update({
                'no_prom_total': no_prom_total if no_prom_total else 0,
                'no_prom_message': no_prom_message if no_prom_message else '',
            })
        return val

    # funcion que crea las lineas de factura
    def _prepare_invoice_lines(self, fiscal_position):
        self.ensure_one()
        revenue_date_start = self.recurring_next_date
        periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
        revenue_date_stop = revenue_date_start + relativedelta(
            **{periods[self.recurring_rule_type]: self.recurring_interval}) - relativedelta(days=1)
        array_res = []
        SubLines = []
        if not self.template_id.custom_template:
            SubLines = self.recurring_invoice_line_ids.filtered(lambda t: t.state == 'done')
        else:
            SubLines = self.custom_invoice_line_ids

        if self.recurring_next_date:
            Period = self.env['account.period'].search([
                ('date_start', '<=', self.recurring_next_date),
                ('date_end', '>=', self.recurring_next_date),
                ('is_opening_close', '=', False)
            ])
            if Period:
                period_id = Period.id
            else:
                raise UserError('No se ha encontrado periodo para la fecha {0}'.format(self.recurring_next_date))

        # recorrer las lineas de facturas

        for line in SubLines:
            # verifico si el servicio fue facturado o no en el periodo
            is_invoice = self._check_line_to_invoiced(line, period_id)
            if is_invoice is False:
                array = []
                if not self.template_id.custom_template and not line.stop_date and line.price_unit > 0:
                    raise UserError('Las lineas en estado Activo necesitan una fecha de finalizacion')
                if not self.template_id.custom_template and not line.stop_date and line.price_unit == 0:
                    continue
                if not self.template_id.custom_template:
                    revenue_date_start = line.stop_date
                    last_day = calendar.monthrange(line.stop_date.year, line.stop_date.month)[1]
                    last_date = datetime.date(line.stop_date.year, line.stop_date.month, last_day)
                revenue_date_stop = revenue_date_start + relativedelta(
                    **{periods[self.recurring_rule_type]: self.recurring_interval}) - relativedelta(days=1)
                discount_dict = self.discount_process(line)
                '''
                if line.fees_number > 0:
                    invoice_line = False
                else:
                '''
                if 1 == 1:
                    if 'no_prom_total' in discount_dict and discount_dict['no_prom_total'] > 0:
                        inv_line = self._prepare_invoice_line(line, fiscal_position, revenue_date_start,
                                                              revenue_date_stop,
                                                              discount_dict['no_prom_total'],
                                                              discount_dict['no_prom_message'])
                        array.append((0, 0, inv_line))
                    invoice_line = self._prepare_invoice_line(line, fiscal_position, revenue_date_start,
                                                              revenue_date_stop,
                                                              discount_dict['total'], discount_dict['message'])
                MainParameter = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)], limit=1)
                if invoice_line and line.fees_number == 0:
                    array.append((0, 0, invoice_line))
                elif invoice_line and line.fees_number > 0 and line.fees_to_invoice > 0:
                    array.append((0, 0, invoice_line))

                # if line.product_id.id == 5389:
                #    raise ValidationError('holi'+str(array))
                if (self.recurring_next_date - revenue_date_start).days < 30 and \
                        self.template_id.calculate_upsell and \
                        not self.template_id.custom_template:
                    price_unit = (line.price_unit * (
                        1 if revenue_date_start.day == 1 else ((last_day - revenue_date_start.day) / 30))) or 0.0
                    if line.fees_number > 0:
                        price_unit = line.price_unit
                    discount_dict = self.discount_process(line)
                    val = {
                        'name': line.product_id.display_name if line.fees_number > 0 else line.product_id.display_name + ' ' +
                                                                                          discount_dict['message'],
                        'subscription_id': line.analytic_account_id.id,
                        'price_unit': float_round(discount_dict['total'], 2) if discount_dict['total'] else price_unit,
                        'discount': 0 if discount_dict['total'] else line.discount,
                        'quantity': line.quantity,
                        'product_uom_id': line.product_id.uom_id.id,
                        'product_id': line.product_id.id,
                        'tax_ids': [(6, 0, line.product_id.taxes_id.filtered(
                            lambda t: t.company_id == line.analytic_account_id.company_id).ids)],
                        'analytic_account_id': line.analytic_account_id.analytic_account_id.id,
                        'subscription_start_date': revenue_date_start,
                        'subscription_end_date': revenue_date_stop,
                        'circuit_number': line.circuit_number,
                        'service_id': line.service_id if line.service_id else '',
                        'partner_street_destination': line.partner_street_destination.id if line.partner_street_destination else None,
                        'partner_street_destination_header': line.partner_street_destination_header.id if line.partner_street_destination_header else None,
                    }
                    # agregar si el metodo de facturacion es segun el periodo de facturacion
                    if price_unit > 0 and MainParameter.billing_method == 'period':
                        array.append((0, 0, val))
                    # agregar si el metodo de facturacion es desde el primer dia de facturacion
                    if price_unit > 0 and MainParameter.billing_method == 'first':
                        next_date = line.analytic_account_id.recurring_next_date  # Fecha de la próxima factura
                        stop_date = line.stop_date  # Fecha de instalacion
                        next_val = next_date.year + next_date.month
                        stop_val = stop_date.year + stop_date.month
                        if next_val == stop_val:
                            array = []
                            array.append((0, 0, val))
                array_res += array

        return array_res

    def _prepare_invoice_line(self, line, fiscal_position, date_start=False, date_stop=False, total=0, message=''):
        name = ''
        if line.price_unit > 0:
            MainParameter = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)], limit=1)
            if line.product_id.bool_qty_street and MainParameter.including_address_in_invoice:
                name = '{0}\r\n{1}\r\n{2}'.format(
                    line.name,
                    line.partner_street_destination.street if line.partner_street_destination else '',
                    line.partner_street_destination_header.street if line.partner_street_destination_header else '',
                )
            else:
                name = line.name
            if (
                    line.discount > 0 and line.date_prom_stop and line.analytic_account_id.recurring_next_date < line.date_prom_stop):
                flag = True
            else:
                flag = False
            vals = {
                'name': name + message if flag else name,
                'subscription_id': line.analytic_account_id.id,
                'price_unit': total if total else line.price_unit,
                'discount': 0 if line.date_prom_stop else line.discount,
                'quantity': line.quantity,
                'product_uom_id': line.uom_id.id,
                'product_id': line.product_id.id,
                'tax_ids': [(6, 0, line.product_id.taxes_id.filtered(
                    lambda t: t.company_id == line.analytic_account_id.company_id).ids)],
                'analytic_account_id': line.analytic_account_id.analytic_account_id.id,
                'subscription_start_date': date_start,
                'subscription_end_date': date_stop,
                'circuit_number': line.circuit_number,
                'service_id': line.service_id if line.service_id else '',
                'partner_street_destination': line.partner_street_destination.id if line.partner_street_destination else None,
                'partner_street_destination_header': line.partner_street_destination_header.id if line.partner_street_destination_header else None,
            }
            if line.fees_number > 0:
                vals['name'] = line.name + ' Cuota: %d/%d' % (len(line.move_line_ids) + 1, line.fees_number) + message
                vals['subscription_line_id'] = line.id
            return vals

    @api.model
    def _get_recurring_next_date(self, interval_type, interval, current_date, recurring_invoice_day):
        periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
        interval_type = periods[interval_type]
        # busco si existen items en estado pendiente
        recurring_invoice_line_ids = self.recurring_invoice_line_ids.filtered(lambda line: line.state == 'pending')
        # entra al if si se encuentran items en estado pendiente
        if len(recurring_invoice_line_ids) > 0:
            # si dia actual no es el primer dia del mes entonces, no modifico la fecha proxima de factura
            if date.today().day != 1:
                return current_date
            else:
                # en caso de que sea dia primero aplico el desarrollo base del modulo sale_subscription
                recurring_next_date = fields.Date.from_string(current_date) + relativedelta(**{interval_type: interval})
                if interval_type == 'months':
                    last_day_of_month = recurring_next_date + relativedelta(day=31)
                    if last_day_of_month.day >= recurring_invoice_day:
                        return recurring_next_date.replace(day=recurring_invoice_day)
                    return last_day_of_month
                return recurring_next_date
        else:
            # en caso de que no se encuentren items pendientes aplico el desarrollo base del modulo sale_subscription
            recurring_next_date = fields.Date.from_string(current_date) + relativedelta(**{interval_type: interval})
            if interval_type == 'months':
                last_day_of_month = recurring_next_date + relativedelta(day=31)
                if last_day_of_month.day >= recurring_invoice_day:
                    return recurring_next_date.replace(day=recurring_invoice_day)
                return last_day_of_month
            return recurring_next_date

    def _check_line_to_invoiced(self, line, period_id):
        flag = True
        sql_query = """
            SELECT aml.service_id from account_move_line aml
                LEFT JOIN res_company rc ON (aml.company_id=rc.id)
                LEFT JOIN account_move am ON (am.id = aml.move_id)
                LEFT JOIN account_period ap ON (ap.id = am.invoice_period_id)
                where am.invoice_period_id = %d and rc.id=%d and aml.service_id = %s
        """ % (period_id, self.env.company.id, "'" + line.service_id + "'")
        self._cr.execute(sql_query)
        service_ids = self._cr.dictfetchall()
        if len(service_ids) == 0:
            flag = False
        return flag


class SaleSubscriptionLog(models.Model):
    _name = "sale.subscription.log"
    _description = "Sale Subscription Log"

    sale_subscription_id = fields.Many2one('sale.subscription', string='Suscripcion')
    error = fields.Char(string='Tipo de Error')
    date = fields.Datetime(string='Fecha')
    invoice_date = fields.Date(string='Fecha Proxima Facturacion')
    template_id = fields.Many2one('sale.subscription.template', string='Plantilla de la Suscripcion')


class SaleSubscriptionTemplate(models.Model):
    _inherit = 'sale.subscription.template'

    calculate_upsell = fields.Boolean(string='Calcular Prorrateo', default=True)
    custom_template = fields.Boolean(string='Plantilla Personalizada', default=False)


class SaleSubscriptionLineCustom(models.Model):
    _name = 'sale.subscription.line.custom'

    product_id = fields.Many2one(
        'product.product', string='Product', check_company=True,
        domain="[('recurring_invoice','=',True)]", required=True)
    analytic_account_id = fields.Many2one('sale.subscription', string='Subscription')
    company_id = fields.Many2one('res.company', related='analytic_account_id.company_id', stored=True, index=True)
    name = fields.Text(string='Description', required=True)
    quantity = fields.Float(string='Quantity', help="Quantity that will be invoiced.", default=1.0)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True,
                             domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price')
    discount = fields.Float(string='Discount (%)', digits='Discount')
    price_subtotal = fields.Float(compute='_compute_price_subtotal', string='Subtotal', digits='Account', store=True)
    circuit_number = fields.Char(string='Nro Circuito')
    fees_number = fields.Integer()
    invoiced_fees = fields.Integer()
    fees_to_invoice = fields.Integer()
    service_id = fields.Char()
    partner_street_destination = fields.Many2one('res.partner')
    partner_street_destination_header = fields.Many2one('res.partner')

    @api.depends('price_unit', 'quantity', 'discount', 'analytic_account_id.pricelist_id')
    def _compute_price_subtotal(self):
        AccountTax = self.env['account.tax']
        for line in self:
            price = AccountTax._fix_tax_included_price(line.price_unit, line.product_id.sudo().taxes_id, AccountTax)
            line.price_subtotal = line.quantity * price * (100.0 - line.discount) / 100.0
            if line.analytic_account_id.pricelist_id.sudo().currency_id:
                line.price_subtotal = line.analytic_account_id.pricelist_id.sudo().currency_id.round(
                    line.price_subtotal)

    @api.onchange('product_id')
    def onchange_product_id(self):
        product = self.product_id
        partner = self.analytic_account_id.partner_id
        if partner.lang:
            product = product.with_context(lang=partner.lang)

        self.name = product.get_product_multiline_description_sale()

    @api.onchange('product_id', 'quantity')
    def onchange_product_quantity(self):
        subscription = self.analytic_account_id
        company_id = subscription.company_id.id
        pricelist_id = subscription.pricelist_id.id
        context = dict(self.env.context, company_id=company_id, force_company=company_id, pricelist=pricelist_id,
                       quantity=self.quantity)
        if not self.product_id:
            self.price_unit = 0.0
        else:
            partner = subscription.partner_id.with_context(context)
            if partner.lang:
                context.update({'lang': partner.lang})

            product = self.product_id.with_context(context)
            self.price_unit = product.price

            if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = product.uom_id.id
            if self.uom_id.id != product.uom_id.id:
                self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)

    @api.onchange('uom_id')
    def onchange_uom_id(self):
        if not self.uom_id:
            self.price_unit = 0.0
        else:
            return self.onchange_product_quantity()

    def get_template_option_line(self):
        """ Return the account.analytic.invoice.line.option which has the same product_id as
        the invoice line"""
        if not self.analytic_account_id and not self.analytic_account_id.template_id:
            return False
        template = self.analytic_account_id.template_id
        return template.sudo().subscription_template_option_ids.filtered(lambda r: r.product_id == self.product_id)

    def _amount_line_tax(self):
        self.ensure_one()
        val = 0.0
        product = self.product_id
        product_tmp = product.sudo().product_tmpl_id
        for tax in product_tmp.taxes_id.filtered(lambda t: t.company_id == self.analytic_account_id.company_id):
            fpos_obj = self.env['account.fiscal.position']
            partner = self.analytic_account_id.partner_id
            fpos_id = fpos_obj.with_context(force_company=self.analytic_account_id.company_id.id).get_fiscal_position(
                partner.id)
            fpos = fpos_obj.browse(fpos_id)
            if fpos:
                tax = fpos.map_tax(tax, product, partner)
            compute_vals = tax.compute_all(self.price_unit * (1 - (self.discount or 0.0) / 100.0),
                                           self.analytic_account_id.currency_id, self.quantity, product, partner)[
                'taxes']
            if compute_vals:
                val += compute_vals[0].get('amount', 0)
        return val

    @api.model
    def create(self, values):
        if values.get('product_id') and not values.get('name'):
            line = self.new(values)
            line.onchange_product_id()
            values['name'] = line._fields['name'].convert_to_write(line['name'], line)
        return super(SaleSubscriptionLineCustom, self).create(values)
