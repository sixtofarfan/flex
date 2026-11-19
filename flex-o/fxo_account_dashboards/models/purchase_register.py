# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

from .dashboard_mixin import REGISTER_COLS

SUM_COLS = REGISTER_COLS + ['total', 'amount_me']


class FxoPurchaseRegisterLine(models.Model):
    """Rows of the Purchase Register loaded by each user from the dashboard."""
    _name = 'fxo.purchase.register.line'
    _inherit = 'fxo.dashboard.mixin'
    _description = 'Purchase Register'
    _order = 'period, journal_code, voucher, id'
    _rec_name = 'voucher'

    user_id = fields.Many2one('res.users', string='User', index=True, required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', index=True)
    move_id = fields.Many2one('account.move', string='Journal Entry', index=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Partner', index=True)
    account_id = fields.Many2one('account.account', string='Payable Account', index=True)
    account_codes = fields.Char(string='Account')
    account_names = fields.Char(string='Account Name')
    expense_codes = fields.Char(string='Expense Account')
    period = fields.Char(string='Period', index=True)
    date = fields.Date(string='Accounting Date')
    journal_code = fields.Char(string='Journal')
    voucher = fields.Char(string='Voucher')
    invoice_date = fields.Date(string='Issue Date')
    date_due = fields.Date(string='Due Date')
    doc_type = fields.Char(string='Doc. Type')
    serie = fields.Char(string='Series')
    doc_year = fields.Char(string='Year')
    doc_number = fields.Char(string='Number')
    partner_doc_type = fields.Char(string='Partner Doc. Type')
    partner_vat = fields.Char(string='Tax ID')
    partner_name = fields.Char(string='Partner Name')
    base1 = fields.Float(string='BIOGYE', digits=(16, 2))
    base2 = fields.Float(string='BIOGEYNG', digits=(16, 2))
    base3 = fields.Float(string='BIONG', digits=(16, 2))
    cng = fields.Float(string='CNG', digits=(16, 2))
    isc = fields.Float(string='ISC', digits=(16, 2))
    icbper = fields.Float(string='ICBPER', digits=(16, 2))
    otros = fields.Float(string='Others', digits=(16, 2))
    igv1 = fields.Float(string='IGV 1', digits=(16, 2))
    igv2 = fields.Float(string='IGV 2', digits=(16, 2))
    igv3 = fields.Float(string='IGV 3', digits=(16, 2))
    total = fields.Float(string='Total', digits=(16, 2))
    currency_name = fields.Char(string='Currency')
    amount_me = fields.Float(string='Foreign Amount', digits=(16, 2))
    currency_rate = fields.Float(string='Exchange Rate', digits=(12, 4))
    detraction_date = fields.Date(string='Detraction Date')
    detraction_number = fields.Char(string='Detraction Voucher')
    ref_doc_date = fields.Date(string='Ref. Doc. Date')
    ref_doc_type = fields.Char(string='Ref. Doc. Type')
    ref_serie = fields.Char(string='Ref. Series')
    ref_number = fields.Char(string='Ref. Number')
    glosa = fields.Char(string='Description')

    # ------------------------------------------------------------------
    @api.model
    def _fxo_columns(self):
        """Columns of the register, in the order of the current report with the
        account among the first ones."""
        def col(name, label, ctype='text', width=12, **kw):
            return dict(name=name, label=label, type=ctype, width=width, **kw)
        return [
            col('period', _('Period'), width=9),
            col('date', _('Acc. Date'), 'date', 11),
            col('journal_code', _('Journal'), width=7),
            col('voucher', _('Voucher'), width=12, link='move'),
            col('account_codes', _('Account'), width=10, link='account'),
            col('account_names', _('Account Name'), width=34),
            col('invoice_date', _('Issue Date'), 'date', 11),
            col('date_due', _('Due Date'), 'date', 11),
            col('doc_type', _('DT'), width=4),
            col('serie', _('Series'), width=8),
            col('doc_year', _('Year'), width=6),
            col('doc_number', _('Number'), width=11),
            col('partner_doc_type', _('PDT'), width=5),
            col('partner_vat', _('Tax ID'), width=12),
            col('partner_name', _('Partner'), width=40, link='partner'),
            col('base1', 'BIOGYE', 'number', 12, sum=True),
            col('base2', 'BIOGEYNG', 'number', 12, sum=True),
            col('base3', 'BIONG', 'number', 12, sum=True),
            col('cng', 'CNG', 'number', 12, sum=True),
            col('isc', 'ISC', 'number', 10, sum=True),
            col('icbper', 'ICBPER', 'number', 10, sum=True),
            col('otros', _('Others'), 'number', 10, sum=True),
            col('igv1', 'IGV 1', 'number', 12, sum=True),
            col('igv2', 'IGV 2', 'number', 10, sum=True),
            col('igv3', 'IGV 3', 'number', 10, sum=True),
            col('total', _('Total'), 'number', 13, sum=True),
            col('currency_name', _('Cur.'), width=5),
            col('amount_me', _('Foreign Amt.'), 'number', 12, sum=True),
            col('currency_rate', _('Rate'), 'rate', 8),
            col('detraction_date', _('Detr. Date'), 'date', 11),
            col('detraction_number', _('Detr. Voucher'), width=12),
            col('ref_doc_date', _('Ref. Doc. Date'), 'date', 11),
            col('ref_doc_type', _('Ref. DT'), width=6),
            col('ref_serie', _('Ref. Series'), width=8),
            col('ref_number', _('Ref. Number'), width=11),
            col('glosa', _('Description'), width=45),
        ]

    @api.model
    def _fxo_search_fields(self):
        return [
            {'name': 'partner_name', 'label': _('Partner')},
            {'name': 'partner_vat', 'label': _('Tax ID')},
            {'name': 'doc_number', 'label': _('Number')},
            {'name': 'voucher', 'label': _('Voucher')},
            {'name': 'account_codes', 'label': _('Account')},
            {'name': 'account_names', 'label': _('Account Name')},
            {'name': 'journal_code', 'label': _('Journal')},
            {'name': 'doc_type', 'label': _('Doc. Type')},
            {'name': 'glosa', 'label': _('Description')},
        ]

    # ------------------------------------------------------------------
    @api.model
    def fxo_load(self, filters):
        """(Re)build the rows of the current user for the given filters."""
        f = self._fxo_parse_filters(filters)
        select, params = self._fxo_purchase_sql(f['company'], f['date_from'], f['date_to'], f['currency'])
        cols = ['period', 'date', 'journal_code', 'voucher', 'invoice_date', 'date_due', 'doc_type', 'serie',
                'doc_year', 'doc_number', 'partner_doc_type', 'partner_vat', 'partner_name'] + REGISTER_COLS + [
                'total', 'currency_name', 'amount_me', 'currency_rate', 'detraction_date', 'detraction_number',
                'ref_doc_date', 'ref_doc_type', 'ref_serie', 'ref_number', 'glosa', 'company_id', 'move_id',
                'partner_id', 'account_codes', 'account_names', 'account_id', 'expense_codes']
        cr = self.env.cr
        cr.execute("DELETE FROM fxo_purchase_register_line WHERE user_id = %s", (self.env.uid,))
        params['uid'] = self.env.uid
        cr.execute("""
            INSERT INTO fxo_purchase_register_line
                   (user_id, create_uid, write_uid, create_date, write_date, {cols})
            SELECT %(uid)s, %(uid)s, %(uid)s, now() AT TIME ZONE 'UTC', now() AT TIME ZONE 'UTC', {qcols}
              FROM ({select}) q
        """.format(cols=', '.join(cols), qcols=', '.join('q.' + c for c in cols), select=select), params)
        count = cr.rowcount
        self.invalidate_cache()
        return {'count': count}

    @api.model
    def fxo_summary(self, domain, currency='pen'):
        """KPIs, chart series and footer totals of the rows matching ``domain``."""
        cr = self.env.cr
        from_clause, where, params = self._fxo_user_query(domain)
        t = self._table
        sums = ', '.join('COALESCE(sum("%s".%s), 0) AS %s' % (t, c, c) for c in SUM_COLS)
        cr.execute("""
            SELECT count(*) AS count, count(DISTINCT "{t}".partner_id) AS partners,
                   count(*) FILTER (WHERE "{t}".currency_name <> 'PEN') AS foreign_docs, {sums}
              FROM {f} WHERE {w}""".format(t=t, sums=sums, f=from_clause, w=where), params)
        tot = cr.dictfetchone()
        taxable = tot['base1'] + tot['base2'] + tot['base3']
        igv = tot['igv1'] + tot['igv2'] + tot['igv3']
        kpis = {
            'count': tot['count'], 'partners': tot['partners'], 'foreign_docs': tot['foreign_docs'],
            'total': tot['total'], 'taxable': taxable, 'igv': igv, 'non_taxable': tot['cng'],
            'other': tot['isc'] + tot['icbper'] + tot['otros'], 'amount_me': tot['amount_me'],
            'average': tot['total'] / tot['count'] if tot['count'] else 0.0,
        }
        cr.execute("""
            SELECT "{t}".period AS key,
                   COALESCE(sum("{t}".base1 + "{t}".base2 + "{t}".base3), 0) AS taxable,
                   COALESCE(sum("{t}".igv1 + "{t}".igv2 + "{t}".igv3), 0) AS igv,
                   COALESCE(sum("{t}".total), 0) AS total, count(*) AS count
              FROM {f} WHERE {w} GROUP BY 1 ORDER BY 1""".format(t=t, f=from_clause, w=where), params)
        monthly = cr.dictfetchall()
        cr.execute("""
            SELECT "{t}".partner_id AS id, max("{t}".partner_name) AS name, max("{t}".partner_vat) AS vat,
                   COALESCE(sum("{t}".total), 0) AS total, count(*) AS count
              FROM {f} WHERE {w} GROUP BY 1 ORDER BY 4 DESC LIMIT 10""".format(t=t, f=from_clause, w=where), params)
        partners = cr.dictfetchall()
        cr.execute("""
            SELECT COALESCE("{t}".doc_type, '') AS key, COALESCE(sum("{t}".total), 0) AS total, count(*) AS count
              FROM {f} WHERE {w} GROUP BY 1 ORDER BY 2 DESC""".format(t=t, f=from_clause, w=where), params)
        doc_types = cr.dictfetchall()
        # Purchase bases split by the account of each journal item (exact, not by voucher)
        amount = 'COALESCE(l.tax_amount_me, 0)' if currency == 'usd' else 'COALESCE(l.tax_amount_it, 0)'
        cr.execute("""
            SELECT a.code AS key, a.name AS name, sum({amount}) AS total, count(DISTINCT l.move_id) AS count
              FROM {f}
              JOIN account_move_line l ON l.move_id = "{t}".move_id AND l.display_type IS NULL
              JOIN account_account a ON a.id = l.account_id
             WHERE {w}
               AND EXISTS (SELECT 1
                             FROM account_account_tag_account_move_line_rel r
                             JOIN account_account_tag tg ON tg.id = r.account_account_tag_id
                            WHERE r.account_move_line_id = l.id
                              AND tg.record_shop IN ('1', '2', '3', '4', '5', '6'))
             GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 12""".format(t=t, f=from_clause, w=where, amount=amount), params)
        accounts = cr.dictfetchall()
        return {'kpis': kpis, 'totals': tot, 'monthly': monthly, 'partners': partners,
                'doc_types': doc_types, 'accounts': accounts}

    def action_open_move(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'res_model': 'account.move', 'res_id': self.move_id.id,
            'view_mode': 'form', 'views': [(False, 'form')], 'target': 'current',
        }
