odoo.define('fxo_account_dashboards.DashboardBase', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var framework = require('web.framework');
var session = require('web.session');

var QWeb = core.qweb;
var _t = core._t;

var PALETTE = ['#1f6f54', '#2f9e77', '#7cc7a4', '#f2b441', '#e8703a', '#3b82b8', '#7a5ea8', '#c0504d',
               '#5f7d8c', '#9bbb59', '#d98880', '#48a9a6'];

/**
 * Base of the accounting dashboards: filter bar (company, fiscal year, dates,
 * currency), KPI cards, charts that filter the data when clicked and a paged,
 * sortable and searchable table with links to the source records.
 * The rows live in a server model, loaded per user with `fxo_load`.
 */
var DashboardBase = AbstractAction.extend({
    template: 'fxo_dashboards.Root',
    jsLibs: ['/web/static/lib/Chart/Chart.js'],
    events: {
        'click .fxo-apply': '_onApply',
        'change .fxo-f-company': '_onCompanyChange',
        'change .fxo-f-year': '_onYearChange',
        'click .fxo-month': '_onMonth',
        'click .fxo-mode button': '_onMode',
        'change .fxo-f-pfrom, .fxo-f-pto': '_onPeriodChange',
        'click .fxo-range button': '_onRange',
        'click .fxo-currency button': '_onCurrency',
        'keydown .fxo-filterbar input': '_onFilterKey',
        'keydown .fxo-search-input': '_onSearchKey',
        'click .fxo-search-go': '_onSearch',
        'click .fxo-search-clear': '_onSearchClear',
        'click .fxo-chip-remove': '_onChipRemove',
        'click .fxo-chips-clear': '_onChipsClear',
        'click th.fxo-sortable': '_onSort',
        'click .fxo-link': '_onLink',
        'click .fxo-prev': '_onPrev',
        'click .fxo-next': '_onNext',
        'change .fxo-page-size': '_onPageSize',
        'click .fxo-open-list': '_onOpenList',
        'click .fxo-export': '_onExport',
        'click .fxo-kpi[data-chip]': '_onKpiChip',
    },

    // ---- to define in each dashboard --------------------------------------
    model: null,
    dashTitle: '',
    dashSubtitle: '',
    dashIcon: 'fa-bar-chart',
    accountsFilter: false,      // show the "accounts" input in the filter bar
    extraFields: [],            // fields read besides the visible columns
    chartSpecs: [],             // [{key, title, size}]

    init: function (parent, action) {
        this._super.apply(this, arguments);
        this.actionParams = (action && action.params) || {};
        this.charts = {};
        this.filters = {};
        this.chips = [];
        this.search = {field: '', text: ''};
        this.pager = {offset: 0, limit: 80, total: 0};
        this.order = null;
        this.rows = [];
        this.summary = null;
        this.loaded = false;
    },

    willStart: function () {
        var self = this;
        var options = this._rpc({model: this.model, method: 'fxo_options'}).then(function (result) {
            self.options = result;
            self._initFilters();
        });
        return Promise.all([this._super.apply(this, arguments), ajax.loadLibs(this), options]);
    },

    start: function () {
        var self = this;
        this.$el.html(QWeb.render('fxo_dashboards.Layout', {widget: this}));
        this._syncFilterBar();
        return this._super.apply(this, arguments).then(function () {
            self._load();
        });
    },

    destroy: function () {
        this._destroyCharts();
        this._super.apply(this, arguments);
    },

    // ---- filters ----------------------------------------------------------
    _initFilters: function () {
        var o = this.options;
        var p = this.actionParams;
        // After a page reload the params come back from the URL (numbers / strings mixed)
        var company = parseInt(p.company_id, 10) || o.company_id;
        if (!_.findWhere(o.companies, {id: company})) {
            company = o.company_id;
        }
        var year = parseInt(p.year, 10) || (o.defaults[company] && o.defaults[company].year) || o.year;
        var now = new Date();
        var lastMonth = now.getFullYear() === year ? now.getMonth() + 1 : 12;
        this.filters = {
            company_id: company,
            year: year,
            currency: p.currency === 'usd' ? 'usd' : 'pen',
            accounts: p.accounts ? String(p.accounts) : '',
            // Like the 19.0 dashboards: by accounting periods by default (01 .. current month)
            mode: (p.mode === 'date' || (!p.mode && p.date_from)) ? 'date' : 'period',
            period_from: p.period_from ? String(p.period_from) : year + '01',
            period_to: p.period_to ? String(p.period_to) : year + this._pad(lastMonth),
            date_from: p.date_from ? String(p.date_from) : year + '-01-01',
            date_to: p.date_to ? String(p.date_to) : this._monthRange(year, lastMonth)[1],
        };
    },

    _pad: function (n) { return (n < 10 ? '0' : '') + n; },

    _monthRange: function (year, month) {
        var last = new Date(year, month, 0).getDate();
        return [year + '-' + this._pad(month) + '-01', year + '-' + this._pad(month) + '-' + this._pad(last)];
    },

    /** Default range of a fiscal year: 01 .. current month (or 12 for past years). */
    _resetYear: function (year) {
        var now = new Date();
        var lastMonth = now.getFullYear() === year ? now.getMonth() + 1 : 12;
        var f = this.filters;
        f.year = year;
        f.period_from = year + '01';
        f.period_to = year + this._pad(lastMonth);
        f.date_from = year + '-01-01';
        f.date_to = this._monthRange(year, lastMonth)[1];
    },

    periodChoices: function () {
        var months = [_t('January'), _t('February'), _t('March'), _t('April'), _t('May'), _t('June'), _t('July'),
                      _t('August'), _t('September'), _t('October'), _t('November'), _t('December')];
        var choices = [{code: '00', label: '00 · ' + _t('Opening')}];
        for (var m = 1; m <= 12; m++) {
            choices.push({code: this._pad(m), label: this._pad(m) + ' · ' + months[m - 1]});
        }
        choices.push({code: '13', label: '13 · ' + _t('Closing')});
        return choices;
    },

    _syncFilterBar: function () {
        var f = this.filters;
        this.$('.fxo-f-company').val(f.company_id);
        this.$('.fxo-f-year').val(f.year);
        this.$('.fxo-f-from').val(f.date_from);
        this.$('.fxo-f-to').val(f.date_to);
        this.$('.fxo-f-accounts').val(f.accounts);
        this.$('.fxo-f-pfrom').val(String(f.period_from).substr(4));
        this.$('.fxo-f-pto').val(String(f.period_to).substr(4));
        this.$('.fxo-mode button').removeClass('active').filter('[data-mode="' + f.mode + '"]').addClass('active');
        this.$('.fxo-only-period').toggleClass('d-none', f.mode !== 'period');
        this.$('.fxo-only-date').toggleClass('d-none', f.mode !== 'date');
        var range = String(f.period_from).substr(4) + '-' + String(f.period_to).substr(4);
        this.$('.fxo-range button').each(function () {
            $(this).toggleClass('active', $(this).data('range') === range);
        });
        this.$('.fxo-currency button').removeClass('active')
            .filter('[data-currency="' + f.currency + '"]').addClass('active');
        var year = parseInt(f.year, 10);
        var self = this;
        this.$('.fxo-month').each(function () {
            var m = parseInt($(this).data('month'), 10);
            var active;
            if (m === 0) {
                active = f.date_from === year + '-01-01' && f.date_to === year + '-12-31';
            } else {
                var r = self._monthRange(year, m);
                active = f.date_from === r[0] && f.date_to === r[1];
            }
            $(this).toggleClass('active', active);
        });
    },

    _readFilterBar: function () {
        this.filters.company_id = parseInt(this.$('.fxo-f-company').val(), 10);
        this.filters.year = parseInt(this.$('.fxo-f-year').val(), 10);
        this.filters.date_from = this.$('.fxo-f-from').val();
        this.filters.date_to = this.$('.fxo-f-to').val();
        this.filters.period_from = this.filters.year + this.$('.fxo-f-pfrom').val();
        this.filters.period_to = this.filters.year + this.$('.fxo-f-pto').val();
        if (this.accountsFilter) {
            this.filters.accounts = this.$('.fxo-f-accounts').val() || '';
        }
    },

    _onMode: function (ev) {
        this._readFilterBar();
        this.filters.mode = $(ev.currentTarget).data('mode');
        this._syncFilterBar();
        this._load();
    },

    _onPeriodChange: function (ev) {
        this._readFilterBar();
        var f = this.filters;
        if (f.period_from > f.period_to) {
            if ($(ev.currentTarget).hasClass('fxo-f-pfrom')) {
                f.period_to = f.period_from;
            } else {
                f.period_from = f.period_to;
            }
        }
        this._syncFilterBar();
        this._load();
    },

    _onRange: function (ev) {
        this._readFilterBar();
        var range = String($(ev.currentTarget).data('range')).split('-');
        this.filters.period_from = this.filters.year + range[0];
        this.filters.period_to = this.filters.year + range[1];
        this._syncFilterBar();
        this._load();
    },

    _onApply: function () {
        this._readFilterBar();
        this._load();
    },

    _onFilterKey: function (ev) {
        if (ev.which === 13) {
            this._onApply();
        }
    },

    _onCompanyChange: function () {
        this._readFilterBar();
        var def = this.options.defaults[this.filters.company_id];
        if (def) {
            this._resetYear(def.year);
        }
        this._syncFilterBar();
        this._load();
    },

    _onYearChange: function () {
        this._readFilterBar();
        this._resetYear(parseInt(this.$('.fxo-f-year').val(), 10));
        this._syncFilterBar();
        this._load();
    },

    _onMonth: function (ev) {
        var month = parseInt($(ev.currentTarget).data('month'), 10);
        this.filters.year = parseInt(this.$('.fxo-f-year').val(), 10);
        if (month === 0) {
            this.filters.date_from = this.filters.year + '-01-01';
            this.filters.date_to = this.filters.year + '-12-31';
        } else {
            var range = this._monthRange(this.filters.year, month);
            this.filters.date_from = range[0];
            this.filters.date_to = range[1];
        }
        if (this.accountsFilter) {
            this.filters.accounts = this.$('.fxo-f-accounts').val() || '';
        }
        this._syncFilterBar();
        this._load();
    },

    _onCurrency: function (ev) {
        this._readFilterBar();
        this.filters.currency = $(ev.currentTarget).data('currency');
        this._syncFilterBar();
        this._load();
    },

    // ---- data -------------------------------------------------------------
    _busy: function (on) {
        this.$('.fxo-loading').toggleClass('d-none', !on);
    },

    _load: function () {
        var self = this;
        this._busy(true);
        this.chips = [];
        this.search.text = '';
        this.$('.fxo-search-input').val('');
        this.pager.offset = 0;
        var filters = _.extend({}, this.filters, {by_period: this.filters.mode === 'period'});
        return this._rpc({model: this.model, method: 'fxo_load', args: [filters]}).then(function () {
            self.loaded = true;
            self._syncFilterBar();
            return self._refresh();
        }).guardedCatch(function () {
            self._busy(false);
        });
    },

    _domain: function () {
        var domain = [];
        _.each(this.chips, function (chip) {
            domain = domain.concat(chip.domain);
        });
        var text = (this.search.text || '').trim();
        if (text) {
            var fields = this.search.field ? [this.search.field] : _.pluck(this.options.search_fields, 'name');
            for (var i = 0; i < fields.length - 1; i++) {
                domain.push('|');
            }
            _.each(fields, function (name) {
                domain.push([name, 'ilike', text]);
            });
        }
        return domain;
    },

    _refresh: function () {
        var self = this;
        this._busy(true);
        this.pager.offset = 0;
        var domain = this._domain();
        var summary = this._rpc({
            model: this.model, method: 'fxo_summary', args: [domain, this.filters.currency],
        }).then(function (result) {
            self.summary = result;
        });
        return Promise.all([summary, this._fetchRows(true)]).then(function () {
            self._renderKpis();
            self._renderChips();
            self._renderTable();
            self._renderCharts();
            self._busy(false);
        }).guardedCatch(function () {
            self._busy(false);
        });
    },

    _fetchRows: function (silent) {
        var self = this;
        var fields = _.pluck(this.options.columns, 'name').concat(this.extraFields);
        return this._rpc({
            model: this.model, method: 'fxo_rows',
            args: [this._domain(), fields, this.pager.offset, this.pager.limit, this.order],
        }).then(function (result) {
            self.rows = result.records;
            self.pager.total = result.length;
            if (!silent) {
                self._renderTable();
            }
        });
    },

    // ---- formatting -------------------------------------------------------
    fmt: function (value, decimals) {
        var n = Number(value || 0);
        decimals = decimals === undefined ? 2 : decimals;
        var parts = Math.abs(n).toFixed(decimals).split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        return (n < 0 ? '-' : '') + parts.join('.');
    },

    fmtInt: function (value) {
        return this.fmt(value, 0);
    },

    symbol: function () {
        return this.filters.currency === 'usd' ? 'US$' : 'S/';
    },

    money: function (value) {
        return this.symbol() + ' ' + this.fmt(value);
    },

    compact: function (value) {
        var n = Number(value || 0);
        var abs = Math.abs(n);
        if (abs >= 1e6) { return this.fmt(n / 1e6, 2) + ' M'; }
        if (abs >= 1e3) { return this.fmt(n / 1e3, 1) + ' K'; }
        return this.fmt(n, 0);
    },

    fmtDate: function (value) {
        if (!value) { return ''; }
        var p = String(value).split('-');
        return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : value;
    },

    monthNames: function () {
        return [_t('Jan'), _t('Feb'), _t('Mar'), _t('Apr'), _t('May'), _t('Jun'),
                _t('Jul'), _t('Aug'), _t('Sep'), _t('Oct'), _t('Nov'), _t('Dec')];
    },

    periodLabel: function (period) {
        if (!period || period.length !== 6) { return period || ''; }
        var mm = period.substr(4, 2);
        if (mm === '00') { return _t('Opening'); }
        if (mm === '13') { return _t('Closing'); }
        return this.monthNames()[parseInt(mm, 10) - 1] + ' ' + period.substr(0, 4);
    },

    cell: function (col, row) {
        var value = row[col.name];
        if (col.type === 'number') { return this.fmt(value); }
        if (col.type === 'rate') { return value ? this.fmt(value, 4) : ''; }
        if (col.type === 'date') { return this.fmtDate(value); }
        if (value === false || value === null || value === undefined) { return ''; }
        return value;
    },

    cellClass: function (col, row) {
        var cls = [];
        if (col.type === 'number' || col.type === 'rate') {
            cls.push('fxo-num');
            if (Number(row[col.name] || 0) < 0) { cls.push('fxo-neg'); }
        }
        return cls.join(' ');
    },

    /** Pieces of a cell rendered as links ([{text, value}]); null = plain text. */
    cellLinks: function (col, row) {
        var value = row[col.name];
        if (!col.link || value === false || value === null || value === '') { return null; }
        if (col.link === 'move' && !row.move_id) { return null; }
        if (col.link === 'partner' && !row.partner_id) { return null; }
        if (col.link === 'account' && col.name === 'account_codes') {
            return _.map(String(value).split(','), function (code) {
                return {text: code.trim(), value: code.trim()};
            });
        }
        return [{text: value, value: value}];
    },

    rowClass: function (row) {
        return '';
    },

    subtitle: function () {
        var f = this.filters;
        var company = _.findWhere(this.options.companies, {id: f.company_id});
        var range = f.mode === 'period'
            ? _t('Periods') + ' ' + String(f.period_from).substr(0, 4) + '-' + String(f.period_from).substr(4) +
              ' – ' + String(f.period_to).substr(0, 4) + '-' + String(f.period_to).substr(4)
            : this.fmtDate(f.date_from) + ' – ' + this.fmtDate(f.date_to);
        return (company ? company.name : '') + '  ·  ' + range + '  ·  ' + (f.currency === 'usd' ? 'USD' : 'PEN');
    },

    // ---- rendering --------------------------------------------------------
    _kpiCards: function () {
        return [];
    },

    _renderKpis: function () {
        this.$('.fxo-kpis').html(QWeb.render('fxo_dashboards.Kpis', {widget: this, cards: this._kpiCards()}));
        this.$('.fxo-subtitle').text(this.subtitle());
    },

    _renderChips: function () {
        this.$('.fxo-chips').html(QWeb.render('fxo_dashboards.Chips', {widget: this}));
    },

    _renderTable: function () {
        var scroll = this.$('.fxo-table-wrap').scrollLeft();
        this.$('.fxo-table-zone').html(QWeb.render('fxo_dashboards.Table', {widget: this}));
        this.$('.fxo-table-wrap').scrollLeft(scroll);
    },

    _destroyCharts: function () {
        _.each(this.charts, function (chart) {
            chart.destroy();
        });
        this.charts = {};
    },

    _renderCharts: function () {
        this._destroyCharts();
        this._drawCharts();
    },

    _drawCharts: function () {},

    _canvas: function (key) {
        var $box = this.$('.fxo-chart[data-key="' + key + '"] .fxo-chart-body');
        $box.empty();
        var $canvas = $('<canvas/>').appendTo($box);
        return $canvas[0].getContext('2d');
    },

    _emptyChart: function (key) {
        this.$('.fxo-chart[data-key="' + key + '"] .fxo-chart-body')
            .html($('<div class="fxo-empty"/>').text(_t('No data for this selection')));
    },

    _chartOptions: function (extra) {
        var self = this;
        var base = {
            maintainAspectRatio: false,
            legend: {display: false, labels: {boxWidth: 12, fontSize: 11}},
            tooltips: {
                callbacks: {
                    label: function (item, data) {
                        var ds = data.datasets[item.datasetIndex];
                        var value = ds.data[item.index];
                        var label = ds.label || data.labels[item.index] || '';
                        return label + ': ' + self.fmt(value);
                    },
                },
            },
        };
        return $.extend(true, base, extra || {});
    },

    _axis: function (stacked) {
        var self = this;
        return {
            stacked: !!stacked,
            gridLines: {color: 'rgba(0,0,0,0.06)', zeroLineColor: 'rgba(0,0,0,0.25)'},
            ticks: {
                fontSize: 10, beginAtZero: true,
                callback: function (value) { return typeof value === 'number' ? self.compact(value) : value; },
            },
        };
    },

    _catAxis: function (stacked) {
        return {stacked: !!stacked, gridLines: {display: false}, ticks: {fontSize: 10}};
    },

    /** Common chart builder. cfg: {key, type, labels, datasets, options, onPick(index)} */
    _chart: function (cfg) {
        if (!cfg.labels.length) {
            this._emptyChart(cfg.key);
            return;
        }
        var options = this._chartOptions(cfg.options);
        if (cfg.onPick) {
            options.onClick = function (ev, elements) {
                if (elements && elements.length) {
                    cfg.onPick(elements[0]._index);
                }
            };
            options.hover = {
                onHover: function (ev, elements) {
                    ev.target.style.cursor = elements && elements.length ? 'pointer' : 'default';
                },
            };
        }
        this.charts[cfg.key] = new Chart(this._canvas(cfg.key), {
            type: cfg.type, data: {labels: cfg.labels, datasets: cfg.datasets}, options: options,
        });
    },

    palette: function (n) {
        var colors = [];
        for (var i = 0; i < n; i++) { colors.push(PALETTE[i % PALETTE.length]); }
        return colors;
    },

    short: function (text, max) {
        text = text || '';
        return text.length > max ? text.substr(0, max - 1) + '…' : text;
    },

    // ---- chips / search ---------------------------------------------------
    addChip: function (key, label, domain) {
        var existing = _.findWhere(this.chips, {key: key});
        if (existing && _.isEqual(existing.domain, domain)) {
            this.chips = _.without(this.chips, existing);    // click again = remove
        } else {
            this.chips = _.reject(this.chips, function (c) { return c.key === key; });
            this.chips.push({key: key, label: label, domain: domain});
        }
        this._refresh();
    },

    _onChipRemove: function (ev) {
        var key = $(ev.currentTarget).data('key');
        this.chips = _.reject(this.chips, function (c) { return c.key === key; });
        this._refresh();
    },

    _onChipsClear: function () {
        this.chips = [];
        this.search.text = '';
        this.$('.fxo-search-input').val('');
        this._refresh();
    },

    _onKpiChip: function (ev) {
        this._kpiChip($(ev.currentTarget).data('chip'));
    },

    _kpiChip: function () {},

    _onSearch: function () {
        this.search.field = this.$('.fxo-search-field').val();
        this.search.text = this.$('.fxo-search-input').val();
        this._refresh();
    },

    _onSearchKey: function (ev) {
        if (ev.which === 13) {
            this._onSearch();
        }
    },

    _onSearchClear: function () {
        this.$('.fxo-search-input').val('');
        this._onSearch();
    },

    // ---- table ------------------------------------------------------------
    _onSort: function (ev) {
        var field = $(ev.currentTarget).data('field');
        if (this.order && this.order.field === field) {
            this.order = this.order.dir === 'asc' ? {field: field, dir: 'desc'} : null;
        } else {
            this.order = {field: field, dir: 'asc'};
        }
        this.pager.offset = 0;
        this._fetchRows();
    },

    _onPrev: function () {
        if (this.pager.offset > 0) {
            this.pager.offset = Math.max(0, this.pager.offset - this.pager.limit);
            this._fetchRows();
        }
    },

    _onNext: function () {
        if (this.pager.offset + this.pager.limit < this.pager.total) {
            this.pager.offset += this.pager.limit;
            this._fetchRows();
        }
    },

    _onPageSize: function (ev) {
        this.pager.limit = parseInt($(ev.currentTarget).val(), 10);
        this.pager.offset = 0;
        this._fetchRows();
    },

    _onLink: function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        var row = this.rows[parseInt($link.closest('tr').data('index'), 10)];
        if (!row) { return; }
        this._followLink($link.data('link'), row, String($link.data('value')));
    },

    _followLink: function (kind, row, value) {
        if (kind === 'move' && row.move_id) {
            this._openRecord('account.move', row.move_id[0]);
        } else if (kind === 'partner' && row.partner_id) {
            this._openRecord('res.partner', row.partner_id[0]);
        }
    },

    _openRecord: function (model, id) {
        this.do_action({
            type: 'ir.actions.act_window', res_model: model, res_id: id,
            views: [[false, 'form']], target: 'current',
        });
    },

    _onOpenList: function () {
        this.do_action({
            type: 'ir.actions.act_window', name: String(this.dashTitle),
            res_model: this.model, domain: this._domain(),
            views: [[false, 'list'], [false, 'pivot'], [false, 'graph']], target: 'current',
        });
    },

    _onExport: function (ev) {
        var fmt = $(ev.currentTarget).data('fmt');
        var company = _.findWhere(this.options.companies, {id: this.filters.company_id});
        framework.blockUI();
        session.get_file({
            url: '/fxo_dashboards/export',
            data: {
                model: this.model, fmt: fmt, domain: JSON.stringify(this._domain()),
                meta: JSON.stringify({
                    title: String(this.dashTitle), company: company ? company.name : '', subtitle: this.subtitle(),
                }),
            },
            complete: framework.unblockUI,
            error: function () {
                framework.unblockUI();
            },
        });
    },
});

return DashboardBase;

});
