from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError

class AccountJournal(models.Model):
    _inherit = 'account.journal'
    is_detraction = fields.Boolean(string='Is detraction')