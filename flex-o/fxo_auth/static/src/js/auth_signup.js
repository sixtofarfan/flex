
odoo.define('auth_signup.auth_signup', function (require) {
    'use strict';
    require('web.dom_ready');

    if ($('.field-aname').length) {
        var state_options = $("input[id='aname']");
        $('.field-aname').on('change', "input[id='aname']", function () {
            var select = $("input[id='las_name'");
            var name = $("input[id='name'");
            var temp = $(this).val() + " " + select.val()  
            name.val(temp)

        });
        $('.field-aname').find("input[id='aname']").change();
    }

    if ($('.field-las_name').length) {
        var state_options = $("input[id='las_name']");
        $('.field-las_name').on('change', "input[id='las_name']", function () {
            var select = $("input[id='aname'");
            var name = $("input[id='name'");
            var temp = select.val() + " " + $(this).val() 
            name.val(temp)

        });
        $('.field-las_name').find("input[id='las_name']").change();
    }

    if ($('.field-razon').length) {
        var state_options = $("input[id='razon']");
        $('.field-razon').on('change', "input[id='razon']", function () {
            var temp = $(this).val()
            var name = $("input[id='name'");
            name.val(temp)

        });
        $('.field-razon').find("input[id='razon']").change();
    }

    if ($('.field-email_institucional').length) {
        var state_options = $("input[id='email_institucional']");
        $('.field-email_institucional').on('change', "input[id='email_institucional']", function () {
            var temp = $(this).val()
            var name = $("input[id='login'");
            name.val(temp)

        });
        $('.field-email_institucional').find("input[id='email_institucional']").change();
    }

    /* $("#persona").click(function () {
        alert("persona");
         $("select[id='state_id']").attr("required", "true");  
    });

    $("#empresa").click(function () {
        alert("empresa");
    }); */

});