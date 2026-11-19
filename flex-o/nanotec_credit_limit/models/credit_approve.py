from odoo import fields, models, api
from odoo.tools.translate import _

class credit_approve_reason(models.Model):
    
    _name = "credit.approve.reason"
    _description = "Reason of credit approved"

    name = fields.Char('Name', size=256, required=True)
    reason_sunat_code = fields.Char('Cod.Sunat', size=10, required=True)

class credit_approve(models.Model):

    _name = 'credit.approve'
    _description = 'Credit approved'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Date('Effective Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
    reason_id = fields.Many2one('credit.approve.reason', 'Reason', required=True, readonly=True, states={'draft': [('readonly', False)]})
    notes = fields.Text('Notes', readonly=True, states={'draft': [('readonly', False)]})
    sale_order = fields.Many2one('sale.order', 'Cotizacion', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('cancel', 'Cancelled'), ('done', 'Done'), ], 'State', readonly=True, default="draft")


    def act_confirm(self):
        self.write({'state': 'confirm'})

    def state_cancel(self):
        self.write({'state': 'cancel'})
        return True

    def state_done(self):

        self.write({'state': 'done'})
