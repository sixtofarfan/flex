odoo.define('auth_signup.portal', function (require) {
'use strict';
    require('web.dom_ready');
    
    if ($('.o_portal_details').length) {
        var state_options = $("select[name='state_ids']:enabled option:not(:first)");

        $('.o_portal_details').on('change', "select[name='country_id']", function () {
            console.log('cambio Pais')
            console.log($(this).val())
            var select = $("select[name='state_ids']");
            state_options.detach();
            var displayed_state = state_options.filter("[data-country_id=" + ($(this).val() || 0) + "]");
            var nb = displayed_state.appendTo(select).show().length;
            select.parent().toggle(true);
            if ($(this).val() != 173) {
                console.log('No peru')
                $(".field-state-id").css("display", "none");
                    $("select[name='state_id']").removeAttr("required");
                $(".field-province").css("display", "none");
                    $("select[name='province_id']").removeAttr("required");
                $(".field-district-id").css("display", "none");
                    $("select[name='district_id']").removeAttr("required");
                    
            } else {
                console.log('Peru')
                $(".field-state-id").css("display", "block");
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
            select.parent().toggle(true);
            $(".field-state").css("display", "block");
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
            select.parent().toggle(true);
        });
        $('.o_portal_details').find("select[name='district_id']").change();
    }
    $("#persona").click(function () {
        $("input[id='aname']").attr("required", "true");
        $("input[id='las_name']").attr("required", "true");
        $("input[id='login']").attr("required", "true");
        /* remover */

        $("select[id='category_id']").removeAttr("required");
        $("input[id='razon']").removeAttr("required");
        /* $("input[id='ruc']").removeAttr("required"); */
        $("input[id='street']").removeAttr("required");
        $("input[id='email_institucional']").removeAttr("required");
        $("input[id='cargo']").removeAttr("required");
        $("input[id='nombre_responsable']").removeAttr("required");
        $("input[id='apellido_responsable']").removeAttr("required"); 
         
    });

    $("#empresa").click(function () {
        $("select[id='category_id']").attr("required", "true"); 
        $("input[id='razon']").attr("required", "true");
        /* $("input[id='ruc']").attr("required", "true");  */
        $("input[id='street']").attr("required", "true");
        $("input[id='email_institucional']").attr("required", "true");
        $("input[id='cargo']").attr("required", "true"); 
        $("input[id='nombre_responsable']").attr("required", "true"); 
        $("input[id='apellido_responsable']").attr("required", "true"); 

        /* remover */
        $("input[id='aname']").removeAttr("required");
        $("input[id='las_name']").removeAttr("required");
        $("input[id='login']").removeAttr("required");

    }); 
});

