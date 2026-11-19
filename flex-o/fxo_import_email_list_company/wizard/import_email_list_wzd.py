# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ImportEmailListWzd(models.TransientModel):
    _name = "import.email.list.wzd"

    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company.id,
                                 required=True)
    vat = fields.Char(related='company_id.vat', string='Vat')
    to_contract = fields.Boolean(string='Desde Contratos', default=True)
    to_budget = fields.Boolean(string='Desde Cotizaciones', default=True)
    to_invoice = fields.Boolean(string='Desde Facturas', default=True)
    to_category = fields.Boolean(string='Por Categorías')
    to_state = fields.Boolean(string='Por Estados')

    def import_list(self):
        if not self.to_category and not self.to_state:
            mailing_list = self.env['mailing.list'].search([('vat', '=', self.vat),
                                                            ('category_id', '=', False),
                                                            ('state_partner', '=', False)], limit=1)
            mailing_contact_subscription = self.env['mailing.contact.subscription']
            mailing_contact = self.env['mailing.contact']
            if len(mailing_list) == 1:
                contacts_list_email = mailing_list.contact_ids.mapped('email')
                partners_contract = list()
                partners_budget = list()
                partners_invoice = list()
                if self.to_contract:
                    partners_contract = self._search_partners_to_contract(self.company_id.id)
                if self.to_budget:
                    partners_budget = self._search_partners_to_budget(self.company_id.id)
                if self.to_invoice:
                    partners_invoice = self._search_partners_to_invoice(self.company_id.id)
                contacts = partners_contract + partners_budget + partners_invoice
                contacts = list(set(contacts))
                contacts = self.env['res.partner'].browse(contacts)
                for c in contacts:
                    email_list = self._split_email_to_partner(c)
                    for email in email_list:
                        if email not in contacts_list_email:
                            dicc_contact = dict()
                            dicc_contact['name'] = c.name
                            dicc_contact['email'] = email
                            dicc_contact['partner_id'] = c.id
                            dicc_contact['country_id'] = c.country_id.id
                            dicc_contact['company_name'] = self.company_id.name
                            contact_obj_id = mailing_contact.create(dicc_contact)
                            mailing_contact_subscription.create({
                                'list_id': mailing_list.id,
                                'contact_id': contact_obj_id.id
                            })
            else:
                mailing_list_obj = self.env['mailing.list']
                dicc_list = dict()
                dicc_list['name'] = _('Clientes de Compañía: %s' % self.company_id.name)
                dicc_list['vat'] = self.vat
                contacts = list()
                mailing_list_obj_id = mailing_list_obj.create(dicc_list)
                partners_contract = list()
                partners_budget = list()
                partners_invoice = list()
                if self.to_contract:
                    partners_contract = self._search_partners_to_contract(self.company_id.id)
                if self.to_budget:
                    partners_budget = self._search_partners_to_budget(self.company_id.id)
                if self.to_invoice:
                    partners_invoice = self._search_partners_to_invoice(self.company_id.id)
                contacts = partners_contract + partners_budget + partners_invoice
                contacts = list(set(contacts))
                contacts = self.env['res.partner'].browse(contacts)
                for c in contacts:
                    email_list = self._split_email_to_partner(c)
                    for email in email_list:
                        dicc_contact = dict()
                        dicc_contact['name'] = c.name
                        dicc_contact['email'] = email
                        dicc_contact['partner_id'] = c.id
                        dicc_contact['country_id'] = c.country_id.id
                        dicc_contact['company_name'] = self.company_id.name
                        contact_obj_id = mailing_contact.create(dicc_contact)
                        mailing_contact_subscription.create({
                            'list_id': mailing_list_obj_id.id,
                            'contact_id': contact_obj_id.id
                        })
        if self.to_category and not self.to_state:
            mailing_contact_subscription = self.env['mailing.contact.subscription']
            mailing_contact = self.env['mailing.contact']
            partners_contract = list()
            partners_budget = list()
            partners_invoice = list()
            if self.to_contract:
                partners_contract = self._search_partners_to_contract(self.company_id.id)
            if self.to_budget:
                partners_budget = self._search_partners_to_budget(self.company_id.id)
            if self.to_invoice:
                partners_invoice = self._search_partners_to_invoice(self.company_id.id)
            contacts = partners_contract + partners_budget + partners_invoice
            contacts = list(set(contacts))
            contacts = self.env['res.partner'].browse(contacts)
            category_partner = contacts.mapped('fxo_category_id')
            for category in category_partner:
                contacts_category = contacts.filtered(lambda l: l.fxo_category_id.id == category.id)
                mailing_list = self.env['mailing.list'].search([('vat', '=', self.vat),
                                                                ('category_id', '=', category.id),
                                                                ('state_partner', '=', False)], limit=1)
                if len(mailing_list) == 1:
                    contacts_list_email = mailing_list.contact_ids.mapped('email')
                    for c in contacts_category:
                        email_list = self._split_email_to_partner(c)
                        for email in email_list:
                            if email not in contacts_list_email:
                                dicc_contact = dict()
                                dicc_contact['name'] = c.name
                                dicc_contact['email'] = email
                                dicc_contact['partner_id'] = c.id
                                dicc_contact['country_id'] = c.country_id.id
                                dicc_contact['company_name'] = self.company_id.name
                                contact_obj_id = mailing_contact.create(dicc_contact)
                                mailing_contact_subscription.create({
                                    'list_id': mailing_list.id,
                                    'contact_id': contact_obj_id.id
                                })
                else:
                    mailing_list_obj = self.env['mailing.list']
                    dicc_list = dict()
                    dicc_list['name'] = _(
                        'Clientes de Compañía: %s - Categoría: %s' % (self.company_id.name, category.name))
                    dicc_list['vat'] = self.vat
                    dicc_list['category_id'] = category.id
                    mailing_list_obj_categ_id = mailing_list_obj.create(dicc_list)
                    for c in contacts_category:
                        email_list = self._split_email_to_partner(c)
                        for email in email_list:
                            dicc_contact = dict()
                            dicc_contact['name'] = c.name
                            dicc_contact['email'] = email
                            dicc_contact['partner_id'] = c.id
                            dicc_contact['country_id'] = c.country_id.id
                            dicc_contact['company_name'] = self.company_id.name
                            contact_obj_categ_id = mailing_contact.create(dicc_contact)
                            mailing_contact_subscription.create({
                                'list_id': mailing_list_obj_categ_id.id,
                                'contact_id': contact_obj_categ_id.id
                            })
        if not self.to_category and self.to_state:
            mailing_contact_subscription = self.env['mailing.contact.subscription']
            mailing_contact = self.env['mailing.contact']
            partners_contract = list()
            partners_budget = list()
            partners_invoice = list()
            if self.to_contract:
                partners_contract = self._search_partners_to_contract(self.company_id.id)
            if self.to_budget:
                partners_budget = self._search_partners_to_budget(self.company_id.id)
            if self.to_invoice:
                partners_invoice = self._search_partners_to_invoice(self.company_id.id)
            contacts = partners_contract + partners_budget + partners_invoice
            contacts = list(set(contacts))
            contacts = self.env['res.partner'].browse(contacts)
            status_partner = contacts.mapped('status_id')
            for status in status_partner:
                contacts_status = contacts.filtered(lambda l: l.status_id.id == status.id)
                mailing_list = self.env['mailing.list'].search([('vat', '=', self.vat),
                                                                ('category_id', '=', False),
                                                                ('state_partner', '=', status.id)], limit=1)
                if len(mailing_list) == 1:
                    contacts_list_email = mailing_list.contact_ids.mapped('email')
                    for c in contacts_status:
                        email_list = self._split_email_to_partner(c)
                        for email in email_list:
                            if email not in contacts_list_email:
                                dicc_contact = dict()
                                dicc_contact['name'] = c.name
                                dicc_contact['email'] = email
                                dicc_contact['partner_id'] = c.id
                                dicc_contact['country_id'] = c.country_id.id
                                dicc_contact['company_name'] = self.company_id.name
                                contact_obj_id = mailing_contact.create(dicc_contact)
                                mailing_contact_subscription.create({
                                    'list_id': mailing_list.id,
                                    'contact_id': contact_obj_id.id
                                })
                else:
                    mailing_list_obj = self.env['mailing.list']
                    dicc_list = dict()
                    dicc_list['name'] = _(
                        'Clientes de Compañía: %s - Estado: %s' % (self.company_id.name, status.name))
                    dicc_list['vat'] = self.vat
                    dicc_list['state_partner'] = status.id
                    mailing_list_obj_status_id = mailing_list_obj.create(dicc_list)
                    for c in contacts_status:
                        email_list = self._split_email_to_partner(c)
                        for email in email_list:
                            dicc_contact = dict()
                            dicc_contact['name'] = c.name
                            dicc_contact['email'] = email
                            dicc_contact['partner_id'] = c.id
                            dicc_contact['country_id'] = c.country_id.id
                            dicc_contact['company_name'] = self.company_id.name
                            contact_obj_status_id = mailing_contact.create(dicc_contact)
                            mailing_contact_subscription.create({
                                'list_id': mailing_list_obj_status_id.id,
                                'contact_id': contact_obj_status_id.id
                            })
        else:
            mailing_contact_subscription = self.env['mailing.contact.subscription']
            mailing_contact = self.env['mailing.contact']
            partners_contract = list()
            partners_budget = list()
            partners_invoice = list()
            if self.to_contract:
                partners_contract = self._search_partners_to_contract(self.company_id.id)
            if self.to_budget:
                partners_budget = self._search_partners_to_budget(self.company_id.id)
            if self.to_invoice:
                partners_invoice = self._search_partners_to_invoice(self.company_id.id)
            contacts = partners_contract + partners_budget + partners_invoice
            contacts = list(set(contacts))
            contacts = self.env['res.partner'].browse(contacts)
            category_partner = contacts.mapped('fxo_category_id')
            for category in category_partner:
                contacts_category = contacts.filtered(lambda l: l.fxo_category_id.id == category.id)
                contacts_status = contacts_category.mapped('status_id')
                for status in contacts_status:
                    contacts_category_status = contacts_category.filtered(lambda l: l.status_id.id == status.id)
                    mailing_list = self.env['mailing.list'].search([('vat', '=', self.vat),
                                                                    ('category_id', '=', category.id),
                                                                    ('state_partner', '=', status.id)], limit=1)
                    if len(mailing_list) == 1:
                        contacts_list_email = mailing_list.contact_ids.mapped('email')
                        for c in contacts_category_status:
                            email_list = self._split_email_to_partner(c)
                            for email in email_list:
                                if email not in contacts_list_email:
                                    dicc_contact = dict()
                                    dicc_contact['name'] = c.name
                                    dicc_contact['email'] = email
                                    dicc_contact['partner_id'] = c.id
                                    dicc_contact['country_id'] = c.country_id.id
                                    dicc_contact['company_name'] = self.company_id.name
                                    contact_obj_id = mailing_contact.create(dicc_contact)
                                    mailing_contact_subscription.create({
                                        'list_id': mailing_list.id,
                                        'contact_id': contact_obj_id.id
                                    })
                    else:
                        mailing_list_obj = self.env['mailing.list']
                        dicc_list = dict()
                        dicc_list['name'] = _(
                            'Clientes de Compañía: %s - Categoría: %s - Estado: %s' % (self.company_id.name, category.name, status.name))
                        dicc_list['vat'] = self.vat
                        dicc_list['category_id'] = category.id
                        dicc_list['state_partner'] = status.id
                        mailing_list_obj_categ_id = mailing_list_obj.create(dicc_list)
                        for c in contacts_category_status:
                            email_list = self._split_email_to_partner(c)
                            for email in email_list:
                                dicc_contact = dict()
                                dicc_contact['name'] = c.name
                                dicc_contact['email'] = email
                                dicc_contact['partner_id'] = c.id
                                dicc_contact['country_id'] = c.country_id.id
                                dicc_contact['company_name'] = self.company_id.name
                                contact_obj_categ_id = mailing_contact.create(dicc_contact)
                                mailing_contact_subscription.create({
                                    'list_id': mailing_list_obj_categ_id.id,
                                    'contact_id': contact_obj_categ_id.id
                                })
        return self.env['popup.it'].get_message('Operación realizada con éxito!')

    def _search_partners_to_contract(self, company_id):
        sql_query = f'''
            select partner_id from sale_subscription where company_id = {company_id}
            group by partner_id
        '''
        self._cr.execute(sql_query)
        partners = [x[0] for x in self._cr.fetchall()]
        return partners

    def _search_partners_to_budget(self, company_id):
        sql_query = f'''
            select partner_id from sale_order where company_id = {company_id}
            group by partner_id
        '''
        self._cr.execute(sql_query)
        partners = [x[0] for x in self._cr.fetchall()]
        return partners

    def _search_partners_to_invoice(self, company_id):
        sql_query = f'''
            select partner_id from account_move where company_id = {company_id}
            and type='out_invoice'
            group by partner_id
        '''
        self._cr.execute(sql_query)
        partners = [x[0] for x in self._cr.fetchall()]
        return partners

    @api.constrains('to_contract', 'to_budget', 'to_invoice')
    def _constraint_filter_search_partner(self):
        if not self.to_invoice and not self.to_budget and not self.to_contract:
            raise ValidationError(_('Debe seleccionar al menos un filtro de donde se buscarán los clientes'))

    def _split_email_to_partner(self, partner):
        result = list()
        coma = ','
        punto_coma = ';'
        if partner.email:
            email = partner.email
            if email.find(coma) != -1 and email.find(punto_coma) != -1:
                email_list = email.split(',')
                for e in email_list:
                    if e.find(punto_coma) != -1:
                        e_second = e.split(';')
                        for s in e_second:
                            result.append(s.strip())
                    else:
                        result.append(e.strip())
            elif email.find(coma) != -1 and email.find(punto_coma) == -1:
                email_list = email.split(',')
                for e in email_list:
                    result.append(e.strip())
            elif email.find(coma) == -1 and email.find(punto_coma) != -1:
                email_list = email.split(';')
                for e in email_list:
                    result.append(e.strip())
            else:
                result.append(email)
        if partner.email_second:
            email_second = partner.email_second
            if email_second.find(coma) != -1 and email_second.find(punto_coma) != -1:
                email_list = email_second.split(',')
                for e in email_list:
                    if e.find(punto_coma) != -1:
                        e_second = e.split(';')
                        for s in e_second:
                            result.append(s.strip())
                    else:
                        result.append(e.strip())
            elif email_second.find(coma) != -1 and email_second.find(punto_coma) == -1:
                email_list = email_second.split(',')
                for e in email_list:
                    result.append(e.strip())
            elif email_second.find(coma) == -1 and email_second.find(punto_coma) != -1:
                email_list = email_second.split(';')
                for e in email_list:
                    result.append(e.strip())
            else:
                result.append(email_second)
        return result
