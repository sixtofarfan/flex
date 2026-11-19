
odoo.define('auth_signup.auth_signup', function (require) {
'use strict';
    var publicWidget = require('web.public.widget');
    publicWidget.registry.portalDetails = publicWidget.Widget.extend({
        selector: '.oe_addres_form',
        events: {
            'change select[name="country_id"]' :  '_onCountryChange',
            'change select[name="state_id"]'    :  '_onEjeChange',
            'change select[name="province_id"]'    :  '_onPacChange',

        },

        /**
         * @override
         */
        start: function () {
            var def = this._super.apply(this, arguments);
            this.$eje = this.$('select[name="state_id"]');
            this.$ejeOptions = this.$eje.filter(':enabled').find('option:not(:first)');
            this._adaptAddressState();

            this.$pac = this.$('select[name="province_id"]');
            this.$pacOptions = this.$pac.filter(':enabled').find('option:not(:first)');
            this._adaptAddressEje();
            
            this.$clap = this.$('select[name="district_id"]');
            this.$clapOptions = this.$clap.filter(':enabled').find('option:not(:first)');
            this._adaptAddressClap();
            return def;
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @private
         */
        _adaptAddressState: function () {
            var $parish = this.$('select[name="country_id"]');
            var parishID = ($parish.val() || 0);
            this.$ejeOptions.detach();
            var $displayedEje = this.$ejeOptions.filter('[data-country_id=' + parishID + ']');
            var nb = $displayedEje.appendTo(this.$eje).show().length;
            console.log("Cambio")
            /* this.$eje.parent().toggle(nb >= 1); */
        },
        _adaptAddressEje: function () {
            var ejeID = (this.$eje.val() || 0);
            this.$pacOptions.detach();
            var $displayedPac = this.$pacOptions.filter('[data-state_id=' + ejeID + ']');
            var nb = $displayedPac.appendTo(this.$pac).show().length;
        },
        _adaptAddressClap: function () {

            var pacID = (this.$pac.val() || 0);
            this.$clapOptions.detach();
            var $displayedClap = this.$clapOptions.filter('[data-province_id=' + pacID + ']');
            var nb = $displayedClap.appendTo(this.$clap).show().length;
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         */
        _onCountryChange: function () {
            this._adaptAddressState();
        },
        _onEjeChange: function () {
            this._adaptAddressEje();
        },
        _onPacChange: function () {
            this._adaptAddressClap();
        },

    });

});