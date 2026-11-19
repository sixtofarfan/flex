# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import traceback
import logging
from odoo.exceptions import UserError
import calendar
from odoo.tools import format_date, float_round

_logger = logging.getLogger(__name__)


class GenerateInvoicesWizard(models.TransientModel):
    _name = "generate.invoices.wizard"

    def get_default_subscription_lines(self):
        subscription_line = self.env['sale.subscription.line']
        active_ids = self._context['active_ids']
        ids = subscription_line.search([('id', 'in', active_ids)])
        return ids

    subscription_line_ids = fields.Many2many('sale.subscription.line', 'sale_subscription_line_invoices_wizard_rel',
                                             'subscription_line_id',
                                             'wizard_id', string='Subscription Lines',
                                             default=get_default_subscription_lines)

    def generate_invoices(self):
        for subscription in self.subscription_line_ids.mapped('analytic_account_id'):
            self._recurring_create_invoice(subscription)
        return {
            'name': _('Facturas'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
        }

    def _recurring_create_invoice(self, subscription):
        invoices = self.env['account.move']
        if subscription:
            sub_data = subscription.read(fields=['id', 'company_id'])
            for company_id in set(data['company_id'][0] for data in sub_data):
                sub_ids = [s['id'] for s in sub_data if s['company_id'][0] == company_id]
                subs = subscription.with_context(company_id=company_id, force_company=company_id).browse(sub_ids)
                context_invoice = dict(self.env.context, type='out_invoice', company_id=company_id,
                                       force_company=company_id)
                for subscription in subs:
                    subscription = subscription[0]
                    try:
                        period = self._get_periods(subscription, self.subscription_line_ids)
                        invoice_values = dict()
                        invoice_values = self._prepare_invoice(subscription, period)
                        new_invoice = self.env['account.move'].with_context(context_invoice).create(invoice_values)
                        invoices += new_invoice
                        new_invoice.message_post_with_view(
                            'mail.message_origin_link',
                            values={'self': new_invoice, 'origin': subscription},
                            subtype_id=self.env.ref('mail.mt_note').id)
                    except Exception:
                        raise
        CustomLines = subscription.mapped('custom_invoice_line_ids')
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
        return invoices

    def _prepare_invoice_data(self, subscription, period):
        self.ensure_one()
        if 'force_company' in self.env.context:
            company = self.env['res.company'].browse(self.env.context['force_company'])
        else:
            company = subscription.company_id
        MainParameter = self.env['main.parameter'].search([('company_id', '=', company.id)], limit=1)
        if subscription.team_id:
            team_id = subscription.team_id.id
        if MainParameter.glosa:
            glosa = MainParameter.glosa
        else:
            raise UserError('No se ha configurado una glosa en Parametros Principales en la pestaña \
                Suscripcion en la compañia %s' % company.name)
        sale_order = self.env['sale.order'].search([('order_line.subscription_id', '=', subscription.id)],
                                                   order="id desc",
                                                   limit=1)
        fpos_id = self.env['account.fiscal.position'].get_fiscal_position(subscription.partner_id.id)
        addr = subscription.partner_id.address_get(['delivery', 'invoice'])

        return {
            'type': 'out_invoice',
            'partner_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'currency_id': subscription.pricelist_id.currency_id.id,
            'journal_id': subscription.journal_id.id,
            'type_document_id': subscription.type_document_id.id,
            'invoice_origin': subscription.code,
            'invoice_period_id': period.id,
            'glosa': glosa,
            'fiscal_position_id': fpos_id,
            'team_id': team_id,
            'collection_id': subscription.partner_id.collection_id.id,
            'serie_id': subscription.serie_id.id,
            'invoice_payment_term_id': sale_order.payment_term_id.id if sale_order else subscription.partner_id.property_payment_term_id.id,
            'narration': _("This invoice covers the following period: %s - %s") % (
                format_date(self.env, period.date_start), format_date(self.env, period.date_end)),
            'invoice_user_id': subscription.user_id.id,
        }

    def _prepare_invoice_lines(self, subscription, period):
        self.ensure_one()
        array_res = []
        SubLines = self.subscription_line_ids.filtered(lambda
                                                           t: t.analytic_account_id.id == subscription.id)
        for line in SubLines:
            array = []
            discount_dict = self.discount_process(line, subscription)
            '''
            if line.fees_number > 0:
                invoice_line = False
            else:
            '''
            if 1 == 1:
                if 'no_prom_total' in discount_dict and discount_dict['no_prom_total'] > 0:
                    inv_line = self._prepare_invoice_line(subscription, line, discount_dict['no_prom_total'],
                                                          discount_dict['no_prom_message'], period)
                    array.append((0, 0, inv_line))
                invoice_line = self._prepare_invoice_line(subscription, line, discount_dict['total'],
                                                          discount_dict['message'], period)
            MainParameter = self.env['main.parameter'].search([('company_id', '=', subscription.company_id.id)],
                                                              limit=1)
            if invoice_line and line.fees_number == 0:
                array.append((0, 0, invoice_line))
            elif invoice_line and line.fees_number > 0 and line.fees_to_invoice > 0:
                array.append((0, 0, invoice_line))
            array_res += array

        return array_res

    def discount_process(self, line, subscription):
        next_date = line.stop_date + relativedelta(days=1)  # Fecha de la próxima factura
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
        else:
            last_day = calendar.monthrange(stop_date.year, stop_date.month)[1]
            res_days = last_day - stop_date.day
            total = (line.price_unit / 30) * res_days

        if next_val == stop_val:
            last_day = calendar.monthrange(stop_date.year, stop_date.month)[1]
            last_date = date(stop_date.year, stop_date.month, last_day)

            message = '\nProrrateo del %s al %s\n%s' % (
                line.stop_date.strftime('%d/%m/%Y'), last_date.strftime('%d/%m/%Y') if last_date else '', message)
        MainParameter = self.env['main.parameter'].search([('company_id', '=', subscription.company_id.id)],
                                                          limit=1)
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

    def _prepare_invoice_line(self, subscription, line, total=0, message='', period=False):
        name = ''
        if line.price_unit > 0:
            MainParameter = self.env['main.parameter'].search([('company_id', '=', subscription.company_id.id)],
                                                              limit=1)
            if line.product_id.bool_qty_street and MainParameter.including_address_in_invoice:
                name = '{0}\r\n{1}\r\n{2}'.format(
                    line.name,
                    line.partner_street_destination.street if line.partner_street_destination else '',
                    line.partner_street_destination_header.street if line.partner_street_destination_header else '',
                )
            else:
                name = line.name
            vals = {
                'name': name + message if message else name + _(' - Corresponding to period: %s') % (period.name),
                'subscription_id': line.analytic_account_id.id,
                'price_unit': total if total else line.price_unit,
                'discount': 0 if line.date_prom_stop else line.discount,
                'quantity': line.quantity,
                'product_uom_id': line.uom_id.id,
                'product_id': line.product_id.id,
                'tax_ids': [(6, 0, line.product_id.taxes_id.filtered(
                    lambda t: t.company_id == line.analytic_account_id.company_id).ids)],
                'analytic_account_id': line.analytic_account_id.analytic_account_id.id,
                'subscription_start_date': line.stop_date,
                'subscription_end_date': line.stop_date,
                'circuit_number': line.circuit_number,
                'service_id': line.service_id if line.service_id else '',
                'partner_street_destination': line.partner_street_destination.id if line.partner_street_destination else None,
                'partner_street_destination_header': line.partner_street_destination_header.id if line.partner_street_destination_header else None,
            }
            if line.fees_number > 0:
                vals['name'] = line.name + ' Cuota: %d/%d' % (len(line.move_line_ids) + 1, line.fees_number) + message
                vals['subscription_line_id'] = line.id
            return vals

    def _prepare_invoice(self, subscription, period):
        invoice = self._prepare_invoice_data(subscription, period)
        invoice['invoice_line_ids'] = self._prepare_invoice_lines(subscription, period)
        return invoice

    def _get_periods(self, subscription, subscription_line_ids):
        sub_lines = subscription_line_ids.filtered(lambda t: t.analytic_account_id.id == subscription.id)
        period = sub_lines[0].period_report_id
        return period
