from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def create(self,vals):
        res = super(AccountMove,self).create(vals)
        for account in res:
            if account.auto_post:
                account.post()
        return res
