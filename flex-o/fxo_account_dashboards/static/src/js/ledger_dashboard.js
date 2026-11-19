odoo.define('fxo_account_dashboards.LedgerDashboard', function (require) {
"use strict";

var core = require('web.core');
var DashboardBase = require('fxo_account_dashboards.DashboardBase');

var _t = core._t;
var _lt = core._lt;

var LedgerDashboard = DashboardBase.extend({
    model: 'fxo.ledger.line',
    dashTitle: _lt('Analytic Ledger'),
    dashIcon: 'fa-book',
    accountsFilter: true,
    extraFields: ['move_id', 'partner_id', 'analytic_account_id', 'is_opening'],
    chartSpecs: [
        {key: 'monthly', title: _lt('Debit and credit by month'), size: 'fxo-w-5'},
        {key: 'groups', title: _lt('Balance by ledger account (2 digits)'), size: 'fxo-w-7'},
        {key: 'accounts', title: _lt('Top 10 accounts by movement'), size: 'fxo-w-6'},
        {key: 'analytics', title: _lt('Top 10 cost centers'), size: 'fxo-w-6'},
    ],

    _kpiCards: function () {
        var k = this.summary.kpis;
        return [
            {label: _t('Debit'), value: this.money(k.debit), icon: 'fa-arrow-circle-down', tone: 'green',
             sub: this.fmtInt(k.count) + ' ' + _t('journal items')},
            {label: _t('Credit'), value: this.money(k.credit), icon: 'fa-arrow-circle-up', tone: 'amber',
             sub: this.fmtInt(k.vouchers) + ' ' + _t('vouchers')},
            {label: _t('Net movement'), value: this.money(k.net), icon: 'fa-exchange', tone: 'primary',
             sub: _t('Debit - Credit')},
            {label: _t('Opening balance'), value: this.money(k.opening), icon: 'fa-flag-o', tone: 'slate',
             sub: _t('Before the start date')},
            {label: _t('Closing balance'), value: this.money(k.closing), icon: 'fa-flag-checkered', tone: 'blue',
             sub: _t('Opening + movement')},
            {label: _t('Accounts'), value: this.fmtInt(k.accounts), icon: 'fa-sitemap', tone: 'violet',
             sub: _t('with movement or balance')},
        ];
    },

    rowClass: function (row) {
        return row.is_opening ? 'fxo-row-opening' : '';
    },

    _drawCharts: function () {
        var self = this;
        var s = this.summary;

        this._chart({
            key: 'monthly', type: 'bar',
            labels: _.map(s.monthly, function (m) { return self.periodLabel(m.key); }),
            datasets: [
                {label: _t('Debit'), backgroundColor: '#1f6f54',
                 data: _.map(s.monthly, function (m) { return m.debit; })},
                {label: _t('Credit'), backgroundColor: '#f2b441',
                 data: _.map(s.monthly, function (m) { return m.credit; })},
            ],
            options: {
                legend: {display: true, position: 'bottom'},
                scales: {xAxes: [this._catAxis()], yAxes: [this._axis()]},
            },
            onPick: function (i) {
                var m = s.monthly[i];
                self.addChip('period', self.periodLabel(m.key), [['period', '=', m.key]]);
            },
        });

        this._chart({
            key: 'groups', type: 'bar',
            labels: _.map(s.groups, function (g) { return g.key || '—'; }),
            datasets: [{
                label: _t('Balance'),
                backgroundColor: _.map(s.groups, function (g) { return g.balance >= 0 ? '#2f9e77' : '#e8703a'; }),
                data: _.map(s.groups, function (g) { return g.balance; }),
            }],
            options: {
                scales: {xAxes: [this._catAxis()], yAxes: [this._axis()]},
                tooltips: {
                    callbacks: {
                        title: function (items) {
                            var g = s.groups[items[0].index];
                            return (g.key || '—') + '  ' + (g.name || '');
                        },
                        label: function (item) {
                            var g = s.groups[item.index];
                            return [_t('Balance') + ': ' + self.fmt(g.balance),
                                    _t('Debit') + ': ' + self.fmt(g.debit),
                                    _t('Credit') + ': ' + self.fmt(g.credit)];
                        },
                    },
                },
            },
            onPick: function (i) {
                var g = s.groups[i];
                self.addChip('group', _t('Ledger acc.') + ' ' + g.key, [['account_group', '=', g.key]]);
            },
        });

        this._chart({
            key: 'accounts', type: 'horizontalBar',
            labels: _.map(s.accounts, function (a) { return a.key + '  ' + self.short(a.name, 30); }),
            datasets: [
                {label: _t('Debit'), backgroundColor: '#1f6f54',
                 data: _.map(s.accounts, function (a) { return a.debit; })},
                {label: _t('Credit'), backgroundColor: '#f2b441',
                 data: _.map(s.accounts, function (a) { return a.credit; })},
            ],
            options: {
                legend: {display: true, position: 'bottom'},
                scales: {xAxes: [this._axis()], yAxes: [this._catAxis()]},
            },
            onPick: function (i) {
                var a = s.accounts[i];
                self.addChip('account', _t('Account') + ' ' + a.key, [['account_code', '=', a.key]]);
            },
        });

        this._chart({
            key: 'analytics', type: 'horizontalBar',
            labels: _.map(s.analytics, function (a) {
                return self.short((a.code ? a.code + '  ' : '') + (a.name || ''), 36);
            }),
            datasets: [{
                label: _t('Balance'),
                backgroundColor: _.map(s.analytics, function (a) { return a.balance >= 0 ? '#3b82b8' : '#e8703a'; }),
                data: _.map(s.analytics, function (a) { return a.balance; }),
            }],
            options: {scales: {xAxes: [this._axis()], yAxes: [this._catAxis()]}},
            onPick: function (i) {
                var a = s.analytics[i];
                self.addChip('analytic', _t('CC') + ' ' + self.short(a.name, 28),
                             [['analytic_account_id', '=', a.id]]);
            },
        });
    },

    _followLink: function (kind, row, value) {
        if (kind === 'account') {
            this.addChip('account', _t('Account') + ' ' + value, [['account_code', '=', value]]);
        } else if (kind === 'group') {
            this.addChip('group', _t('Ledger acc.') + ' ' + value, [['account_group', '=', value]]);
        } else if (kind === 'analytic' && row.analytic_account_id) {
            this.addChip('analytic', _t('CC') + ' ' + this.short(row.analytic_account_id[1], 28),
                         [['analytic_account_id', '=', row.analytic_account_id[0]]]);
        } else {
            this._super.apply(this, arguments);
        }
    },
});

core.action_registry.add('fxo_ledger_dashboard', LedgerDashboard);

return LedgerDashboard;

});
