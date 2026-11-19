# -*- coding: utf-8 -*-
import calendar
import csv
import io
import re
from datetime import date, datetime

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools.misc import xlsxwriter

REGISTER_COLS = ['base1', 'base2', 'base3', 'cng', 'isc', 'icbper', 'otros', 'igv1', 'igv2', 'igv3']
# record_shop code of account.account.tag for each purchase register column
REGISTER_TAGS = [('base1', '1'), ('base2', '2'), ('base3', '3'), ('cng', '4'), ('isc', '5'),
                 ('otros', '6'), ('igv1', '7'), ('igv2', '8'), ('igv3', '9'), ('icbper', '10')]


class FxoDashboardMixin(models.AbstractModel):
    """Shared helpers of the accounting dashboards: filter handling, the SQL of
    both reports (single source for dashboards and legacy wizards) and exports."""
    _name = 'fxo.dashboard.mixin'
    _description = 'Accounting dashboards helpers'

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    @api.model
    def _fxo_parse_filters(self, filters):
        filters = filters or {}
        company = self.env['res.company'].browse(int(filters.get('company_id') or self.env.company.id))
        if company not in self.env.companies:
            raise AccessError(_('You are not allowed to see the company "%s".') % company.name)
        period_from = period_to = False
        if filters.get('by_period'):
            # Periods "YYYYMM": 00 = opening entry, 01-12 = months, 13 = closing entry
            period_from = str(filters.get('period_from') or '')
            period_to = str(filters.get('period_to') or '')
            if not (re.match(r'^\d{4}(0\d|1[0-3])$', period_from) and re.match(r'^\d{4}(0\d|1[0-3])$', period_to)):
                raise UserError(_('The initial and final periods are required.'))
            if period_from[:4] != period_to[:4]:
                raise UserError(_('The initial and final periods must belong to the same fiscal year.'))
            if period_to < period_from:
                raise UserError(_('The final period cannot be earlier than the initial period.'))
            year = int(period_from[:4])
            month_from = min(max(int(period_from[4:]), 1), 12)
            month_to = min(max(int(period_to[4:]), 1), 12)
            date_from = date(year, month_from, 1)
            date_to = date(year, month_to, calendar.monthrange(year, month_to)[1])
        else:
            try:
                date_from = fields.Date.to_date(filters.get('date_from'))
                date_to = fields.Date.to_date(filters.get('date_to'))
            except Exception:
                date_from = date_to = False
            if not date_from or not date_to:
                raise UserError(_('The start and end dates are required.'))
            if date_to < date_from:
                raise UserError(_('The end date cannot be earlier than the start date.'))
            if date_from.year != date_to.year:
                raise UserError(_('The start and end dates must belong to the same fiscal year.'))
        currency = 'usd' if filters.get('currency') == 'usd' else 'pen'
        return {'company': company, 'date_from': date_from, 'date_to': date_to, 'currency': currency,
                'period_from': period_from, 'period_to': period_to}

    @api.model
    def fxo_options(self):
        """Data needed by the filter bar of the dashboards."""
        company = self.env.company
        today = fields.Date.context_today(self)
        self.env.cr.execute(
            "SELECT DISTINCT extract(year FROM date_from)::int FROM account_fiscal_year WHERE date_from IS NOT NULL")
        years = {r[0] for r in self.env.cr.fetchall()} | {today.year}
        defaults = {}
        params = self.env['main.parameter'].sudo().search([('company_id', 'in', self.env.companies.ids)])
        for param in params:
            fy = param.fiscal_year
            if fy and fy.date_from and fy.date_to and fy.date_from.year == fy.date_to.year:
                defaults[param.company_id.id] = {
                    'year': fy.date_from.year,
                    'date_from': fields.Date.to_string(fy.date_from),
                    'date_to': fields.Date.to_string(fy.date_to),
                }
        return {
            'companies': [{'id': c.id, 'name': c.name} for c in self.env.companies.sorted('name')],
            'company_id': company.id,
            'years': sorted(years, reverse=True),
            'year': today.year,
            'defaults': defaults,
            'columns': self._fxo_columns(),
            'search_fields': self._fxo_search_fields(),
        }

    @api.model
    def _fxo_columns(self):
        return []

    @api.model
    def _fxo_search_fields(self):
        return []

    @api.model
    def _fxo_user_query(self, domain):
        """FROM / WHERE of the rows of the current user matching ``domain``."""
        domain = list(domain or []) + [('user_id', '=', self.env.uid)]
        query = self._where_calc(domain)
        self._apply_ir_rules(query, 'read')
        from_clause, where_clause, params = query.get_sql()
        return from_clause, where_clause or 'TRUE', params

    @api.model
    def fxo_rows(self, domain, fields_list, offset=0, limit=80, order=None):
        """Page of rows for the table of the dashboard."""
        domain = list(domain or []) + [('user_id', '=', self.env.uid)]
        sort = None
        if order and order.get('field') in self._fields:
            sort = '%s %s, id' % (order['field'], 'desc' if order.get('dir') == 'desc' else 'asc')
        fields_list = [f for f in fields_list if f in self._fields]
        return {
            'length': self.search_count(domain),
            'records': self.search_read(domain, fields_list, offset=int(offset or 0),
                                        limit=min(int(limit or 80), 1000), order=sort),
        }

    # ------------------------------------------------------------------
    # SQL: purchase register
    # ------------------------------------------------------------------
    @api.model
    def _fxo_purchase_sql(self, company, date_from, date_to, currency):
        """SELECT of the purchase register (one row per voucher). Same rules as the
        legacy view ``vst_compras_1_1`` but filtered from the start by company and
        dates, plus the account of the voucher (payable, else current assets)."""
        mn = ', '.join("sum(CASE WHEN t.record_shop = '%s' THEN l.tax_amount_it ELSE 0 END) AS %s" % (tag, col)
                       for col, tag in REGISTER_TAGS)
        me = ', '.join("sum(CASE WHEN t.record_shop = '%s' THEN COALESCE(l.tax_amount_me, 0) ELSE 0 END) AS %s_me"
                       % (tag, col) for col, tag in REGISTER_TAGS)
        suffix = '_me' if currency == 'usd' else ''
        amounts = ', '.join('COALESCE(amt.%s%s, 0) AS %s' % (c, suffix, c) for c in REGISTER_COLS)
        total = ' + '.join('COALESCE(amt.%s%s, 0)' % (c, suffix) for c in REGISTER_COLS)
        total_me = ' + '.join('COALESCE(amt.%s_me, 0)' % c for c in REGISTER_COLS)
        sql = """
WITH mv AS (
    SELECT am.id, am.date, am.name, am.invoice_date, am.invoice_date_due, am.ref, am.partner_id,
           am.type_document_id, am.currency_id, am.currency_rate, am.date_detraccion, am.voucher_number,
           am.glosa, am.company_id, aj.code AS journal_code
      FROM account_move am
      JOIN account_journal aj ON aj.id = am.journal_id
     WHERE aj.register_sunat = '1' AND am.state = 'posted'
       AND am.company_id = %(company_id)s AND am.date BETWEEN %(date_from)s AND %(date_to)s
), amt AS (
    SELECT l.move_id, {mn}, {me}
      FROM account_move_line l
      JOIN mv ON mv.id = l.move_id
      JOIN account_account_tag_account_move_line_rel r ON r.account_move_line_id = l.id
      JOIN account_account_tag t ON t.id = r.account_account_tag_id
     WHERE l.display_type IS NULL AND l.account_id IS NOT NULL AND t.record_shop IS NOT NULL
     GROUP BY l.move_id
), pay AS (
    -- Account of the voucher: the one of type Payable (42...); if it has none
    -- (e.g. IGV application entries), the one of type Current Assets. Never taxes.
    SELECT d.move_id,
           COALESCE(string_agg(d.code, ', ' ORDER BY d.code) FILTER (WHERE d.is_payable),
                    string_agg(d.code, ', ' ORDER BY d.code) FILTER (WHERE NOT d.is_payable)) AS account_codes,
           COALESCE(string_agg(d.name, ', ' ORDER BY d.code) FILTER (WHERE d.is_payable),
                    string_agg(d.name, ', ' ORDER BY d.code) FILTER (WHERE NOT d.is_payable)) AS account_names,
           COALESCE((array_agg(d.account_id ORDER BY d.amount DESC) FILTER (WHERE d.is_payable))[1],
                    (array_agg(d.account_id ORDER BY d.amount DESC) FILTER (WHERE NOT d.is_payable))[1]) AS account_id
      FROM (SELECT l.move_id, l.account_id, a.code, a.name, (a.internal_type = 'payable') AS is_payable,
                   sum(abs(l.balance)) AS amount
              FROM account_move_line l
              JOIN mv ON mv.id = l.move_id
              JOIN account_account a ON a.id = l.account_id
             WHERE l.display_type IS NULL
               AND (a.internal_type = 'payable' OR a.user_type_id = %(current_assets_type)s)
             GROUP BY l.move_id, l.account_id, a.code, a.name, a.internal_type) d
     GROUP BY d.move_id
), exp AS (
    -- Expense / purchase accounts: journal items tagged with a base of the register
    SELECT l.move_id, string_agg(DISTINCT a.code, ', ') AS expense_codes
      FROM account_move_line l
      JOIN mv ON mv.id = l.move_id
      JOIN account_account a ON a.id = l.account_id
     WHERE l.display_type IS NULL
       AND EXISTS (SELECT 1
                     FROM account_account_tag_account_move_line_rel r
                     JOIN account_account_tag t ON t.id = r.account_account_tag_id
                    WHERE r.account_move_line_id = l.id
                      AND t.record_shop IN ('1', '2', '3', '4', '5', '6'))
     GROUP BY l.move_id
)
SELECT to_char(mv.date, 'yyyymm') AS period,
       mv.date AS date,
       mv.journal_code,
       mv.name AS voucher,
       mv.invoice_date,
       mv.invoice_date_due AS date_due,
       ec1.code AS doc_type,
       CASE WHEN split_part(mv.ref, '-', 2) <> '' THEN split_part(mv.ref, '-', 1) END AS serie,
       CASE WHEN ec1.code = '50' THEN to_char(mv.invoice_date, 'yyyy') END AS doc_year,
       CASE WHEN split_part(mv.ref, '-', 2) <> '' THEN split_part(mv.ref, '-', 2)
            ELSE split_part(mv.ref, '-', 1) END AS doc_number,
       lit.code_sunat AS partner_doc_type,
       rp.vat AS partner_vat,
       rp.name AS partner_name,
       {amounts},
       {total} AS total,
       rc.name AS currency_name,
       CASE WHEN rc.name <> 'PEN' THEN {total_me} ELSE 0 END AS amount_me,
       mv.currency_rate,
       mv.date_detraccion AS detraction_date,
       mv.voucher_number AS detraction_number,
       dr.date AS ref_doc_date,
       ec2.code AS ref_doc_type,
       CASE WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 1) END AS ref_serie,
       CASE WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 2)
            ELSE split_part(dr.nro_comprobante, '-', 1) END AS ref_number,
       mv.glosa,
       mv.company_id,
       mv.id AS move_id,
       rp.id AS partner_id,
       pay.account_codes,
       pay.account_names,
       pay.account_id,
       exp.expense_codes
  FROM mv
  LEFT JOIN res_partner rp ON rp.id = mv.partner_id
  LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
  LEFT JOIN einvoice_catalog_01 ec1 ON ec1.id = mv.type_document_id
  LEFT JOIN res_currency rc ON rc.id = mv.currency_id
  LEFT JOIN amt ON amt.move_id = mv.id
  LEFT JOIN pay ON pay.move_id = mv.id
  LEFT JOIN exp ON exp.move_id = mv.id
  LEFT JOIN LATERAL (SELECT d.date, d.nro_comprobante, d.type_document_id
                       FROM doc_invoice_relac d
                      WHERE d.move_id = mv.id
                      ORDER BY d.id LIMIT 1) dr ON TRUE
  LEFT JOIN einvoice_catalog_01 ec2 ON ec2.id = dr.type_document_id
 ORDER BY 1, mv.journal_code, mv.name
""".format(mn=mn, me=me, amounts=amounts, total=total, total_me=total_me)
        current_assets = self.env.ref('account.data_account_type_current_assets', raise_if_not_found=False)
        return sql, {'company_id': company.id, 'date_from': date_from, 'date_to': date_to,
                     'current_assets_type': current_assets.id if current_assets else 0}

    # ------------------------------------------------------------------
    # SQL: analytic ledger
    # ------------------------------------------------------------------
    @api.model
    def _fxo_account_filter(self, company, account_ids=None, prefixes=None):
        """Ids of the accounts selected by ids and/or by code prefixes; None = all."""
        ids = set(account_ids or [])
        prefixes = [p.strip() for p in str(prefixes or '').replace(';', ',').split(',') if p.strip()]
        if prefixes:
            self.env.cr.execute(
                "SELECT id FROM account_account WHERE company_id = %s AND code LIKE ANY(%s)",
                (company.id, [p.replace('%', '') + '%' for p in prefixes]))
            ids |= {r[0] for r in self.env.cr.fetchall()}
            if not ids:
                raise UserError(_('No account matches "%s".') % ', '.join(prefixes))
        return list(ids) or None

    @api.model
    def _fxo_ledger_sql(self, company, date_from, date_to, currency, account_ids=None,
                        period_from=None, period_to=None):
        """SELECT of the analytic ledger (one row per journal item plus one opening
        balance row per account when the start date is not January 1st), with the
        running balance per account. Same rules as ``get_mayor_detalle``."""
        params = {'company_id': company.id, 'date_from': date_from, 'date_to': date_to,
                  'year_start': date(date_from.year, 1, 1)}
        account_filter = ''
        if account_ids:
            account_filter = 'AND l.account_id IN %(account_ids)s'
            params['account_ids'] = tuple(account_ids)
        # By dates (legacy wizards) or by accounting periods (00 opening ... 13 closing)
        movement, opening = 'y.date >= %(date_from)s', 'y.date < %(date_from)s'
        opening_period = "to_char(%(date_from)s::date - 1, 'yyyymm')"
        if period_from and period_to:
            params.update(period_from=period_from, period_to=period_to,
                          opening_period='%s%02d' % (period_from[:4], max(int(period_from[4:]) - 1, 0)))
            movement = 'y.period BETWEEN %(period_from)s AND %(period_to)s'
            opening = 'y.period < %(period_from)s'
            opening_period = '%(opening_period)s'
        if currency == 'usd':
            amounts = "COALESCE(x.debit_me, 0) AS debit, COALESCE(x.credit_me, 0) AS credit, " \
                      "COALESCE(x.debit_me, 0) - COALESCE(x.credit_me, 0) AS balance"
        else:
            amounts = "x.debit, x.credit, x.balance"
        sql = """
WITH x AS (
    SELECT l.id AS move_line_id, am.id AS move_id, am.date,
           CASE WHEN am.is_opening_close AND to_char(am.date, 'mmdd') = '0101' THEN to_char(am.date, 'yyyy') || '00'
                WHEN am.is_opening_close AND to_char(am.date, 'mmdd') = '1231' THEN to_char(am.date, 'yyyy') || '13'
                ELSE to_char(am.date, 'yyyymm') END AS period,
           aj.code AS journal_code, am.name AS voucher, l.account_id,
           l.debit, l.credit, l.balance,
           CASE WHEN cur.name = 'USD' THEN CASE WHEN l.debit <> 0 THEN l.amount_currency END
                ELSE round(l.debit / COALESCE(NULLIF(l.tc, 0), 1), 2) END AS debit_me,
           CASE WHEN cur.name = 'USD' THEN CASE WHEN l.credit <> 0 THEN abs(l.amount_currency) END
                ELSE round(l.credit / COALESCE(NULLIF(l.tc, 0), 1), 2) END AS credit_me,
           CASE WHEN l.currency_id IS NULL THEN 'PEN' ELSE cur.name END AS currency_name,
           COALESCE(NULLIF(l.tc, 0), 1) AS currency_rate,
           l.amount_currency, l.analytic_account_id, am.glosa, l.name AS line_name,
           l.partner_id, lit.code_sunat AS partner_doc_type, rp.vat AS partner_vat, rp.name AS partner_name,
           ec.code AS doc_type, replace(l.nro_comp, '/', '-') AS doc_number,
           am.invoice_date, l.date_maturity
      FROM account_move_line l
      JOIN account_move am ON am.id = l.move_id
      JOIN account_journal aj ON aj.id = am.journal_id
      LEFT JOIN res_currency cur ON cur.id = l.currency_id
      LEFT JOIN res_partner rp ON rp.id = l.partner_id
      LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
      LEFT JOIN einvoice_catalog_01 ec ON ec.id = l.type_document_id
     WHERE am.state = 'posted' AND l.display_type IS NULL AND l.account_id IS NOT NULL
       AND am.company_id = %(company_id)s AND l.company_id = %(company_id)s
       AND l.date BETWEEN %(year_start)s AND %(date_to)s
       {account_filter}
), y AS (
    SELECT x.move_line_id, x.move_id, x.date, x.period, x.journal_code, x.voucher, x.account_id,
           {amounts}, x.currency_name, x.currency_rate, x.amount_currency, x.analytic_account_id,
           x.glosa, x.line_name, x.partner_id, x.partner_doc_type, x.partner_vat, x.partner_name,
           x.doc_type, x.doc_number, x.invoice_date, x.date_maturity
      FROM x
), rows AS (
    SELECT FALSE AS is_opening, y.* FROM y WHERE {movement}
    UNION ALL
    SELECT TRUE, NULL::int, NULL::int, (%(date_from)s::date - 1), {opening_period},
           '', '', y.account_id,
           GREATEST(sum(y.balance), 0), GREATEST(-sum(y.balance), 0), sum(y.balance),
           '', 0, sum(y.amount_currency), NULL::int,
           'SALDO INICIAL', NULL, NULL::int, '', '', '', '', '', NULL::date, NULL::date
      FROM y
     WHERE {opening}
     GROUP BY y.account_id
)
SELECT r.is_opening, r.move_line_id, r.move_id, r.date, r.period, r.journal_code, r.voucher,
       r.account_id, a.code AS account_code, a.name AS account_name, left(a.code, 2) AS account_group,
       r.debit, r.credit, r.balance,
       sum(r.balance) OVER (PARTITION BY r.account_id
                            ORDER BY r.is_opening DESC, r.period, r.date, r.voucher, r.move_line_id) AS running_balance,
       r.currency_name, r.currency_rate, r.amount_currency,
       r.analytic_account_id, an.code AS analytic_code, an.name AS analytic_name,
       r.glosa, r.line_name, r.partner_id, r.partner_doc_type, r.partner_vat, r.partner_name,
       r.doc_type, r.doc_number, r.invoice_date, r.date_maturity,
       %(company_id)s AS company_id
  FROM rows r
  JOIN account_account a ON a.id = r.account_id
  LEFT JOIN account_analytic_account an ON an.id = r.analytic_account_id
 ORDER BY a.code, r.is_opening DESC, r.period, r.date, r.voucher, r.move_line_id
""".format(account_filter=account_filter, amounts=amounts, movement=movement, opening=opening,
           opening_period=opening_period)
        return sql, params

    # ------------------------------------------------------------------
    # Export (Excel with formulas / CSV)
    # ------------------------------------------------------------------
    @api.model
    def _fxo_export_rows(self, domain):
        cols = [c for c in self._fxo_columns() if not c.get('no_export')]
        domain = list(domain or []) + [('user_id', '=', self.env.uid)]
        rows = self.search_read(domain, [c['name'] for c in cols], order=self._order)
        return cols, rows

    @api.model
    def fxo_export(self, fmt, domain, meta=None):
        meta = meta or {}
        cols, rows = self._fxo_export_rows(domain)
        title = meta.get('title') or self._description
        fname = title.replace(' ', '_')
        if fmt == 'csv':
            out = io.StringIO()
            writer = csv.writer(out, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([c['label'] for c in cols])
            for row in rows:
                writer.writerow([self._fxo_csv_value(row.get(c['name'])) for c in cols])
            return fname + '.csv', ('﻿' + out.getvalue()).encode('utf-8'), 'text/csv;charset=utf-8'
        return fname + '.xlsx', self._fxo_xlsx(title, meta, cols, rows), \
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    @api.model
    def _fxo_csv_value(self, value):
        if value is False or value is None:
            return ''
        if isinstance(value, (list, tuple)):
            return value[1] if len(value) > 1 else ''
        return value

    @api.model
    def _fxo_xlsx(self, title, meta, cols, rows):
        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = wb.add_worksheet(title[:31])
        f_company = wb.add_format({'bold': True, 'font_size': 12})
        f_title = wb.add_format({'bold': True, 'font_size': 11, 'font_color': '#375623'})
        f_sub = wb.add_format({'font_size': 9, 'font_color': '#555555'})
        f_head = wb.add_format({'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#375623', 'border': 1,
                                'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'font_size': 9})
        f_text = wb.add_format({'font_size': 9})
        f_date = wb.add_format({'font_size': 9, 'num_format': 'dd/mm/yyyy'})
        f_num = wb.add_format({'font_size': 9, 'num_format': '#,##0.00'})
        f_rate = wb.add_format({'font_size': 9, 'num_format': '0.0000'})
        f_total = wb.add_format({'bold': True, 'font_size': 9, 'num_format': '#,##0.00', 'bg_color': '#A9D08E',
                                 'top': 1})
        f_total_lbl = wb.add_format({'bold': True, 'font_size': 9, 'bg_color': '#A9D08E', 'top': 1})
        ws.write(0, 0, meta.get('company') or self.env.company.name, f_company)
        ws.write(1, 0, title.upper(), f_title)
        ws.write(2, 0, meta.get('subtitle') or '', f_sub)
        head = 4
        for i, col in enumerate(cols):
            ws.write(head, i, col['label'].upper(), f_head)
            ws.set_column(i, i, col.get('width', 12))
        ws.set_row(head, 26)
        first = head + 1
        r = first
        for row in rows:
            for i, col in enumerate(cols):
                value = row.get(col['name'])
                ctype = col['type']
                if ctype == 'number':
                    ws.write_number(r, i, value or 0.0, f_num)
                elif ctype == 'rate':
                    ws.write_number(r, i, value or 0.0, f_rate)
                elif ctype == 'date':
                    if value:
                        ws.write_datetime(r, i, datetime.combine(value, datetime.min.time()), f_date)
                    else:
                        ws.write_blank(r, i, None, f_text)
                else:
                    ws.write(r, i, self._fxo_csv_value(value), f_text)
            r += 1
        last = max(r - 1, first)
        # Totals with live formulas: SUBTOTAL(9) follows the autofilter of the sheet
        for i, col in enumerate(cols):
            if col.get('sum'):
                rng = '%s%d:%s%d' % (self._fxo_col(i), first + 1, self._fxo_col(i), last + 1)
                ws.write_formula(r, i, '=SUBTOTAL(9,%s)' % rng, f_total)
            else:
                ws.write(r, i, _('TOTAL') if i == 0 else '', f_total_lbl)
        ws.autofilter(head, 0, last, len(cols) - 1)
        ws.freeze_panes(first, 0)
        wb.close()
        return output.getvalue()

    @api.model
    def _fxo_col(self, index):
        name = ''
        index += 1
        while index:
            index, rem = divmod(index - 1, 26)
            name = chr(65 + rem) + name
        return name
