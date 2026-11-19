odoo.define('fxo_account_dashboards.ExpenseDashboard', function (require) {
"use strict";

var core = require('web.core');
var DashboardBase = require('fxo_account_dashboards.DashboardBase');

var _t = core._t;
var _lt = core._lt;

/**
 * Expense Analysis: the counterpart of the payable account of the Purchase
 * Register (expense accounts, cost centers and IGV), reconciled with its total.
 */
var ExpenseDashboard = DashboardBase.extend({
    model: 'fxo.expense.analysis.line',
    dashTitle: _lt('Expense Analysis'),
    dashIcon: 'fa-pie-chart',
    extraFields: ['move_id', 'partner_id', 'analytic_account_id', 'is_tax'],
    gotoLinks: [{tag: 'fxo_purchase_dashboard', label: _lt('Purchase Register'), icon: 'fa-shopping-basket'}],
    chartSpecs: [
        {key: 'accounts', title: _lt('Top 12 expense accounts'), size: 'fxo-w-7'},
        {key: 'groups', title: _lt('Expense by ledger account (2 digits)'), size: 'fxo-w-5'},
        {key: 'monthly', title: _lt('Monthly evolution'), size: 'fxo-w-6'},
        {key: 'analytics', title: _lt('Expense by cost center'), size: 'fxo-w-6'},
    ],

    _kpiCards: function () {
        var k = this.summary.kpis;
        var info = this.loadInfo || {};
        var diff = Math.round((Number(k.loaded_total) - Number(info.register_total || 0)) * 100) / 100;
        var ok = Math.abs(diff) < 0.005;
        return [
            {label: _t('Expense (base)'), value: this.money(k.base_amount), icon: 'fa-cubes', tone: 'primary',
             sub: this.fmtInt(k.accounts) + ' ' + _t('accounts')},
            {label: _t('IGV'), value: this.money(k.tax_amount), icon: 'fa-percent', tone: 'amber',
             sub: _t('Tax of the vouchers')},
            {label: _t('Total'), value: this.money(k.amount), icon: 'fa-calculator', tone: 'green',
             sub: this.fmtInt(k.vouchers) + ' ' + _t('vouchers') + ' · ' + this.fmtInt(k.count) + ' ' + _t('lines')},
            {label: _t('Purchase Register'), value: this.money(info.register_total), icon: 'fa-shopping-basket',
             tone: 'blue', sub: this.fmtInt(info.register_count) + ' ' + _t('vouchers')},
            {label: _t('Reconciliation'), value: ok ? _t('Balanced') : this.money(diff),
             icon: ok ? 'fa-check-circle' : 'fa-exclamation-triangle', tone: ok ? 'ok' : 'bad',
             sub: ok ? _t('Equal to the Purchase Register') : _t('Difference with the Purchase Register')},
            {label: _t('Without cost center'), value: this.money(k.no_analytic), icon: 'fa-question-circle',
             tone: 'slate', sub: this.fmtInt(k.analytics) + ' ' + _t('cost centers used'), chip: 'no_cc'},
        ];
    },

    _kpiChip: function (chip) {
        if (chip === 'no_cc') {
            this.addChip('analytic', _t('Without cost center'),
                         [['analytic_account_id', '=', false], ['is_tax', '=', false]]);
        }
    },

    _drawCharts: function () {
        var self = this;
        var s = this.summary;

        this._chart({
            key: 'accounts', type: 'horizontalBar',
            labels: _.map(s.accounts, function (a) { return a.key + '  ' + self.short(a.name, 36); }),
            datasets: [{label: _t('Expense'), backgroundColor: '#1f6f54',
                        data: _.map(s.accounts, function (a) { return a.total; })}],
            options: {scales: {xAxes: [this._axis()], yAxes: [this._catAxis()]}},
            onPick: function (i) {
                var a = s.accounts[i];
                self.addChip('account', _t('Account') + ' ' + a.key, [['account_code', '=', a.key]]);
            },
        });

        this._chart({
            key: 'groups', type: 'doughnut',
            labels: _.map(s.groups, function (g) { return (g.key || '—') + '  ' + self.short(g.name, 28); }),
            datasets: [{backgroundColor: this.palette(s.groups.length), borderWidth: 2,
                        data: _.map(s.groups, function (g) { return g.total; })}],
            options: {legend: {display: true, position: 'right'}, cutoutPercentage: 58},
            onPick: function (i) {
                var g = s.groups[i];
                self.addChip('group', _t('Ledger acc.') + ' ' + g.key, [['account_group', '=', g.key]]);
            },
        });

        this._chart({
            key: 'monthly', type: 'bar',
            labels: _.map(s.monthly, function (m) { return self.periodLabel(m.key); }),
            datasets: [
                {label: _t('Expense'), backgroundColor: '#1f6f54',
                 data: _.map(s.monthly, function (m) { return m.base_amount; })},
                {label: _t('IGV'), backgroundColor: '#f2b441',
                 data: _.map(s.monthly, function (m) { return m.tax_amount; })},
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
            key: 'analytics', type: 'horizontalBar',
            labels: _.map(s.analytics, function (a) {
                return a.id ? self.short((a.code ? a.code + '  ' : '') + (a.name || ''), 36) : _t('Without cost center');
            }),
            datasets: [{
                label: _t('Expense'),
                backgroundColor: _.map(s.analytics, function (a) { return a.id ? '#3b82b8' : '#9fb3bd'; }),
                data: _.map(s.analytics, function (a) { return a.total; }),
            }],
            options: {scales: {xAxes: [this._axis()], yAxes: [this._catAxis()]}},
            onPick: function (i) {
                var a = s.analytics[i];
                if (a.id) {
                    self.addChip('analytic', _t('CC') + ' ' + self.short(a.name, 28),
                                 [['analytic_account_id', '=', a.id]]);
                } else {
                    self._kpiChip('no_cc');
                }
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
        } else if (kind === 'group') {
            this.addChip('group', _t('Ledger acc.') + ' ' + value, [['account_group', '=', value]]);
        } else if (kind === 'column') {
            this.addChip('column', value, [['register_column', '=', value]]);
        } else if (kind === 'analytic' && row.analytic_account_id) {
            this.addChip('analytic', _t('CC') + ' ' + this.short(row.analytic_account_id[1], 28),
                         [['analytic_account_id', '=', row.analytic_account_id[0]]]);
        } else {
            this._super.apply(this, arguments);
        }
    },
});

core.action_registry.add('fxo_expense_dashboard', ExpenseDashboard);

return ExpenseDashboard;

});
