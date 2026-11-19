# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, http, _
from odoo import http
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.osv.expression import OR


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        ids = request.env.user.partner_id.id
        values['stock_picking_router_count'] = request.env['sale.order'].sudo().search_count([
            ('router_partner', '=', ids),
            ('state_router','=','confirm')
            ])
        if values.get('sales_user', False):
            values['title'] = _("Salesperson")
        return values

    @http.route(['/my/orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        """ try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my') """
        order_sudo = request.env['sale.order'].sudo().search([('id', '=',order_id )])
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type, report_ref='sale.action_report_saleorder', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if order_sudo and request.session.get('view_quote_%s' % order_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % order_sudo.id] = now
            body = _('Quotation viewed by customer %s') % order_sudo.partner_id.name
            _message_post_helper('sale.order', order_sudo.id, body, token=order_sudo.access_token, message_type='notification', subtype="mail.mt_note")

        values = {
            'sale_order': order_sudo,
            'message': message,
            'token': access_token,
            'return_url': '/shop/payment/validate',
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'report_type': 'html',
            'action': order_sudo._get_portal_return_action(),
        }
        if order_sudo.company_id:
            values['res_company'] = order_sudo.company_id

        if order_sudo.has_to_be_paid():
            domain = expression.AND([
                ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', order_sudo.company_id.id)],
                ['|', ('country_ids', '=', False), ('country_ids', 'in', [order_sudo.partner_id.country_id.id])]
            ])
            acquirers = request.env['payment.acquirer'].sudo().search(domain)

            values['acquirers'] = acquirers.filtered(lambda acq: (acq.payment_flow == 'form' and acq.view_template_id) or
                                                     (acq.payment_flow == 's2s' and acq.registration_view_template_id))
            values['pms'] = request.env['payment.token'].search([('partner_id', '=', order_sudo.partner_id.id)])
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(order_sudo.amount_total, order_sudo.currency_id, order_sudo.partner_id.country_id.id)

        if order_sudo.state in ('draft', 'sent', 'cancel'):
            history = request.session.get('my_quotations_history', [])
        else:
            history = request.session.get('my_orders_history', [])
        values.update(get_records_pager(history, order_sudo))

        return request.render('sale.sale_order_portal_template', values)


class Prueba(http.Controller):

    def _prepare_portal_layout_values(self):
        # get customer sales rep
        sales_user = False
        partner = request.env.user.partner_id
        if partner.user_id and not partner.user_id._is_public():
            sales_user = partner.user_id

        return {
            'sales_user': sales_user,
            'page_name': 'home',
            'archive_groups': [],
        }

    @http.route('/my/router', auth='public', website=True)
    def list(self, **kw):
        values = self._prepare_portal_layout_values()
        ids = request.env.user.partner_id.id

        values.update({
           'objects': http.request.env['stock.picking.router.line'].search([('drivers_id','in', ids)]),
        })
        response = request.render("fxo_order_router_picking.portal_router", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/my/router/<int:router_id>', type='http', auth="user", website=True)
    def get_router_list(self, router_id=None, access_token=None, **kw):
        values = self._prepare_portal_layout_values()
        ids = request.env.user.partner_id.id

        orders_id = http.request.env['sale.order'].sudo().search([
            ('router_partner', '=', ids), 
            ('router_day', '=', router_id),
            ('state_router','=','confirm')
        ])
        values.update({
            'orders_id': orders_id,
            'router':router_id
        })
        response = request.render("fxo_order_router_picking.portal_router_detally", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/my/router/<int:router_id>/<int:order_id>/<string:state>',type='http',auth="public", website=True)
    def get_router_id_states(self, router_id=None,order_id=None,state =None,access_token=None, **kw):
        order = http.request.env['sale.order'].sudo().search([('id', '=', order_id)])
        if order.state_router == 'confirm':
            if state in ('not deliver','delivered'):
                order.sudo().state_router = state
        return request.redirect('/my/router/%s/' % router_id)