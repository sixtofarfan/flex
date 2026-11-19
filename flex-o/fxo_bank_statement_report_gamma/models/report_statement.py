from odoo import api, models
from odoo.tools import float_round

class ReportStatementGamma(models.AbstractModel):
    _name = 'report.fxo_bank_statement_report_gamma.report_statement_gamma'
    _description = 'Report Statement Gamma'

    @api.model
    def _get_report_values(self, docids, data=None):
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.bank.statement',
            'docs': self.env['account.bank.statement'].browse(docids),
            'custom': self.get_custom_data(docids),
        }
        return docargs
    
    def get_custom_data(self, docids):
        Statement = self.env['account.bank.statement'].browse(docids)
        Lines = Statement.line_ids.filtered(lambda l: l.amount > 0)
        income = sum(Lines.mapped('amount')) if Lines else 0
        Lines = Statement.line_ids.filtered(lambda l: l.amount < 0)
        charge = sum([abs(l) for l in Lines.mapped('amount')]) if Lines else 0
        return {
            'income': float_round(income, 2),
            'charge': float_round(charge, 2),
            'difference': float_round(income - charge, 2),
        }