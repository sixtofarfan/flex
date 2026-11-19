from odoo import fields, models, api

class AccountPayment(models.Model):
    _inherit = "account.payment"

    disbursement_id = fields.Many2one('account.bank.disbursement', string='Bank Disbursement')

