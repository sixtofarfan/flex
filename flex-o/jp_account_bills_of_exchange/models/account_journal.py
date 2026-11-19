from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    type = fields.Selection(selection_add=[('boe', 'Bill of Exchange')])
    # Se puede agregar mas posiciones si el cliente lo solicita
    # Por ahora solo Cobranza, Descuento y Garantía
    bank_position = fields.Selection(string='Bank Position', selection=[('collection', 'Collection'), ('discount', 'Discount'), ('guarantee', 'Guarantee'),],)
    default_interest_account_id = fields.Many2one('account.account', string='Default Interest Account',
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]", help="It acts as a default account for interest in bills of exchange", ondelete='restrict')
    bank_partner_id = fields.Many2one('res.partner', string='Bank Partner')

    @api.constrains('currency_id', 'default_credit_account_id', 'default_debit_account_id','default_interest_account_id')
    def _check_currency(self):
        res = super(AccountJournal, self)._check_currency()
        for journal in self:
            if journal.currency_id:
                if journal.default_interest_account_id and not journal.default_interest_account_id.currency_id.id == journal.currency_id.id:
                    raise ValidationError(_('The currency of the journal should be the same than the default interest account.'))
        return res