odoo.define('fxo_website_helpdesk_form.form', function (require) {
'use strict';

var core = require('web.core');
var FormEditorRegistry = require('website_form.form_editor_registry');

var _t = core._t;

FormEditorRegistry.add('create_ticket', {
    defaultTemplateName: 'website_helpdesk_form.default_ticket_form',
    defaultTemplatePath: '/fxo_website_helpdesk_form/static/src/xml/website_helpdesk_form.xml',
    fields: [{
        name: 'team_id',
        type: 'many2one',
        relation: 'helpdesk.team',
        string: _t('Helpdesk Team'),
    },{
        name: 'problem',
        type: 'many2one',
        relation: 'helpdesk.problem',
        string: _t('Problema'),
    },{
        name: 'afection_type',
        type: 'many2one',
        relation: 'helpdesk.afection.type',
        string: _t('Tipo de Afectacion'),
    },{
        name: 'analytic_id',
        type: 'many2one',
        relation: 'account.analytic.account',
        string: _t('Cuenta Analitica'),
    },
    ],
    successPage: '/your-ticket-has-been-submitted',
});

});
