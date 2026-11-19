# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def _fxo_check_open(self):
        for statement in self:
            if statement.state != 'open':
                raise UserError(_(
                    'The statement "%s" is validated. Reset it to New before '
                    'reverting or deleting its lines.') % (statement.name or ''))

    def action_fxo_unreconcile_all(self):
        """Revert the reconciliation of every reconciled line of the statement."""
        self._fxo_check_open()
        lines = self.mapped('line_ids').filtered('journal_entry_ids')
        if lines:
            lines.button_cancel_reconciliation()
        return True

    def action_fxo_unreconcile_delete(self):
        """Revert every reconciliation and delete the whole statement."""
        self._fxo_check_open()
        is_cash = any(st.journal_type == 'cash' for st in self)
        self.action_fxo_unreconcile_all()
        self.unlink()
        xmlid = 'account.action_view_bank_statement_tree' if is_cash \
            else 'account.action_bank_statement_tree'
        action = self.env.ref(xmlid).read()[0]
        action['target'] = 'main'
        return action


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    def action_fxo_unreconcile_delete(self):
        """Revert the reconciliation of the line (if any) and delete it."""
        self.mapped('statement_id')._fxo_check_open()
        lines = self.filtered('journal_entry_ids')
        if lines:
            lines.button_cancel_reconciliation()
        self.unlink()
        return True
