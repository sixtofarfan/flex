# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import math
import re

from werkzeug import urls

from odoo import fields as odoo_fields, tools, _
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError
from odoo.http import content_disposition, Controller, request, route
from odoo.tools import consteq
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalL(CustomerPortal):

    MANDATORY_BILLING_FIELDS = [
     "name", "email",  "apaterno", "last_name",  ]
    OPTIONAL_BILLING_FIELDS = [
        "zipcode", "street", "city", "state_id", "vat", "sex", "birthday",
        "province_id", "district_id", "company_name", "phone", 
    ]

    @route()
    def account(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        values.update({
         'error': {},
         'error_message': [],
        })

        if post:
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                values.update({'zip': values.pop('zipcode', '')})
                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        provinces = request.env['res.country.province'].sudo().search([])
        districts = request.env['res.country.district'].sudo().search([])

        values.update({
         'partner': partner,
         'countries': countries,
         'states': states,
         'provinces': provinces,
         'districts': districts,
         'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
         'redirect': redirect,
         'page_name': 'my_details',
        })

        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
