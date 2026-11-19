# -*- coding: utf-8 -*-
"""New columns in the existing wizards (Accounting > Reports): account in the
Purchase Register; account name, 2-digit ledger account, cost center and line
label in the Analytic Ledger. Both keep their current layout and options
(screen / Excel / CSV) and now read the same SQL as the dashboards."""
import base64
import csv
import io

from odoo import fields, models
from odoo.tools.misc import xlsxwriter


def _fxo_build_file(env, fmt, sheet, columns, rows, totals=()):
    """Excel in the layout of the legacy reports (report.base formats) or CSV.
    columns: (key, HEADER, kind, width); kind in text/date/num/rate."""
    if fmt == 'csv':
        out = io.StringIO()
        writer = csv.writer(out, delimiter=',')
        writer.writerow([c[1] for c in columns])
        for row in rows:
            writer.writerow(['' if row[c[0]] in (None, False) else row[c[0]] for c in columns])
        return base64.b64encode(out.getvalue().encode('utf-8'))
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    workbook, formats = env['report.base'].get_formats(workbook)
    worksheet = workbook.add_worksheet(sheet)
    worksheet.set_tab_color('blue')
    worksheet = env['report.base'].get_headers(worksheet, [c[1] for c in columns], 0, 0, formats['boldbord'])
    kinds = {'text': formats['especial1'], 'date': formats['dateformat'], 'num': formats['numberdos'],
             'rate': formats['numbercuatro']}
    x = 1
    for row in rows:
        for y, (key, _header, kind, _width) in enumerate(columns):
            value = row[key]
            if kind in ('num', 'rate'):
                worksheet.write(x, y, value or 0.0, kinds[kind])
            else:
                worksheet.write(x, y, value if value not in (None, False) else '', kinds[kind])
        x += 1
    for y, (key, _header, _kind, _width) in enumerate(columns):
        if key in totals:
            worksheet.write(x, y, sum((row[key] or 0.0) for row in rows), formats['numbertotal'])
    worksheet = env['report.base'].resize_cells(worksheet, [c[3] for c in columns])
    workbook.close()
    return base64.b64encode(output.getvalue())


# ----------------------------------------------------------------------
# Purchase Register
# ----------------------------------------------------------------------
class AccountPurchaseBook(models.Model):
    _inherit = 'account.purchase.book'

    account_codes = fields.Char(string='Account')
    account_names = fields.Char(string='Account Name')
    move_id = fields.Many2one('account.move', string='Journal Entry')

    def action_open_move(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'res_model': 'account.move', 'res_id': self.move_id.id,
            'view_mode': 'form', 'views': [(False, 'form')], 'target': 'current',
        }


PURCHASE_COLUMNS = [
    ('periodo', 'PERIODO', 'text', 9), ('fecha_cont', 'FECHA CONT', 'date', 12), ('libro', 'LIBRO', 'text', 7),
    ('voucher', 'VOUCHER', 'text', 11), ('account_codes', 'CUENTA', 'text', 10),
    ('account_names', 'NOMBRE CUENTA', 'text', 34),
    ('fecha_e', 'FECHA EM', 'date', 10), ('fecha_v', 'FECHA VEN', 'date', 10), ('td', 'TD', 'text', 3),
    ('serie', 'SERIE', 'text', 10), ('anio', u'AÑO', 'text', 10), ('numero', u'NÚMERO', 'text', 10),
    ('tdp', 'TDP', 'text', 4), ('docp', 'RUC', 'text', 11), ('namep', 'PARTNER', 'text', 40),
    ('base1', 'BIOGYE', 'num', 10), ('base2', 'BIOGEYNG', 'num', 10), ('base3', 'BIONG', 'num', 10),
    ('cng', 'CNG', 'num', 10), ('isc', 'ISC', 'num', 10), ('icbper', 'ICBPER', 'num', 10),
    ('otros', 'OTROS', 'num', 10), ('igv1', 'IGV 1', 'num', 10), ('igv2', 'IGV 2', 'num', 10),
    ('igv3', 'IGV 3', 'num', 10), ('total', 'TOTAL', 'num', 12), ('name', 'MON', 'text', 5),
    ('monto_me', 'MONTO ME', 'num', 12), ('currency_rate', 'TC', 'rate', 7),
    ('fecha_det', 'FECHA DET', 'date', 12), ('comp_det', 'COMP DET', 'text', 12),
    ('f_doc_m', 'FECHA DOC M', 'date', 12), ('td_doc_m', 'TD DOC M', 'text', 12),
    ('serie_m', 'SERIE M', 'text', 12), ('numero_m', 'NUMERO M', 'text', 12), ('glosa', 'GLOSA', 'text', 47),
]
PURCHASE_TOTALS = ('base1', 'base2', 'base3', 'cng', 'isc', 'icbper', 'otros', 'igv1', 'igv2', 'igv3', 'total')


class AccountPurchaseRep(models.TransientModel):
    _inherit = 'account.purchase.rep'

    def _get_sql(self):
        select, params = self.env['fxo.dashboard.mixin']._fxo_purchase_sql(
            self.company_id, self.date_ini, self.date_end, self.currency)
        sql = """SELECT row_number() OVER () AS id,
                q.period AS periodo, q.date AS fecha_cont, q.journal_code AS libro, q.voucher,
                q.invoice_date AS fecha_e, q.date_due AS fecha_v, q.doc_type AS td, q.serie,
                q.doc_year AS anio, q.doc_number AS numero, q.partner_doc_type AS tdp, q.partner_vat AS docp,
                q.partner_name AS namep, q.base1, q.base2, q.base3, q.cng, q.isc, q.icbper, q.otros,
                q.igv1, q.igv2, q.igv3, q.total, q.currency_name AS name, q.amount_me AS monto_me,
                q.currency_rate, q.detraction_date AS fecha_det, q.detraction_number AS comp_det,
                q.ref_doc_date AS f_doc_m, q.ref_doc_type AS td_doc_m, q.ref_serie AS serie_m,
                q.ref_number AS numero_m, q.glosa, q.account_codes, q.account_names, q.move_id
                FROM (""" + select + """) q"""
        return self.env.cr.mogrify(sql, params).decode('utf-8')

    def get_report(self):
        # The columns of the view change, so it cannot be only "replaced"
        self.env.cr.execute("DROP VIEW IF EXISTS account_purchase_book")
        return super(AccountPurchaseRep, self).get_report()

    def _fxo_book_rows(self):
        self.env.cr.execute("SELECT * FROM account_purchase_book ORDER BY periodo, libro, voucher")
        return self.env.cr.dictfetchall()

    def get_excel(self):
        data = _fxo_build_file(self.env, 'xlsx', 'REGISTRO COMPRAS', PURCHASE_COLUMNS, self._fxo_book_rows(),
                               PURCHASE_TOTALS)
        return self.env['popup.it'].get_file('Registro Compras.xlsx', data)

    def getCsv(self):
        data = _fxo_build_file(self.env, 'csv', '', PURCHASE_COLUMNS, self._fxo_book_rows())
        return self.env['popup.it'].get_file('Registro Compras.csv', data)


# ----------------------------------------------------------------------
# Analytic Ledger
# ----------------------------------------------------------------------
class AccountHigherBook(models.Model):
    _inherit = 'account.higher.book'

    account_name = fields.Char(string='Account Name')
    ledger_account = fields.Char(string='Ledger Account')
    cost_center_code = fields.Char(string='Cost Center Code')
    cost_center = fields.Char(string='Cost Center')
    line_label = fields.Char(string='Line Label')
    move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='cascade')

    def action_open_move(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'res_model': 'account.move', 'res_id': self.move_id.id,
            'view_mode': 'form', 'views': [(False, 'form')], 'target': 'current',
        }


LEDGER_COLUMNS = [
    ('periodo', 'PERIODO', 'text', 9), ('fecha', 'FECHA', 'text', 10), ('libro', 'LIBRO', 'text', 7),
    ('voucher', 'VOUCHER', 'text', 11), ('ledger_account', 'CTA MAYOR', 'text', 9),
    ('cuenta', 'CUENTA', 'text', 9), ('account_name', 'NOMBRE CUENTA', 'text', 36),
    ('debe', 'DEBE', 'num', 12), ('haber', 'HABER', 'num', 12), ('balance', 'BALANCE', 'num', 12),
    ('saldo', 'SALDO', 'num', 12), ('moneda', 'MON', 'text', 5), ('tc', 'TC', 'rate', 7),
    ('cost_center_code', 'COD CC', 'text', 10), ('cost_center', 'CENTRO DE COSTO', 'text', 26),
    ('glosa', 'GLOSA', 'text', 47), ('line_label', 'GLOSA LINEA', 'text', 47), ('td_partner', 'TDP', 'text', 4),
    ('doc_partner', 'RUC', 'text', 11), ('partner', 'PARTNER', 'text', 40), ('td_sunat', 'TD', 'text', 3),
    ('nro_comprobante', 'NRO COMPROBANTE', 'text', 16), ('fecha_doc', 'FECHA DOC', 'date', 12),
    ('fecha_ven', 'FECHA VEN', 'date', 12),
]


class AccountHigherRep(models.TransientModel):
    _inherit = 'account.higher.rep'

    def _fxo_fill_book(self):
        select, params = self.env['fxo.dashboard.mixin']._fxo_ledger_sql(
            self.company_id, self.date_ini, self.date_end, self.currency, self.account_ids.ids or None)
        params['uid'] = self.env.uid
        cr = self.env.cr
        cr.execute("DELETE FROM account_higher_book WHERE company_id = %s", (self.company_id.id,))
        cr.execute("""
            INSERT INTO account_higher_book
                   (create_uid, write_uid, create_date, write_date, company_id, periodo, fecha, libro, voucher,
                    cuenta, debe, haber, balance, saldo, moneda, tc, code_cta_analitica, glosa, td_partner,
                    doc_partner, partner, td_sunat, nro_comprobante, fecha_doc, fecha_ven,
                    account_name, ledger_account, cost_center_code, cost_center, line_label, move_id)
            SELECT %(uid)s, %(uid)s, now() AT TIME ZONE 'UTC', now() AT TIME ZONE 'UTC', q.company_id, q.period,
                   to_char(q.date, 'yyyy-mm-dd'), q.journal_code, q.voucher, q.account_code, q.debit, q.credit,
                   q.balance, q.running_balance, q.currency_name, q.currency_rate, q.analytic_name, q.glosa,
                   q.partner_doc_type, q.partner_vat, q.partner_name, q.doc_type, q.doc_number, q.invoice_date,
                   q.date_maturity, q.account_name, q.account_group, q.analytic_code, q.analytic_name,
                   q.line_name, q.move_id
              FROM (""" + select + """) q""", params)
        self.env['account.higher.book'].invalidate_cache()

    def _fxo_book_rows(self):
        self.env.cr.execute(
            "SELECT * FROM account_higher_book WHERE company_id = %s ORDER BY id", (self.company_id.id,))
        return self.env.cr.dictfetchall()

    def get_report(self):
        self.domain_dates()
        self._fxo_fill_book()
        if self.type_show == 'pantalla':
            return {
                'name': 'Libro Mayor Analitico',
                'domain': [('company_id', '=', self.company_id.id)],
                'type': 'ir.actions.act_window',
                'res_model': 'account.higher.book',
                'view_mode': 'tree,pivot,graph',
                'view_type': 'form',
            }
        if self.type_show == 'excel':
            data = _fxo_build_file(self.env, 'xlsx', 'LIBRO MAYOR ANALITICO', LEDGER_COLUMNS, self._fxo_book_rows())
            return self.env['popup.it'].get_file('Libro_Mayor_Analitico.xlsx', data)
        data = _fxo_build_file(self.env, 'csv', '', LEDGER_COLUMNS, self._fxo_book_rows())
        return self.env['popup.it'].get_file('LibroMayorAnalitico.csv', data)
