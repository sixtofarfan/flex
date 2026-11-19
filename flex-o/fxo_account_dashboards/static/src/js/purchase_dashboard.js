odoo.define('fxo_account_dashboards.PurchaseDashboard', function (require) {
"use strict";

var core = require('web.core');
var DashboardBase = require('fxo_account_dashboards.DashboardBase');

var _t = core._t;
var _lt = core._lt;

var PurchaseDashboard = DashboardBase.extend({
    model: 'fxo.purchase.register.line',
    dashTitle: _lt('Purchase Register'),
    dashIcon: 'fa-shopping-basket',
    extraFields: ['move_id', 'partner_id'],
    gotoLinks: [{tag: 'fxo_expense_dashboard', label: _lt('Expense Analysis'), icon: 'fa-pie-chart'}],
    chartSpecs: [
        {key: 'monthly', title: _lt('Monthly evolution'), size: 'fxo-w-7'},
        {key: 'partners', title: _lt('Top 10 suppliers'), size: 'fxo-w-5'},
        {key: 'accounts', title: _lt('Purchases by expense account'), size: 'fxo-w-7'},
        {key: 'doc_types', title: _lt('By document type'), size: 'fxo-w-5'},
    ],

    _kpiCards: function () {
        var k = this.summary.kpis;
        var share = function (part) { return k.total ? (100 * part / k.total).toFixed(1) + ' %' : '0 %'; };
        return [
            {label: _t('Total purchases'), value: this.money(k.total), icon: 'fa-shopping-cart', tone: 'primary',
             sub: this.fmtInt(k.count) + ' ' + _t('vouchers')},
            {label: _t('Taxable base'), value: this.money(k.taxable), icon: 'fa-cubes', tone: 'green',
             sub: share(k.taxable) + ' ' + _t('of total')},
            {label: _t('IGV'), value: this.money(k.igv), icon: 'fa-percent', tone: 'amber',
             sub: share(k.igv) + ' ' + _t('of total')},
            {label: _t('Non-taxable'), value: this.money(k.non_taxable + k.other), icon: 'fa-ban', tone: 'slate',
             sub: share(k.non_taxable + k.other) + ' ' + _t('of total')},
            {label: _t('Suppliers'), value: this.fmtInt(k.partners), icon: 'fa-users', tone: 'blue',
             sub: _t('Average per voucher') + ': ' + this.fmt(k.average)},
            {label: _t('Foreign currency'), value: 'US$ ' + this.fmt(k.amount_me), icon: 'fa-usd', tone: 'violet',
             sub: this.fmtInt(k.foreign_docs) + ' ' + _t('vouchers'), chip: 'foreign'},
        ];
    },

    _kpiChip: function (chip) {
        if (chip === 'foreign') {
            this.addChip('currency', _t('Foreign currency'), [['currency_name', '!=', 'PEN']]);
        }
    },

    _drawCharts: function () {
        var self = this;
        var s = this.summary;

        this._chart({
            key: 'monthly', type: 'bar',
            labels: _.map(s.monthly, function (m) { return self.periodLabel(m.key); }),
            datasets: [
                {label: _t('Taxable base'), backgroundColor: '#1f6f54',
                 data: _.map(s.monthly, function (m) { return m.taxable; })},
                {label: _t('IGV'), backgroundColor: '#f2b441',
                 data: _.map(s.monthly, function (m) { return m.igv; })},
                {label: _t('Non-taxable'), backgroundColor: '#9fb3bd',
                 data: _.map(s.monthly, function (m) { return m.total - m.taxable - m.igv; })},
            ],
            options: {
                legend: {display: true, position: 'bottom'},
                scales: {xAxes: [this._catAxis(true)], yAxes: [this._axis(true)]},
            },
            onPick: function (i) {
                var m = s.monthly[i];
                self.addChip('period', self.periodLabel(m.key), [['period', '=', m.key]]);
            },
        });

        this._chart({
            key: 'partners', type: 'horizontalBar',
            labels: _.map(s.partners, function (p) { return self.short(p.name || _t('No partner'), 30); }),
            datasets: [{label: _t('Total'), backgroundColor: '#2f9e77',
                        data: _.map(s.partners, function (p) { return p.total; })}],
            options: {scales: {xAxes: [this._axis()], yAxes: [this._catAxis()]}},
            onPick: function (i) {
                var p = s.partners[i];
                self.addChip('partner', self.short(p.name || _t('No partner'), 34),
                             [['partner_id', '=', p.id || false]]);
            },
        });

        this._chart({
            key: 'accounts', type: 'horizontalBar',
            labels: _.map(s.accounts, function (a) { return a.key + '  ' + self.short(a.name, 34); }),
            datasets: [{label: _t('Amount'), backgroundColor: '#3b82b8',
                        data: _.map(s.accounts, function (a) { return a.total; })}],
            options: {scales: {xAxes: [this._axis()], yAxes: [this._catAxis()]}},
            onPick: function (i) {
                var a = s.accounts[i];
                self.addChip('expense', _t('Expense acc.') + ' ' + a.key, [['expense_codes', 'ilike', a.key]]);
            },
        });

        this._chart({
            key: 'doc_types', type: 'doughnut',
            labels: _.map(s.doc_types, function (d) { return (d.key || '—') + '  (' + d.count + ')'; }),
            datasets: [{backgroundColor: this.palette(s.doc_types.length), borderWidth: 2,
                        data: _.map(s.doc_types, function (d) { return d.total; })}],
            options: {legend: {display: true, position: 'right'}, cutoutPercentage: 62},
            onPick: function (i) {
                var d = s.doc_types[i];
                self.addChip('doc_type', _t('DT') + ' ' + (d.key || '—'),
                             [['doc_type', '=', d.key || false]]);
            },
        });
    },

    _followLink: function (kind, row, value) {
        if (kind === 'account') {
            // The account opens the Analytic Ledger with the same period
            this.do_action({
                type: 'ir.actions.client', tag: 'fxo_ledger_dashboard', name: _t('Analytic Ledger'),
                params: this._gotoParams({accounts: value}),
            });
            return;
        }
        this._super.apply(this, arguments);
    },
});

core.action_registry.add('fxo_purchase_dashboard', PurchaseDashboard);

return PurchaseDashboard;

});
