
odoo.define('auth_signup.auth_signup', function (require) {
    'use strict';
    require('web.dom_ready');

    if ($('.field-country').length) {
        var state_options = $("select[id='state_id']:enabled option:not(:first)");
        $('.field-country').on('change', "select[id='country_id']", function () {
            console.log('cambio Pais')
            console.log($(this).val())
            var select = $("select[id='state_id']");
            state_options.detach();
            var displayed_state = state_options.filter("[data-country_id=" + ($(this).val() || 0) + "]");
            var nb = displayed_state.appendTo(select).show().length;
            select.parent().toggle(nb >= 1);
            if ($(this).val() != 173 ){
                $(".field-state").css("display", "none");
                $(".field-district-id").css("display", "none");
                $(".field-province").css("display", "none");

                $("select[id='state_id']").removeAttr("required");
                $("select[id='province_id']").removeAttr("required");
                $("select[id='district_id']").removeAttr("required");

            }else{
                $(".field-state").css("display", "block");
                    $("select[id='state_id']").attr("required", "true"); 
                $(".field-province").css("display", "block");
                    $("select[id='province_id']").attr("required", "true");
                $(".field-district-id").css("display", "block");
                    $("select[id='district_id']").attr("required", "true"); 
            }
        });
        $('.field-country').find("select[id='country_id']").change();
    }

    if ($('.field-state').length) {
        var state_options_province_id = $("select[id='province_id']:enabled option:not(:first)");
        $('.field-state').on('change', "select[id='state_id']", function () {
            console.log('cambio departamento')
            console.log($(this).val())
            var select2 = $("select[id='province_id']");
            state_options_province_id.detach();
            var displayed_state = state_options_province_id.filter("[data-state_id=" + ($(this).val() || 0) + "]");
            var nb = displayed_state.appendTo(select2).show().length;
            select2.parent().toggle(nb >= 1);
            console.log('Fin')
            
            
        });
        $('.field-state').find("select[id='state_id']").change();
    }

    if ($('.field-province').length) {
        var state_options_district_id = $("select[id='district_id']:enabled option:not(:first)");
        $('.field-province').on('change', "select[id='province_id']", function () {
            console.log('cambio provincia')
            var select3 = $("select[id='district_id']");
            state_options_district_id.detach();
            var displayed_state = state_options_district_id.filter("[data-province_id=" + ($(this).val() || 0) + "]");
            var nb = displayed_state.appendTo(select3).show().length;
            select3.parent().toggle(nb >= 1);
            $(".field-state").css("display", "block");
            $(".field-province").css("display", "block");
            $(".field-district-id").css("display", "block");
            
        });
        $('.field-province').find("select[id='province_id']").change();
    }

    $('.field-confirm-password1').on('change', "input[id='confirm-password']", function () {

        var confirm_password = $(this).val();
        var password = $("input[id='password']").val();
        if (confirm_password != password) {
            alert('la Contraseña no son iguales');
            $("button[id='regit']").attr("disabled", true);
        } else {
            var button = $("button[id='regit']").attr("disabled", false);
        }
    });
    $('.field-confirm-password1').find("input[id='confirm-password']").change();

});