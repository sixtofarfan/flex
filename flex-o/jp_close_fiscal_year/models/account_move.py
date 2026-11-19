from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    account_closure_id = fields.Many2one('account.closure', string='Account Closure')

class AccountAccount(models.Model):
    _inherit = 'account.account'

    closure_stage_id = fields.Many2one('account.closure.stage', string='Closure stage')
    