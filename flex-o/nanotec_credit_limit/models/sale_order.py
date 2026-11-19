# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
from odoo import exceptions
from datetime import datetime, timedelta
from datetime import date
import logging

_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _

class SaleOrder(models.Model):
    _inherit = "sale.order"

    approval_line = fields.One2many('sale.order.approval', 'approval_id')
    approvement_required = fields.Boolean(string='Requiere Aprobacion', default=False)
    credit_status = fields.Selection([('0','Requiere Aprobacion'),('1','Aprobado'),('2','Rechazado')],'Estado Credito',compute='get_credit_status',track_visibility='onchange',store=True)

    @api.depends('approval_line', 'approval_line.state')
    def get_credit_status(self):
        for i in self:
            if len(i.approval_line)==0:
                i.credit_status = False
            else:
                stat = '0'
                line_approved = 0
                line_detained = 0
                line_refused = 0
                for elem in i.approval_line:
                    if elem.state == 'refused':
                        line_refused += 1
                    if elem.state == 'detained':
                        line_detained += 1
                    if elem.state == 'approved':
                        line_approved += 1
                if line_approved == len(i.approval_line):
                    stat = '1'
                else:
                    if line_detained>0:
                        stat = '0'
                    else:
                        if line_refused == len(i.approval_line):
                            stat = '2'
                i.credit_status = stat

    def action_confirm(self):
        if self.payment_term_id.is_credit_control:
            self.check_credit_limit(True)
            if not self.approvement_required:
                self.check_invoice_overdue(True)
            self.check_approval_lines()
            if self.approvement_required:
                return self.env['popup.it'].get_message('Pedido Requiere Aprobaciones')
        return super(SaleOrder, self).action_confirm()

    @api.onchange('approval_line')
    def check_approval_lines(self):
        for record in self:
            if any(line.state != 'approved' for line in record.approval_line):
                record.approvement_required = True
            else:
                record.approvement_required = False

    def get_parsed_amount(self):
        for record in self:
            if record.pricelist_id.currency_id.name == 'USD':
                rate = self.env['res.currency.rate'].search([('name', '=', record.date_order.date())]).rate
                if not rate:
                    raise UserError('No existe tipo de cambio para la fecha {0} para el documento {1}'.format(record.date_order.date(), record.name))
                exchange_type = 1/rate
                new_balance = record.amount_total * exchange_type
            else:
                new_balance = record.amount_total
        return new_balance

    def check_credit_limit(self, crear_registro = False):
        self.ensure_one()
        partner = self.partner_id
        result = False
        ## check if this is a customer who doesn't need to be enforced
        if not partner.check_credit_limit:
            return result

        ## Find not invoiced sale orders
        all_so_notinv = self.env['sale.order'].search([
            ('partner_id', '=', partner.id),
            ('company_id', '=', self.company_id.id),
            ('invoice_status', 'in', ['to invoice']),
        ])
        due_notinv = 0
        for so in all_so_notinv:
            due_notinv += so.get_parsed_amount()

        ## Find all invoices
        all_invoices = self.env['account.move'].search([
            ('partner_id', '=', partner.id),
            ('type', 'in', ['out_invoice','out_refund']),
            ('company_id', '=', self.company_id.id),
			('state', 'in', ['posted']),
        ])
        all_open = 0
        all_due = 0.0
        for inv in all_invoices:
            due = inv.amount_residual
            all_due += due
            all_open += 1
            aa = '\n\nInvoice %s Due %s \n\n' % (inv.display_name, due)

        new_balance = self.get_parsed_amount()
        #new_balance += partner.credit

        MainParameter = self.env['sale.main.parameter'].search([],limit=1)
        ##get some parameters
        includenot =  MainParameter.include_not_invoiced
        fresh_orders = MainParameter.force_limit_fresh_orders

        #if includenot:
        #    new_balance = new_balance + due_notinv

        msg = 'Credit Limit Error !! You need to increase the limit of this customer to proceed \n New Balance %s \n Current Customer Balance %s \n  Limit %s \n Open Invoices %s \n Due Invoices %s ' % (
            new_balance, (partner.credit * (-1)), partner.credit_limit2, all_open, all_due)
        _logger.debug(msg)

        v_fresh = True
        if all_open == 0 and not fresh_orders:
            v_fresh = False

        term_obj = self.env['sale.order.approval']

        if new_balance > partner.credit_balance:

            if not self.approval_line:
                if crear_registro:
                    dToday = datetime.now().date()
                    vals = {
                        'name': 'Name',
                        'reason': 'Limite de credito',
                        'date': dToday,
                        'approval_id': self.id,
                        'state': 'detained',
                        'notes': str(new_balance)
                    }
                    term_obj.create(vals)
                result = True
        return result

    # Validacion de facturas vencidas.
    def check_invoice_overdue(self, crear_registro = False):
        self.ensure_one()
        MainParameter = self.env['sale.main.parameter'].search([],limit=1)
        # get some parameters

        due_days = MainParameter.invoice_tolerance_due 
        due_amount_min = MainParameter.invoice_amount_due
        result = False

        now = date.today()
        past_date = now - timedelta(days=int(due_days))

        past_due_invoices = self.env['account.move'].search([
            ('type', '=', 'out_invoice'),
            ('company_id', '=', self.company_id.id),
            ('partner_id', '=', self.partner_id.id),
            ('state', 'in', ['posted']),
            ('invoice_payment_state', '!=', 'paid'), 
            ('invoice_date_due', '<', past_date),

        ])

        due_amount = 0.0
        due_count = 0
        msj = ""
        for invoice in past_due_invoices:
            # amount = invoice.currency_id.compute(invoice.residual, credit_limit_currency)
            amount = invoice.amount_residual
            due_amount += amount
            due_count += 1
            msj += 'Comprobante %s Deuda %s \n' % (invoice.display_name, due_amount)

        term_obj = self.env['sale.order.approval']

        if due_count >= 1 and due_amount >= due_amount_min:
            if crear_registro:
                dToday = date.today()
                vals = {
                    'name': 'Name',
                    'reason': 'Morosidad',
                    'date': dToday,
                    'approval_id': self.id,
                    'state': 'detained',
                    'notes': msj
                }
                term_obj.create(vals)

            result = True
        return result
