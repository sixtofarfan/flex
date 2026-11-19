from odoo import models, fields, api, _

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    currency_item_ids = fields.One2many('currency.journal.item', 'journal_id', string='Currency items')

class JournalCurrencyItems(models.Model):
    _name = 'currency.journal.item'
    _description = 'Currency Journal Items'

    journal_id = fields.Many2one('account.journal', string='Account Journal')
    currency_id = fields.Many2one('res.currency', string='Currency')
    account_id = fields.Many2one('account.account', string='Account')