# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

# PCGE (Peru): names of the 2-digit ledger accounts
PCGE = {
    '10': 'Efectivo y equivalentes de efectivo', '11': 'Inversiones financieras',
    '12': 'Cuentas por cobrar comerciales - terceros', '13': 'Cuentas por cobrar comerciales - relacionadas',
    '14': 'Cuentas por cobrar al personal, accionistas y directores',
    '16': 'Cuentas por cobrar diversas - terceros', '17': 'Cuentas por cobrar diversas - relacionadas',
    '18': 'Servicios y otros contratados por anticipado', '19': 'Estimación de cuentas de cobranza dudosa',
    '20': 'Mercaderías', '21': 'Productos terminados', '22': 'Subproductos, desechos y desperdicios',
    '23': 'Productos en proceso', '24': 'Materias primas', '25': 'Materiales auxiliares, suministros y repuestos',
    '26': 'Envases y embalajes', '27': 'Activos no corrientes mantenidos para la venta',
    '28': 'Inventarios por recibir', '29': 'Desvalorización de inventarios',
    '30': 'Inversiones mobiliarias', '31': 'Propiedades de inversión', '32': 'Activos por derecho de uso',
    '33': 'Propiedad, planta y equipo', '34': 'Intangibles', '35': 'Activos biológicos',
    '36': 'Desvalorización de activo inmovilizado', '37': 'Activo diferido', '38': 'Otros activos',
    '39': 'Depreciación y amortización acumulados',
    '40': 'Tributos, contraprestaciones y aportes por pagar', '41': 'Remuneraciones y participaciones por pagar',
    '42': 'Cuentas por pagar comerciales - terceros', '43': 'Cuentas por pagar comerciales - relacionadas',
    '44': 'Cuentas por pagar a accionistas, directores y gerentes', '45': 'Obligaciones financieras',
    '46': 'Cuentas por pagar diversas - terceros', '47': 'Cuentas por pagar diversas - relacionadas',
    '48': 'Provisiones', '49': 'Pasivo diferido',
    '50': 'Capital', '51': 'Acciones de inversión', '52': 'Capital adicional', '56': 'Resultados no realizados',
    '57': 'Excedente de revaluación', '58': 'Reservas', '59': 'Resultados acumulados',
    '60': 'Compras', '61': 'Variación de inventarios', '62': 'Gastos de personal y directores',
    '63': 'Gastos de servicios prestados por terceros', '64': 'Gastos por tributos',
    '65': 'Otros gastos de gestión', '66': 'Pérdida por medición de activos no financieros',
    '67': 'Gastos financieros', '68': 'Valuación y deterioro de activos y provisiones',
    '69': 'Costo de ventas',
    '70': 'Ventas', '71': 'Variación de la producción almacenada', '72': 'Producción de activo inmovilizado',
    '73': 'Descuentos, rebajas y bonificaciones obtenidos', '74': 'Descuentos, rebajas y bonificaciones concedidos',
    '75': 'Otros ingresos de gestión', '76': 'Ganancia por medición de activos no financieros',
    '77': 'Ingresos financieros', '78': 'Cargas cubiertas por provisiones', '79': 'Cargas imputables a cuentas de costos y gastos',
    '80': 'Margen comercial', '81': 'Producción del ejercicio', '82': 'Valor agregado',
    '83': 'Excedente bruto de explotación', '84': 'Resultado de explotación',
    '85': 'Resultado antes de participaciones e impuestos', '87': 'Participaciones de los trabajadores',
    '88': 'Impuesto a la renta', '89': 'Determinación del resultado del ejercicio',
    '90': 'Costos por distribuir', '91': 'Costos por distribuir', '92': 'Costos de producción',
    '93': 'Centros de costos', '94': 'Gastos administrativos', '95': 'Gastos de ventas',
    '96': 'Gastos de distribución', '97': 'Gastos financieros', '98': 'Otros centros de costos',
    '99': 'Otros centros de costos',
}


class FxoLedgerLine(models.Model):
    """Rows of the Analytic Ledger loaded by each user from the dashboard."""
    _name = 'fxo.ledger.line'
    _inherit = 'fxo.dashboard.mixin'
    _description = 'Analytic Ledger'
    _order = 'account_code, is_opening desc, period, date, voucher, move_line_id, id'
    _rec_name = 'voucher'

    user_id = fields.Many2one('res.users', string='User', index=True, required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', index=True)
    move_id = fields.Many2one('account.move', string='Journal Entry', index=True, ondelete='cascade')
    move_line_id = fields.Many2one('account.move.line', string='Journal Item', index=True, ondelete='cascade')
    is_opening = fields.Boolean(string='Opening Balance')
    period = fields.Char(string='Period', index=True)
    date = fields.Date(string='Date')
    journal_code = fields.Char(string='Journal')
    voucher = fields.Char(string='Voucher')
    account_id = fields.Many2one('account.account', string='Account Record', index=True)
    account_code = fields.Char(string='Account', index=True)
    account_name = fields.Char(string='Account Name')
    account_group = fields.Char(string='Ledger Account', index=True)
    debit = fields.Float(string='Debit', digits=(16, 2))
    credit = fields.Float(string='Credit', digits=(16, 2))
    balance = fields.Float(string='Balance', digits=(16, 2))
    running_balance = fields.Float(string='Running Balance', digits=(16, 2))
    currency_name = fields.Char(string='Currency')
    currency_rate = fields.Float(string='Exchange Rate', digits=(12, 4))
    amount_currency = fields.Float(string='Foreign Amount', digits=(16, 2))
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cost Center Record', index=True)
    analytic_code = fields.Char(string='Cost Center Code')
    analytic_name = fields.Char(string='Cost Center')
    glosa = fields.Char(string='Description')
    line_name = fields.Char(string='Line Label')
    partner_id = fields.Many2one('res.partner', string='Partner Record', index=True)
    partner_doc_type = fields.Char(string='Partner Doc. Type')
    partner_vat = fields.Char(string='Tax ID')
    partner_name = fields.Char(string='Partner')
    doc_type = fields.Char(string='Doc. Type')
    doc_number = fields.Char(string='Document Number')
    invoice_date = fields.Date(string='Document Date')
    date_maturity = fields.Date(string='Due Date')

    # ------------------------------------------------------------------
    @api.model
    def _fxo_columns(self):
        def col(name, label, ctype='text', width=12, **kw):
            return dict(name=name, label=label, type=ctype, width=width, **kw)
        return [
            col('period', _('Period'), width=9),
            col('date', _('Date'), 'date', 11),
            col('journal_code', _('Journal'), width=7),
            col('voucher', _('Voucher'), width=12, link='move'),
            col('account_group', _('Ledger Acc.'), width=8, link='group'),
            col('account_code', _('Account'), width=10, link='account'),
            col('account_name', _('Account Name'), width=34),
            col('debit', _('Debit'), 'number', 13, sum=True),
            col('credit', _('Credit'), 'number', 13, sum=True),
            col('balance', _('Balance'), 'number', 13, sum=True),
            col('running_balance', _('Running Bal.'), 'number', 13),
            col('currency_name', _('Cur.'), width=5),
            col('currency_rate', _('Rate'), 'rate', 8),
            col('analytic_code', _('CC Code'), width=10),
            col('analytic_name', _('Cost Center'), width=26, link='analytic'),
            col('glosa', _('Description'), width=42),
            col('line_name', _('Line Label'), width=42),
            col('partner_doc_type', _('PDT'), width=5),
            col('partner_vat', _('Tax ID'), width=12),
            col('partner_name', _('Partner'), width=38, link='partner'),
            col('doc_type', _('DT'), width=4),
            col('doc_number', _('Doc. Number'), width=16),
            col('invoice_date', _('Doc. Date'), 'date', 11),
            col('date_maturity', _('Due Date'), 'date', 11),
        ]

    @api.model
    def _fxo_search_fields(self):
        return [
            {'name': 'account_code', 'label': _('Account')},
            {'name': 'account_name', 'label': _('Account Name')},
            {'name': 'analytic_name', 'label': _('Cost Center')},
            {'name': 'partner_name', 'label': _('Partner')},
            {'name': 'partner_vat', 'label': _('Tax ID')},
            {'name': 'doc_number', 'label': _('Doc. Number')},
            {'name': 'voucher', 'label': _('Voucher')},
            {'name': 'journal_code', 'label': _('Journal')},
            {'name': 'glosa', 'label': _('Description')},
            {'name': 'line_name', 'label': _('Line Label')},
        ]

    # ------------------------------------------------------------------
    @api.model
    def fxo_load(self, filters):
        f = self._fxo_parse_filters(filters)
        account_ids = self._fxo_account_filter(f['company'], prefixes=(filters or {}).get('accounts'))
        select, params = self._fxo_ledger_sql(f['company'], f['date_from'], f['date_to'], f['currency'],
                                              account_ids, f['period_from'], f['period_to'])
        cols = ['is_opening', 'move_line_id', 'move_id', 'date', 'period', 'journal_code', 'voucher',
                'account_id', 'account_code', 'account_name', 'account_group', 'debit', 'credit', 'balance',
                'running_balance', 'currency_name', 'currency_rate', 'amount_currency', 'analytic_account_id',
                'analytic_code', 'analytic_name', 'glosa', 'line_name', 'partner_id', 'partner_doc_type',
                'partner_vat', 'partner_name', 'doc_type', 'doc_number', 'invoice_date', 'date_maturity',
                'company_id']
        cr = self.env.cr
        cr.execute("DELETE FROM fxo_ledger_line WHERE user_id = %s", (self.env.uid,))
        params['uid'] = self.env.uid
        cr.execute("""
            INSERT INTO fxo_ledger_line
                   (user_id, create_uid, write_uid, create_date, write_date, {cols})
            SELECT %(uid)s, %(uid)s, %(uid)s, now() AT TIME ZONE 'UTC', now() AT TIME ZONE 'UTC', {qcols}
              FROM ({select}) q
        """.format(cols=', '.join(cols), qcols=', '.join('q.' + c for c in cols), select=select), params)
        count = cr.rowcount
        self.invalidate_cache()
        return {'count': count}

    @api.model
    def fxo_summary(self, domain, currency='pen'):
        cr = self.env.cr
        f, w, params = self._fxo_user_query(domain)
        t = '"%s"' % self._table
        mov = 'NOT COALESCE(%s.is_opening, FALSE)' % t
        cr.execute("""
            SELECT count(*) FILTER (WHERE {mov}) AS count,
                   count(DISTINCT {t}.move_id) AS vouchers,
                   count(DISTINCT {t}.account_id) AS accounts,
                   COALESCE(sum({t}.debit) FILTER (WHERE {mov}), 0) AS debit,
                   COALESCE(sum({t}.credit) FILTER (WHERE {mov}), 0) AS credit,
                   COALESCE(sum({t}.balance) FILTER (WHERE {mov}), 0) AS net,
                   COALESCE(sum({t}.balance) FILTER (WHERE NOT {mov}), 0) AS opening,
                   COALESCE(sum({t}.balance), 0) AS closing,
                   COALESCE(sum({t}.debit), 0) AS total_debit,
                   COALESCE(sum({t}.credit), 0) AS total_credit
              FROM {f} WHERE {w}""".format(t=t, mov=mov, f=f, w=w), params)
        kpis = cr.dictfetchone()
        totals = {'debit': kpis['total_debit'], 'credit': kpis['total_credit'], 'balance': kpis['closing']}
        cr.execute("""
            SELECT {t}.period AS key, COALESCE(sum({t}.debit), 0) AS debit, COALESCE(sum({t}.credit), 0) AS credit,
                   COALESCE(sum({t}.balance), 0) AS balance, count(*) AS count
              FROM {f} WHERE {w} AND {mov} GROUP BY 1 ORDER BY 1""".format(t=t, mov=mov, f=f, w=w), params)
        monthly = cr.dictfetchall()
        cr.execute("""
            SELECT {t}.account_group AS key,
                   COALESCE(sum({t}.debit) FILTER (WHERE {mov}), 0) AS debit,
                   COALESCE(sum({t}.credit) FILTER (WHERE {mov}), 0) AS credit,
                   COALESCE(sum({t}.balance), 0) AS balance
              FROM {f} WHERE {w} GROUP BY 1 ORDER BY 1""".format(t=t, mov=mov, f=f, w=w), params)
        groups = cr.dictfetchall()
        for group in groups:
            group['name'] = PCGE.get(group['key'] or '', '')
        cr.execute("""
            SELECT {t}.account_code AS key, max({t}.account_name) AS name,
                   COALESCE(sum({t}.debit) FILTER (WHERE {mov}), 0) AS debit,
                   COALESCE(sum({t}.credit) FILTER (WHERE {mov}), 0) AS credit,
                   COALESCE(sum({t}.balance), 0) AS balance
              FROM {f} WHERE {w} GROUP BY 1
             ORDER BY COALESCE(sum(abs({t}.balance)) FILTER (WHERE {mov}), 0) DESC LIMIT 10
        """.format(t=t, mov=mov, f=f, w=w), params)
        accounts = cr.dictfetchall()
        cr.execute("""
            SELECT {t}.analytic_account_id AS id, max({t}.analytic_code) AS code, max({t}.analytic_name) AS name,
                   COALESCE(sum({t}.debit), 0) AS debit, COALESCE(sum({t}.credit), 0) AS credit,
                   COALESCE(sum({t}.balance), 0) AS balance
              FROM {f} WHERE {w} AND {mov} AND {t}.analytic_account_id IS NOT NULL
             GROUP BY 1 ORDER BY abs(COALESCE(sum({t}.balance), 0)) DESC LIMIT 10
        """.format(t=t, mov=mov, f=f, w=w), params)
        analytics = cr.dictfetchall()
        return {'kpis': kpis, 'totals': totals, 'monthly': monthly, 'groups': groups,
                'accounts': accounts, 'analytics': analytics}

    def action_open_move(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'res_model': 'account.move', 'res_id': self.move_id.id,
            'view_mode': 'form', 'views': [(False, 'form')], 'target': 'current',
        }
