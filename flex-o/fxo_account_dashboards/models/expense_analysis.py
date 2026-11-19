# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

from .ledger import PCGE


class FxoExpenseAnalysisLine(models.Model):
    """Expense Analysis: counterpart of the payable account of the Purchase
    Register (expense / purchase accounts and IGV), per journal item."""
    _name = 'fxo.expense.analysis.line'
    _inherit = 'fxo.dashboard.mixin'
    _description = 'Expense Analysis'
    _order = 'period, journal_code, voucher, account_code, id'
    _rec_name = 'voucher'

    user_id = fields.Many2one('res.users', string='User', index=True, required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', index=True)
    move_id = fields.Many2one('account.move', string='Journal Entry', index=True, ondelete='cascade')
    move_line_id = fields.Many2one('account.move.line', string='Journal Item', index=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Partner Record', index=True)
    account_id = fields.Many2one('account.account', string='Account Record', index=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cost Center Record', index=True)
    period = fields.Char(string='Period', index=True)
    date = fields.Date(string='Accounting Date')
    journal_code = fields.Char(string='Journal')
    voucher = fields.Char(string='Voucher')
    account_group = fields.Char(string='Ledger Account', index=True)
    account_code = fields.Char(string='Account', index=True)
    account_name = fields.Char(string='Account Name')
    analytic_code = fields.Char(string='Cost Center Code')
    analytic_name = fields.Char(string='Cost Center')
    register_column = fields.Char(string='Register Column')
    is_tax = fields.Boolean(string='Is IGV')
    base_amount = fields.Float(string='Expense', digits=(16, 2))
    tax_amount = fields.Float(string='IGV', digits=(16, 2))
    amount = fields.Float(string='Total', digits=(16, 2))
    payable_codes = fields.Char(string='Payable Account')
    doc_type = fields.Char(string='Doc. Type')
    serie = fields.Char(string='Series')
    doc_number = fields.Char(string='Number')
    partner_vat = fields.Char(string='Tax ID')
    partner_name = fields.Char(string='Partner')
    invoice_date = fields.Date(string='Issue Date')
    currency_name = fields.Char(string='Currency')
    glosa = fields.Char(string='Description')
    line_name = fields.Char(string='Line Label')

    # ------------------------------------------------------------------
    @api.model
    def _fxo_columns(self):
        def col(name, label, ctype='text', width=12, **kw):
            return dict(name=name, label=label, type=ctype, width=width, **kw)
        return [
            col('period', _('Period'), width=9),
            col('date', _('Acc. Date'), 'date', 11),
            col('journal_code', _('Journal'), width=7),
            col('voucher', _('Voucher'), width=12, link='move'),
            col('account_group', _('Ledger Acc.'), width=8, link='group'),
            col('account_code', _('Account'), width=10, link='account'),
            col('account_name', _('Account Name'), width=36),
            col('analytic_code', _('CC Code'), width=10),
            col('analytic_name', _('Cost Center'), width=26, link='analytic'),
            col('register_column', _('Register Col.'), width=10, link='column'),
            col('base_amount', _('Expense'), 'number', 13, sum=True),
            col('tax_amount', 'IGV', 'number', 12, sum=True),
            col('amount', _('Total'), 'number', 13, sum=True),
            col('payable_codes', _('Payable Acc.'), width=10),
            col('doc_type', _('DT'), width=4),
            col('serie', _('Series'), width=8),
            col('doc_number', _('Number'), width=11),
            col('partner_vat', _('Tax ID'), width=12),
            col('partner_name', _('Partner'), width=38, link='partner'),
            col('invoice_date', _('Issue Date'), 'date', 11),
            col('currency_name', _('Cur.'), width=5),
            col('glosa', _('Description'), width=42),
            col('line_name', _('Line Label'), width=42),
        ]

    @api.model
    def _fxo_search_fields(self):
        return [
            {'name': 'account_code', 'label': _('Account')},
            {'name': 'account_name', 'label': _('Account Name')},
            {'name': 'analytic_name', 'label': _('Cost Center')},
            {'name': 'partner_name', 'label': _('Partner')},
            {'name': 'partner_vat', 'label': _('Tax ID')},
            {'name': 'doc_number', 'label': _('Number')},
            {'name': 'voucher', 'label': _('Voucher')},
            {'name': 'journal_code', 'label': _('Journal')},
            {'name': 'glosa', 'label': _('Description')},
            {'name': 'line_name', 'label': _('Line Label')},
        ]

    # ------------------------------------------------------------------
    @api.model
    def fxo_load(self, filters):
        f = self._fxo_parse_filters(filters)
        select, params = self._fxo_expense_sql(f['company'], f['date_from'], f['date_to'], f['currency'])
        cols = ['period', 'date', 'journal_code', 'voucher', 'account_group', 'account_code', 'account_name',
                'analytic_code', 'analytic_name', 'register_column', 'is_tax', 'base_amount', 'tax_amount',
                'amount', 'payable_codes', 'doc_type', 'serie', 'doc_number', 'partner_vat', 'partner_name',
                'invoice_date', 'currency_name', 'glosa', 'line_name', 'company_id', 'move_id', 'move_line_id',
                'account_id', 'analytic_account_id', 'partner_id']
        cr = self.env.cr
        cr.execute("DELETE FROM fxo_expense_analysis_line WHERE user_id = %s", (self.env.uid,))
        params['uid'] = self.env.uid
        cr.execute("""
            INSERT INTO fxo_expense_analysis_line
                   (user_id, create_uid, write_uid, create_date, write_date, {cols})
            SELECT %(uid)s, %(uid)s, %(uid)s, now() AT TIME ZONE 'UTC', now() AT TIME ZONE 'UTC', {qcols}
              FROM ({select}) q
        """.format(cols=', '.join(cols), qcols=', '.join('q.' + c for c in cols), select=select), params)
        count = cr.rowcount
        self.invalidate_cache()
        # Control figure: total of the Purchase Register for the same filters
        register_sql, register_params = self._fxo_purchase_sql(f['company'], f['date_from'], f['date_to'],
                                                               f['currency'])
        cr.execute("SELECT COALESCE(sum(q.total), 0), count(*) FROM (%s) q" % register_sql, register_params)
        register_total, register_count = cr.fetchone()
        return {'count': count, 'register_total': float(register_total), 'register_count': register_count}

    @api.model
    def fxo_summary(self, domain, currency='pen'):
        cr = self.env.cr
        f, w, params = self._fxo_user_query(domain)
        t = '"%s"' % self._table
        cr.execute("""
            SELECT count(*) AS count, count(DISTINCT {t}.move_id) AS vouchers,
                   count(DISTINCT {t}.account_id) FILTER (WHERE NOT {t}.is_tax) AS accounts,
                   count(DISTINCT {t}.analytic_account_id) AS analytics,
                   COALESCE(sum({t}.base_amount), 0) AS base_amount,
                   COALESCE(sum({t}.tax_amount), 0) AS tax_amount,
                   COALESCE(sum({t}.amount), 0) AS amount,
                   COALESCE(sum({t}.base_amount) FILTER (WHERE {t}.analytic_account_id IS NULL), 0) AS no_analytic
              FROM {f} WHERE {w}""".format(t=t, f=f, w=w), params)
        kpis = cr.dictfetchone()
        # Loaded total (without the filters of the screen) to reconcile with the register
        cr.execute("SELECT COALESCE(sum(amount), 0) FROM fxo_expense_analysis_line WHERE user_id = %s",
                   (self.env.uid,))
        kpis['loaded_total'] = cr.fetchone()[0]
        totals = {'base_amount': kpis['base_amount'], 'tax_amount': kpis['tax_amount'], 'amount': kpis['amount']}
        cr.execute("""
            SELECT {t}.period AS key, COALESCE(sum({t}.base_amount), 0) AS base_amount,
                   COALESCE(sum({t}.tax_amount), 0) AS tax_amount
              FROM {f} WHERE {w} GROUP BY 1 ORDER BY 1""".format(t=t, f=f, w=w), params)
        monthly = cr.dictfetchall()
        cr.execute("""
            SELECT {t}.account_group AS key, COALESCE(sum({t}.base_amount), 0) AS total
              FROM {f} WHERE {w} AND NOT {t}.is_tax GROUP BY 1 ORDER BY 2 DESC""".format(t=t, f=f, w=w), params)
        groups = cr.dictfetchall()
        for group in groups:
            group['name'] = PCGE.get(group['key'] or '', '')
        cr.execute("""
            SELECT {t}.account_code AS key, max({t}.account_name) AS name,
                   COALESCE(sum({t}.base_amount), 0) AS total, count(DISTINCT {t}.move_id) AS count
              FROM {f} WHERE {w} AND NOT {t}.is_tax GROUP BY 1 ORDER BY 3 DESC LIMIT 12
        """.format(t=t, f=f, w=w), params)
        accounts = cr.dictfetchall()
        cr.execute("""
            SELECT {t}.analytic_account_id AS id, max({t}.analytic_code) AS code, max({t}.analytic_name) AS name,
                   COALESCE(sum({t}.base_amount), 0) AS total
              FROM {f} WHERE {w} AND NOT {t}.is_tax GROUP BY 1 ORDER BY 4 DESC LIMIT 10
        """.format(t=t, f=f, w=w), params)
        analytics = cr.dictfetchall()
        return {'kpis': kpis, 'totals': totals, 'monthly': monthly, 'groups': groups,
                'accounts': accounts, 'analytics': analytics}
