odoo.define('fxo_account_dashboards.MoveLinkList', function (require) {
"use strict";

/**
 * List views of the accounting books: the voucher is shown as a link and a click
 * on a row opens the journal entry / invoice (field `move_id`) instead of the
 * technical row of the report.
 *   <tree js_class="fxo_move_link_list"> ... <field name="voucher" widget="fxo_move_link"/>
 */
var basicFields = require('web.basic_fields');
var fieldRegistry = require('web.field_registry');
var ListController = require('web.ListController');
var ListView = require('web.ListView');
var viewRegistry = require('web.view_registry');

var MoveLinkController = ListController.extend({
    _onOpenRecord: function (ev) {
        ev.stopPropagation();
        var record = this.model.get(ev.data.id, {raw: true});
        var moveId = record && record.data.move_id;
        if (moveId) {
            this.do_action({
                type: 'ir.actions.act_window', res_model: 'account.move', res_id: moveId,
                views: [[false, 'form']], target: 'current',
            });
        }
    },
});

var MoveLinkListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: MoveLinkController,
    }),
});

var FieldMoveLink = basicFields.FieldChar.extend({
    className: 'o_field_char fxo_move_link',
});

viewRegistry.add('fxo_move_link_list', MoveLinkListView);
fieldRegistry.add('fxo_move_link', FieldMoveLink);

return {MoveLinkListView: MoveLinkListView, FieldMoveLink: FieldMoveLink};

});
