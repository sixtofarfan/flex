# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, tools
from odoo.osv import expression


class AccountMove(models.Model):
    _inherit = 'account.move'

    type_invoice = fields.Selection(
        selection_add=[('C', 'Monthly consumption'), ('P', 'Project'), ('N', 'None')], default='N')

    def init(self):
        res = super(AccountMove, self).init()
        # The pickers of invoices filter by partner: account.move has no index on it
        tools.create_index(self._cr, 'account_move_partner_id_index', self._table, ['partner_id'])
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Picker of invoices of the exchange of bills (context ``fxo_move_search``):
        find by voucher or by document number, also partially, and by the whole
        display name "VOUCHER (NUMBER)". The standard picker only finds the exact
        voucher, so typing the number of the invoice returned nothing."""
        if not self.env.context.get('fxo_move_search'):
            return super(AccountMove, self).name_search(name, args, operator, limit)
        domain = list(args or [])
        name = (name or '').strip()
        if name:
            terms = [name]
            match = re.match(r'^(.+?)\s*\((.*)\)$', name)
            if match:
                terms = [t.strip() for t in match.groups() if t.strip()]
            search = []
            for term in terms:
                search = expression.OR([search, [('name', 'ilike', term)], [('ref', 'ilike', term)]])
            domain = expression.AND([domain, search])
        return self.search(domain, limit=limit).name_get()
