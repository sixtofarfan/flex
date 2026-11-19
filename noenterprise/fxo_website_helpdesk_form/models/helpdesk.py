# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons.http_routing.models.ir_http import slug

from odoo import http
from odoo.http import request
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.exceptions import UserError

class helpdesk_problem(models.Model):
	_name = 'helpdesk.problem'

	name = fields.Char('Problema')

class helpdesk_afection_type(models.Model):
	_name = 'helpdesk.afection.type'

	name = fields.Char('Tipo de Afectación')

class helpdesk_team(models.Model):
	_inherit = 'helpdesk.team'

	is_team_collection = fields.Boolean(string='Es Gestor de Cobranza', default=False)

class sale_subscription_line(models.Model):
	_inherit = 'sale.subscription.line'

	partner_id = fields.Many2one('res.partner', related='analytic_account_id.partner_id')

class helpdesk_ticket(models.Model):
	_inherit = 'helpdesk.ticket'

	@api.onchange('partner_id')
	def _domain_service(self):
		if self.partner_id:
			Subscriptions = self.env['sale.subscription'].search([('partner_id', '=', self.partner_id.id)])
			return {'domain': {'service_id': [('id', 'in', Subscriptions.recurring_invoice_line_ids.ids)]}}

	problem = fields.Many2one('helpdesk.problem', 'Problema')
	afection_type = fields.Many2one('helpdesk.afection.type','Tipo de Afectación')
	partner_street_id = fields.Many2one('res.partner', string='Direccion')
	street = fields.Char(related='partner_street_id.street', string='Direccion')
	service_id = fields.Many2one('sale.subscription.line', string='Client Service')
	motive_id = fields.Many2one('helpdesk.motive', string='Motive')
	detail_id = fields.Many2one(related='motive_id.parent_id', store=True, string='Detail')
	cause_id = fields.Many2one(related='detail_id.parent_id', store=True, string='Cause')
	responsable_id = fields.Many2one('res.partner', string='Responsable')
	date_from = fields.Datetime(string='Incident Start')
	date_to = fields.Datetime(string='Incident End')
	description_solution = fields.Text('Description of the solution', translate=True)
	supplier_ticket = fields.Char(string='Supplier Ticket')
	fault_latitude = fields.Float(string='Fault Latitude', digits=(16, 10))
	fault_longitude = fields.Float(string='Fault Longitude', digits=(16, 10))

	#analytic_id = fields.Many2one('account.analytic.account','Cuenta Analitica')

	@api.onchange('partner_id', 'team_id')
	def _get_user(self):
		if self.team_id and self.partner_id and self.team_id.is_team_collection and self.partner_id.collection_id:
			self.user_id = self.partner_id.collection_id.id

	@api.onchange('service_id')
	def _get_direction(self):
		for record in self:
			if record.service_id.partner_street_destination:
				record.partner_street_id = record.service_id.partner_street_destination.id

	@api.constrains('stage_id')
	def _check_stage(self):
		for record in self:
			if record.stage_id.name == 'Cerrado' and not record.motive_id:
				raise UserError('El ticket necesita un motivo para poder pasar a estado Cerrado')

	@api.model
	def create(self, vals):
		if 'partner_id' in vals:
			Partner = self.env['res.partner'].browse(vals['partner_id'])
			if Partner.type != 'contact':
				vals['partner_street_id'] = Partner.id
				vals['partner_id'] = Partner.parent_id.id if Partner.parent_id else None
		res = super(helpdesk_ticket, self).create(vals)
		template_id = self.env.ref('helpdesk.new_ticket_request_email_template').id
		template = self.env['mail.template'].browse(template_id)
		alias = res.team_id.alias_id
		if alias.alias_name and alias.alias_domain:
			template.send_mail(
				res.id,
				force_send=True, 
				email_values={'subject': 'Re: %s' % res.name, 'email_to': '%s@%s' % (alias.alias_name, alias.alias_domain)}, 
				notif_layout='mail.mail_notification_light'),
		return res

class helpdesk_motive(models.Model):
	_name = 'helpdesk.motive'
	_description = 'Helpdesk Motive'

	name = fields.Char(string='Name', required=True)
	parent_id = fields.Many2one('helpdesk.detail', string='Detail', required=True)

class helpdesk_detail(models.Model):
	_name = 'helpdesk.detail'
	_description = 'Helpdesk Detail'

	name = fields.Char(string='Name', required=True)
	parent_id = fields.Many2one('helpdesk.cause', string='Cause', required=True)
	child_ids = fields.One2many('helpdesk.motive', 'parent_id', string='Motives')

class helpdesk_cause(models.Model):
	_name = 'helpdesk.cause'
	_description = 'Helpdesk Cause'

	name = fields.Char(string='Name', required=True)
	child_ids = fields.One2many('helpdesk.detail', 'parent_id', string='Details')

class WebsiteForm(WebsiteForm):

	@http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
	def website_form(self, model_name, **kwargs):
		t= super(WebsiteForm, self).website_form(model_name, **kwargs)
		if model_name == 'helpdesk.ticket':
			ticket = request.env['helpdesk.ticket'].browse(request.session['form_builder_id'])
			if request.params.get('description'):
				ticket.description = kwargs.get('description')
			
			if request.params.get('problem'):
				ticket.problem = kwargs.get('problem')
			
			if request.params.get('afection_type'):
				ticket.afection_type = kwargs.get('afection_type')
			#if request.params.get('analytic_id'):
			#	ticket.analytic_id = kwargs.get('analytic_id')
		return t
