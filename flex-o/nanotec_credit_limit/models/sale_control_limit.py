# -*- coding: utf-8 -*-
from odoo import api, models, fields
from . import sale_order
from odoo.exceptions import UserError
from odoo import exceptions
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class SaleConfirmLimit(models.TransientModel):
    _name = 'sale.control.limit.wizard'

    sale_order = fields.Many2one('sale.order')
    invoice_amount = fields.Float('Invoice Amount', readonly=1)
    debt = fields.Float('Existing Invoiced Debts', readonly=1)
    credit_limit2 = fields.Float('Partner Credit Limit', readonly=1)
    new_balance = fields.Float('New Balance ', readonly=1)
    due_not_invoiced = fields.Float('Amount Due for Sale Orders not yet Invoiced', readonly=1)
    notes = fields.Text('Notes', readonly=True, states={'draft': [('readonly', False)]})

    
    def agent_exceed_limit(self):
        self.sale_order.need_approval = True
        _logger.debug(' \n\n \t Adding USers\n\n\n')
        group = self.env.ref('sales_team.group_sale_manager')
        for myu in group.users:
            self.sale_order.message_subscribe([myu.partner_id.id])
            self.sale_order.message_post('Order Approval is requested for a customer with Credit Limit issue',
                                         subject='Order Approval is requested for a customer with Credit Limit issue',
                                         subtype='mail.mt_comment', type='comment')

    
    def exceed_limit_approve(self):
        term_obj = self.env['credit.approve']
        dToday = datetime.now().date()
        vals = {
            'name': dToday,
            'sale_order': self.sale_order.id,
            'reason_id': 1,
            'state': 'draft',
            'notes': self.notes
        }

        term_obj.create(vals)
