# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_not_account_analytic = fields.Boolean(string='No Usa Cuenta analitica')
    
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    def post(self):
        # OVERRIDE to generate cross invoice based on company rules.
        res = super(AccountMove, self).post()
        for line in self.line_ids:
                line.constrains_not_account_analytic()
        return res

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    @api.constrains('account_id')
    def constrains_not_account_analytic(self):
        for item in self:
            if item.account_id.is_not_account_analytic:
                item.analytic_account_id = False

    @api.onchange('account_id')
    def onchange_not_account_analytic(self):
        self.constrains_not_account_analytic()

    
