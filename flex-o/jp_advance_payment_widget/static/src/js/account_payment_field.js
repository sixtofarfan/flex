odoo.define('jp_advance_payment_widget.payment', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var field_utils = require('web.field_utils');
    var account_payment = require('account.payment');

    var QWeb = core.qweb;

    account_payment.ShowPaymentLineWidget.include({
        events: _.extend({
            'click .outstanding_credit_assign': '_dummyEventListener',
            'change input[id="payment_date"]': '_OnChangeDate',
        }, AbstractField.prototype.events),

        _render: async function() {
            this._super.apply(this, arguments);
            var self = this;
            var info = JSON.parse(this.value);
            var currency_rate = this.recordData.currency_rate;
            var invoice_date = this.recordData.date._i;
            // var invoice_date = this.recordData.invoice_date._i;
            // Funcion para obtener el tipo de cambio de la fecha
            currency_rate = await Promise.all([this._rpc({
                model: 'account.move',
                method: 'get_currency_rate',
                args: [this.recordData.id, this.recordData.date._i],
            })]);
            if (!info) {
                this.$el.html('');
                return;
            }
            _.each(info.content, function (k, v){
                k.index = v;
                k.rate = field_utils.format.float(k.rate, {digits: k.digits});
                if (k.date){
                    k.date = field_utils.format.date(field_utils.parse.date(k.date, {}, {isUTC: true}));
                }
            });
            _.each(this.$('.outstanding_credit_assign'), function(k, v){
                var content = info.content[v];  
                var options = {
                    content: function () {
                        var $content = $(QWeb.render('PaymentCurrencyRatePopOver', {
                            id: content.id,
                            date: invoice_date,
                            // content.date,
                            rate: currency_rate,
                            // content.currency_rate,
                        }));
                        $content.filter('.js_payment_rate').on('click', self._onOutstandingCreditAssign.bind(self));
                        return $content;
                    },
                    html: true,
                    placement: function() { return $(window).width() <= 1080 ? 'bottom' : 'left'; },
                    title: 'Enter date and currency rate',
                    trigger: 'click',
                    delay: { "show": 0, "hide": 100 },
                    container: $(k).parent(),
                };
                // console.log("********************");
                // console.log(invoice_date);
                // console.log(currency_rate);
                // // console.log(value_rate);
                // console.log(content);
                // console.log("********************");
                $(k).popover(options);
                $(k).on('shown.bs.popover', function() {
                    // console.log("********************");
                    // console.log(currency_rate);
                    // console.log("********************");
                    document.getElementById("payment_date").placeholder = $(this).parent().find('#payment_date').attr('date')
                    document.getElementById("currency_rate").placeholder = $(this).parent().find('#currency_rate').attr('rate')
                });
            });
        },
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        _renderCreate: function (state) {
            var self = this;
            return this.model.makeRecord('account.payment', [{
                relation: 'account.journal',
                type: 'many2one',
                name: 'journal_id',
                domain: [['company_id', '=', state.st_line.company_id]],
            }], {
                amount: {string: _t("Account")},
            }).then(function (recordID) {
                self.handleCreateRecord = recordID;
                var record = self.model.get(self.handleCreateRecord);
    
                self.fields.journal_id = new relational_fields.FieldMany2One(self,
                    'journal_id', record, {mode: 'edit'});
    
                var $create = $(qweb.render("reconciliation.line.create", {'state': state, 'group_tags': self.group_tags, 'group_acc': self.group_acc}));
                self.fields.journal_id.appendTo($create.find('.create_journal_id .o_td_field'));
                self.$('.create').append($create);
    
                function addRequiredStyle(widget) {
                    widget.$el.addClass('o_required_modifier');
                }
            });
        },
    
        /**
         * @private
         * @override
         * @param {MouseEvent} event
         */
        _onOutstandingCreditAssign: function (event) {
            var self = this;
            var id = parseInt($(event.target).attr('id'), 10);
            var custom_payment_date = document.getElementById("payment_date").value;
            var custom_currency_rate = parseFloat(document.getElementById("currency_rate").value) || 0.0;
            var context = {
                'payment_date': custom_payment_date,
                'currency_rate': custom_currency_rate,
            }
            this._rpc({
                model: 'account.move',
                method: 'js_assign_outstanding_line',
                args: [JSON.parse(this.value).move_id, id],
                context: context,
            }).then(function () {
                self.trigger_up('reload');
            });
        },
        _dummyEventListener: function (event) {
            event.stopPropagation();
            event.preventDefault();
        },
        _OnChangeDate: async function (event) {
            var new_date = this.$("input[id='payment_date']");
            var rate = this.$("input[id='currency_rate']");
            var currency_rate = 0;
            currency_rate = await Promise.all([this._rpc({
                model: 'account.move',
                method: 'get_currency_rate',
                args: [this.recordData.id, new_date.val()],
            })]);
            rate.val(currency_rate)
        },
    });
});
