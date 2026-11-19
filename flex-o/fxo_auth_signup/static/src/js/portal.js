odoo.define('auth_signup.portal', function (require) {
'use strict';
    require('web.dom_ready');
    
    if ($('.o_portal_details').length) {
        var state_options = $("select[name='state_id']:enabled option:not(:first)");
        $('.o_portal_details').on('change', "select[name='country_id']", function () {
            console.log('cambio Pais')
            console.log($(this).val())
            var select = $("select[name='state_id']");
            state_options.detach();
            var displayed_state = state_options.filter("[data-country_id=" + ($(this).val() || 0) + "]");
            var nb = displayed_state.appendTo(select).show().length;
            select.parent().toggle(nb >= 1);
            if ($(this).val() != 173) {
                $(".field-state").css("display", "none");
                    $("select[name='state_id']").removeAttr("required");
                $(".field-province").css("display", "none");
                    $("select[name='province_id']").removeAttr("required");
                $(".field-district-id").css("display", "none");
                    $("select[name='district_id']").removeAttr("required");
                    
            } else {
                $(".field-state").css("display", "block");
                    $("select[name='state_id']").attr("required", "true");
                $(".field-province").css("display", "block");
                    $("select[name='province_id']").attr("required", "true");
                $(".field-district-id").css("display", "block");
                    $("select[name='district_id']").attr("required", "true");
            }
        });
        $('.o_portal_details').find("select[name='country_id']").change();
    }

    if ($('.o_portal_details').length) {
        var state_options_province_id = $("select[name='province_id']:enabled option:not(:first)");
        $('.o_portal_details').on('change', "select[name='state_id']", function () {
            console.log('cambio departamento')
            var select = $("select[name='province_id']");
            state_options_province_id.detach();
            var displayed_state = state_options_province_id.filter("[data-state_id=" + ($(this).val() || 0) + "]");
            var nb = displayed_state.appendTo(select).show().length;
            select.parent().toggle(nb >= 1);
        });
        $('.o_portal_details').find("select[name='state_id']").change();
    }

    if ($('.o_portal_details').length) {
        var state_options_district_id = $("select[name='district_id']:enabled option:not(:first)");
        $('.o_portal_details').on('change', "select[name='province_id']", function () {
            console.log('cambio provincia')
            var select = $("select[name='district_id']");
            state_options_district_id.detach();
            var displayed_state = state_options_district_id.filter("[data-province_id=" + ($(this).val() || 0) + "]");
            var nb = displayed_state.appendTo(select).show().length;
            select.parent().toggle(nb >= 1);
        });
        $('.o_portal_details').find("select[name='district_id']").change();
    }
});

