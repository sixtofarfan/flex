odoo.define('odoo13.CurrencyRate', function (require) {
    'use strict';

    var core = require('web.core');
    var session = require('web.session');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var Qweb = core.qweb;
    var _t = core._t;

    var CurrencyRate = Widget.extend({
        name: 'currency_rate_menu',
        template: 'odoo13.CurrencyRate',
        events: {
            "click .o_update_rate": "_onUpdateRateClick",
            "click .o_update_rate_range": "_onUpdateRateRangeClick",
            "click .o_show_rates": "_onShowRatesClick",
            'show.bs.dropdown': '_onCurrencyRateShow',
            'hide.bs.dropdown': '_onCurrencyRateHide',
        },
        start: async function() {
            var self = this;
            await Promise.all([this._super.apply(this, arguments),
            this._getCurrencyRateData()]);
            self.$('.o_exchange_rate').addClass(self.currency_rate_data['rate']);
            self.$('.o_exchange_rate').text(self.currency_rate_data['rate']);
            self.$('.currency_rate_date').text(self.currency_rate_data['date']);
            self.$('.currency_rate_sell').text(self.currency_rate_data['sell']);
            self.$('.currency_rate_buy').text(self.currency_rate_data['buy']);
        },
        _getCurrencyRateData: function() {
            var self = this;
            var dt = new Date();
            return this._rpc({
                model: 'res.currency.rate',
                method: 'get_systray_dict',
                args: [self.id, dt],
                kwargs: {context: session.user_context},
            }).then(function (data) {
                self.currency_rate_data = data;
            })
        },
        _onCurrencyRateShow: function () {
            document.body.classList.add('modal-open');
            this.start();
        },
        _onCurrencyRateHide: function () {
            document.body.classList.remove('modal-open');
        },
        _onUpdateRateClick: async function() {
            await Promise.all([this._onUpdateRatePromise()]);
            this.start();
        },
        _onUpdateRateRangeClick: async function() {
            await Promise.all([this._onUpdateRateRangePromise()]);
            this.start();
            this._onUpdateRateClick();
        },
        _onShowRatesClick: async function() {
            await Promise.all([this._onShowRatesPromise()]);
            this.start();
        },
        _onUpdateRatePromise: function() {
            var self = this;
            return this._rpc({
                model: 'res.company',
                method: 'update_currency_rates_sunat',
                args: [self.id],
                kwargs: {context: session.user_context},
            })
        },
        _onUpdateRateRangePromise: function() {
            var self = this;
            self.do_action({
                name: 'Update range',
                type: 'ir.actions.act_window',
                res_model: 'range.wizard',
                view_type: 'form',
                view_mode: 'form',
                view_id: 'view_range_wizard',
                views: [[false, 'form'],],
                target: 'new'
            });
        },
        _onShowRatesPromise: function() {
            var self = this;
            self.do_action({
                name: _t('Currency rates'),
                type: 'ir.actions.act_window',
                res_model: 'res.currency.rate',
                view_type: 'list',
                view_mode: 'list',
                view_id: 'base.view_currency_rate_tree',
                views: [[false, 'list'],],
                // Se debe obtener el id de la moneda dolares para no
                // tenerlo en duro en el código. Ya que el id de la
                // moneda 'USD' puede cambiar.
                domain: [['currency_id','=', 2]],
                context: {default_currency_id: 2},
                target: 'current'
            });
        },
    });
    CurrencyRate.prototype.sequence = 100;
    SystrayMenu.Items.push(CurrencyRate);

    return CurrencyRate;
});
// /** @odoo-module **/
// import { Dropdown } from "@web/core/dropdown/dropdown";
// import { DropdownGroup } from "@web/core/dropdown/dropdown_group";
// import { DropdownItem } from "@web/core/dropdown/dropdown_item";
// import { CheckBox } from "@web/core/checkbox/checkbox";
// import { registry } from "@web/core/registry";
// import { Component, useState } from "@odoo/owl";
// import { useService } from "@web/core/utils/hooks";
// import { _t } from "@web/core/l10n/translation";
// //import { v4 as uuidv4 } from "uuid";

// function generateKey() {
//     return Date.now().toString() + Math.random().toString(36).substr(2, 5);
// }

// const rateMenuRegistry = registry.category("rate_menuitems");

// class CurrencySystray extends Component {
//     static components = { DropdownGroup, Dropdown, DropdownItem, CheckBox };
//     static props = {};

//     setup() {
//         super.setup(...arguments);
//         this.orm = useService("orm");
//         this.state = useState({
//             exchangeRate: 0.0,
//             date_rate: '',
//             refreshKey: Date.now(),
//         });
//         this.loadExchangeRate();
//     }

//     async loadExchangeRate() {
//         let rate = 0;
//         var date_rate ='';
//         try {
//             rate = await this.orm.call(
//                 "res.currency",
//                 "systray_get_currency_rate",
//             );
//             date_rate = await this.orm.call(
//                 "res.currency",
//                 "systray_get_currency_and_date"
//             );

//             this.state.exchangeRate = rate.toFixed(3) || 0.0;
//             this.state.date_rate = date_rate
//             this.state.refreshKey = generateKey();
//         } catch (error) {
//             console.error("Error al cargar la tasa de cambio:", error);
//         }
//     }

//     get elements() {
//         return rateMenuRegistry
//             .getAll()
//             .map((element) => element(this.env, this.state))
//             .filter((element) => (element.show ? element.show() : true))
//             .sort((x, y) => {
//                 const xSeq = x.sequence ? x.sequence : 100;
//                 const ySeq = y.sequence ? y.sequence : 100;
//                 return xSeq - ySeq;
//             });
//         // return sortedItems;
//     }

// }

// CurrencySystray.template = "systray_icon";
// export const systrayItem = { Component: CurrencySystray,};
// registry.category("systray").add("CurrencySystray", systrayItem, { sequence: 100 });

// function dateItem(env, state) {
//     return {
//         type: "item",
//         description: state.date_rate,
//         sequence: 10,
//     };
// }

// function separator(env, state) {
//     return {
//         type: "separator",
//         sequence: 20,
//     };
// }

// function updateRateManuallyItem(env, state) {
//     return {
//         type: "item",
//         id: "updateRateManually",
//         description: _t("Update currency rate Manually"),
//         callback: async function () {
//             env.services.action.doAction({
//                 name: 'Update rate manually',
//                 type: 'ir.actions.act_window',
//                 res_model: 'manual.wizard',
//                 view_type: 'form',
//                 view_mode: 'form',
//                 view_id: 'view_manual_wizard',
//                 views: [[false, 'form'],],
//                 target: 'new'
//             });
//         },
//         sequence: 30,
//     };
// }

// function updateRateItem(env, state) {
//     return {
//         type: "item",
//         id: "updateRate",
//         description: _t("Update currency rate"),
//         callback: async function () {
//             let rate = 0;
//             rate = await env.services.orm.call("res.currency", "update_systray_get_currency_rate");
//             if (rate > 0) {
//                 state.exchangeRate = rate.toFixed(3);
//             }

//             const date_rate = await env.services.orm.call("res.currency", "systray_get_currency_and_date");
//             state.date_rate = date_rate;
//         },
//         sequence: 40,
//     };
// }

// function updateRangeItem(env, state) {
//     return {
//         type: "item",
//         id: "updateRange",
//         description: _t("Update Range"),
//         callback: async function () {
//             env.services.action.doAction({
//                 name: 'Update range',
//                 type: 'ir.actions.act_window',
//                 res_model: 'range.wizard',
//                 view_type: 'form',
//                 view_mode: 'form',
//                 view_id: 'view_range_wizard',
//                 views: [[false, 'form'],],
//                 target: 'new'
//             });
//         },
//         sequence: 50,
//     };
// }

// function currencyRatesItem(env, state) {
//     return {
//         type: "item",
//         id: "showRates",
//         description: _t("Currency Rates"),
//         callback: async function () {
//             const actionDescription = await env.services.orm.call("res.currency", "action_get");
//             env.services.action.doAction(actionDescription);
//         },
//         sequence: 60,
//     };
// }

// registry
//     .category("rate_menuitems")
//     .add("date", dateItem)
//     .add("separator", separator)
//     .add("updateRateManually", updateRateManuallyItem)
//     .add("updateRate", updateRateItem)
//     .add("updateRange", updateRangeItem)
//     .add("showRates", currencyRatesItem)