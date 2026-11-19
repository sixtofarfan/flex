odoo.define('survey.translator', function (require) {
'use strict';

var survey = require('survey.survey');
/*
 * This file is intended to add interactivity to survey forms
 */

var the_form = $('.js_surveyform');
if(!the_form.length) {
    return $.Deferred().reject("DOM doesn't contain '.js_surveyform' - Translator");
}

var cprefill_controller = the_form.attr("data-prefill").replace('prefill', 'cprefill');
var submit_controller = the_form.attr("data-submit");
var print_mode = false;

if (_.isUndefined(submit_controller)) {
    print_mode = true;
    $('#js_add_item').parents('tr').remove();
}

var index = 1;

function cprefill(){
    var prefill_def = $.ajax(cprefill_controller, {dataType: "json"})
        .done(function(json_data){
            _.each(json_data, function(value, prefix){
                var input = the_form.find(".form-control[name='" + prefix + "'], img[name='"+prefix+"']");
                if (input.length){
                    if (input[0].type == 'file'){
                        input.replaceWith("<input type='text' readonly='readonly' class='form-control' value='"+value+"' disabled='disabled'/>");
                    }
                    else if (input.length > 0 && input[0].nodeName == "IMG"){
                        input.attr('src', "data:image/png;base64," + value);
                    }
                    else {
                        input.val(value);
                    }
                }
                else if(_.isObject(value)){
                    _.each(value, function(v, k){
                        the_form.find(".form-control[name='" + k + "'], select[name='" + k + "']").val(v);
                    });
                }
            });
        })
        .fail(function(){
            console.warn("[survey] CPrefill failed to load data");
        });
    return prefill_def;
}

if (! _.isUndefined(cprefill_controller)) {
    cprefill();
}
    // if ($('.field-country').length) {
    //     var state_options = $("select[id='state_id']:enabled option:not(:first)");
    //     $('.field-country').on('change', "select[id='country_id']", function () {
    //         console.log('cambio Pais')
    //         var select = $("select[id='state_id']");
    //         state_options.detach();
    //         var displayed_state = state_options.filter("[data-country_id=" + ($(this).val() || 0) + "]");
    //         var nb = displayed_state.appendTo(select).show().size();
    //         select.parent().toggle(nb >= 1);
    //         $(".field-state").css("display", "block");
    //     });
    //     $('.field-country').find("select[id='country_id']").change();
    // }

    // if ($('.field-state').length) {
    //     var state_options_province_id = $("select[id='province_id']:enabled option:not(:first)");
    //     $('.field-state').on('change', "select[id='state_id']", function () {
    //         console.log('cambio departamento')
    //         var select = $("select[id='province_id']");
    //         state_options_province_id.detach();
    //         var displayed_state = state_options_province_id.filter("[data-state_id=" + ($(this).val() || 0) + "]");
    //         var nb = displayed_state.appendTo(select).show().size();
    //         select.parent().toggle(nb >= 1);
    //         $(".field-province").css("display", "block");
    //     });
    //     $('.field-state').find("select[id='state_id']").change();
    // }

    // if ($('.field-province').length) {
    //     var state_options_district_id = $("select[id='district_id']:enabled option:not(:first)");
    //     $('.field-province').on('change', "select[id='province_id']", function () {
    //         console.log('cambio provincia')
    //         var select = $("select[id='district_id']");
    //         state_options_district_id.detach();
    //         var displayed_state = state_options_district_id.filter("[data-province_id=" + ($(this).val() || 0) + "]");
    //         var nb = displayed_state.appendTo(select).show().size();
    //         select.parent().toggle(nb >= 1);
    //         $(".field-state").css("display", "block");
    //         $(".field-province").css("display", "block");
    //         $(".field-district-id").css("display", "block");
    //     });
    //     $('.field-province').find("select[id='province_id']").change();
    // }

});
