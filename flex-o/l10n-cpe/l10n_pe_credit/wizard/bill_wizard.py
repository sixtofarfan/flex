# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PayBillWizard(models.TransientModel):
    _name = "bill.wizard"
    _description = "Bill Wizard Payment Terms"

    type_bill = fields.Selection([
        ('by_qty', 'By quantity'),
        ('by_amount', 'By amount'),
    ], string='Type of bills', default='by_qty')
    fees_qty = fields.Integer(string='Fees quantity')
    max_amount = fields.Float(string='Max amount on bills', digits=(12, 2))
    range_days = fields.Integer(string='Day range between fees')

    def get_wizard(self):
        return {
            'name': _('Bills wizard'),
            'res_model': 'bill.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('l10n_pe_credit.view_bill_wizard').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
    
    def create_fees(self):
        if self.fees_qty <= 0:
            raise UserError(_('Quantity must be greather than 0'))
        if self.range_days <= 0:
            raise UserError(_('Days range must be greather than 0'))
        active_id = self.env['account.move'].search([('id','=',self.env.context.get('active_id'))])
        # active_id.fees_calculated = False
        active_id.fees_qty = self.fees_qty
        active_id.days_range = self.range_days
        active_id._onchange_fees_qty()
        # active_id.with_context(active_ids=self.ids, 
        #     fees_calculated=True, 
        #     fees_qty=self.fees_qty,
        #     days_range=self.range_days,
        #     )._recompute_payment_terms_lines()
        
    @api.onchange('max_amount')
    def _onchange_max_amount(self):
        pass