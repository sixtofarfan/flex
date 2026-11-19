from odoo import fields, models, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from odoo.exceptions import UserError
from odoo.tools import format_date, float_round
import traceback

_logger = logging.getLogger(__name__)


# heredando forcast
class SuscripcionLine(models.Model):
    _inherit = 'sale.subscription.line'
    invoice_lines = fields.Many2many('account.move.line', compute="get_invoice_lines")
    # invoice_lines = fields.One2many('account.move.line', 'subscription_line_id')
    monto_facturado = fields.Float(compute="get_invoice_lines", string="Monto Facturado")
    monto_facturado_total = fields.Float(compute="get_invoice_lines", string="Monto Total Facturado ")
    period_report_id = fields.Many2one('account.period',
                                string='Period',
                                )
    name_period = fields.Char(string='Period')

    # amount_invoiced = fields.Float(related='monto_facturado_total', string="Monto Total Facturado ",store=True)

    def action_view_supscripcion(self):
        if not self.analytic_account_id:
            raise UserError(_('No tiene una supscripciòn'))
        if not self.id:
            raise UserError(_('crea el registro primero'))
        return {
            'name': ('Editar'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.subscription',
            # 'views': [(view.id, 'form')],
            # 'view_id': view.id,
            'target': 'current',
            'res_id': self.analytic_account_id.id,
            'context': dict(
                self.env.context,
            ),
        }

    @api.depends('analytic_account_id.invoice_count')
    def get_invoice_lines(self):
        InvoiceLine = self.env['account.move.line']
        for record in self:
            invoice_lines = InvoiceLine.search(
                [('subscription_id', '=', record.analytic_account_id.id),
                 ('product_id', '=', record.product_id.id), ('move_id.state', '=', 'posted')])

            record.invoice_lines = False if not invoice_lines else [(6, 0, invoice_lines.ids)]
            amount_invoice = 0
            amount_invoice_total = 0
            if invoice_lines and record.stop_date:
                for l in invoice_lines:
                    if not l.move_id.invoice_date:
                        continue
                    if l.move_id.state == 'posted' and l.move_id.invoice_date >= record.stop_date:
                        amount_invoice += l.price_subtotal
                        amount_invoice_total += l.price_total

            # query = f"SELECT sum(price_total ) FROM account_move_line  WHERE subscription_id =  "

            record.monto_facturado = amount_invoice
            record.monto_facturado_total = amount_invoice_total
