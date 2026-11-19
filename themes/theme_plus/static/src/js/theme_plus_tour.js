odoo.define('theme_plus.tour', function(require) {
    'use strict';

    var tour = require('web_tour.tour');
    var base = require('web_editor.base');

    tour.register('theme_plus_tour', {
        test: true,
        url: '/',
        wait_for: base.ready(),
    }, [{
        content: "Complete name",
        trigger: "input[name=name]",
        run: "text John Smith",
    }, {
        content: "Complete Email",
        trigger: "input[name=email]",
        run: "text john@smith.com",
    }, {
        content: "Complete Subject",
        trigger: "input[name=subject]",
        run: "text Useless message",
    },{
        content: "Complete Phone",
        trigger: "input[name=phone]",
        run: "text 99256",
    },{
        content: "Complete Meeting Time",
        trigger: "input[name=mtime]",
        run: "text 12:30 PM",
    },{
        content: "Complete Meeting Date",
        trigger: "input[name=meeting_datetime]",
        run: "text 2019/09/8",
    }, {
        content: "Complete Question",
        trigger: "textarea[name=question]",
        run: "text ### TOUR DATA ###",
    }, {
        content: "Send the form",
        trigger: ".o_website_form_send"
    }, {
        content: "Check we were redirected to the success page",
        trigger: "#wrap:has(h1:contains('THANK YOU FOR CONTACTING US.')):has(div.success)"
    }]);

    return {};
});
