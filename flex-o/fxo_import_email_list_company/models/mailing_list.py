# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from odoo.tools import email_re


class MailingList(models.Model):
    _inherit = 'mailing.list'

    vat = fields.Char(string='Vat')
    category_id = fields.Many2one('res.partner.category', string='Categoría')
    state_partner = fields.Many2one('catalog.100', string='Estado')

    def unlink(self):
        for c in self.contact_ids:
            c.unlink()
        return super(MailingList, self).unlink()


class MassMailingList(models.Model):
    _inherit = "mailing.contact"

    partner_id = fields.Many2one(comodel_name="res.partner", string="Cliente")
    mobile_partner = fields.Char(related='partner_id.mobile', string='Móvil', store=True)
    phone_partner = fields.Char(related='partner_id.phone', string='Teléfono fijo', store=True)
    category_id = fields.Many2one(related='partner_id.fxo_category_id', string='Categoría', store=True)
    state_partner = fields.Many2one(related='partner_id.status_id', string='Estado', store=True)


class MailingMailing(models.Model):
    _inherit = 'mailing.mailing'

    send_email_second = fields.Boolean(string='Añadir Email CC del Contacto')
    is_contact = fields.Boolean(string='Seleccionado Contacto', compute='_compute_select_contact', store=True)

    @api.depends('mailing_model_id')
    def _compute_select_contact(self):
        for rec in self:
            if rec.mailing_model_id.model == "res.partner":
                rec.is_contact = True
            else:
                rec.is_contact = False


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def get_mail_values(self, res_ids):
        self.ensure_one()
        res = super(MailComposeMessage, self).get_mail_values(res_ids)
        if self.mass_mailing_id.send_email_second:
            recipient_partners_ids = []
            for res_id in res_ids:
                mail_values = res[res_id]
                if mail_values.get('recipient_ids'):
                    recipient_partners_ids.append(mail_values.get('recipient_ids')[0][1])
            read_partners = self.env['res.partner'].browse(recipient_partners_ids)
            for p in read_partners:
                partners_email = dict()
                partners_email_cc = dict()
                if p.email:
                    partners_email[p.id] = p.email.replace(';', ',')
                if p.email_second:
                    partners_email_cc[p.id] = p.email_second.replace(';', ',')

            for res_id in res_ids:
                mail_values = res[res_id]
                partner_id = (mail_values.get('recipient_ids') or [(False, '')])[0][1]
                mail_to = partners_email.get(partner_id)
                mail_to_cc = partners_email_cc.get(partner_id)
                mail_complete = mail_to + ',' + mail_to_cc
                trace_vals = {
                    'model': self.model,
                    'res_id': res_id,
                    'mass_mailing_id': self.mass_mailing_id.id,
                    'email': mail_complete,
                }
                mail_values.update({
                    'mailing_trace_ids': [(0, 0, trace_vals)],
                    'email_to': mail_to,
                    'email_cc': mail_to_cc,
                })
        return res
