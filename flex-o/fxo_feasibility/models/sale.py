# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
# import datetime, calendar
from datetime import date, datetime


class SaleOrder(models.Model):
    _inherit = "sale.order"

    install_type = fields.Selection(related="type_id.install_type")
    finish_facibility = fields.Boolean("Finish Facilities", compute="get_finish_facibility")
    historial_udt_ids = fields.One2many(
        comodel_name="subscription.line.upgrade", inverse_name="sale_id", string="UDT"
    )

    def create_subscriptions(self):
        res = []
        # URO si es renovacion o adenda no crea subscripciones nuevas
        if self.type_id.type_select not in ['adenda', 'renovation']:
            res = super(SaleOrder, self).create_subscriptions()
            Subs = self.env["sale.subscription"].browse(res)
            for sub in Subs:
                OrderLines = self.order_line.filtered(lambda l: l.display_type)
                for line in OrderLines:
                    self.env["sale.subscription.line"].create(
                        {
                            "analytic_account_id": sub.id,
                            "name": line.name,
                            "sequence": line.sequence,
                            "display_type": line.display_type,
                        }
                    )
        return res

    def validar_factibilidades(self):
        for i in self:
            for j in self.order_line:
                if j.product_id.bool_is_factibility or j.product_id.bool_is_study_economic:
                    j.action_qty_street()

    def open_auto_linea(self):
        return {
            "name": "Crear Lineas con Contactos",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "auto.sale.line",
            "target": "new",
            "context": {"default_partner_id": self.partner_id.id},
        }

    def get_finish_facibility(self):
        for i in self:
            todook = False
            # SFR renovaciones no requiere factibilidad
            if self.type_id.type_select in ['renovation']:
                i.finish_facibility = todook
                continue

            for ele in i.order_line:
                if ele.product_id.bool_is_factibility:
                    if ele.addresses_id.factibility_id.state not in ("done", "open"):
                        todook = True
            i.finish_facibility = todook

    # @api.constrains('state')
    # def update_subscription_price(self):
    # 	for line in self.subscription_update_id.recurring_invoice_line_ids:
    # 		line.update_amaout()

    @api.onchange("partner_id")
    def order_line_partner_id(self):
        for line in self.order_line:
            line.set_order_partner_street_id()

    @api.onchange("subscription_update_id")
    def order_line_subscription_update_id(self):
        for line in self.order_line:
            line.set_subscription_update_id()

    @api.onchange("subscription_update_id", "type_id")
    def _onchange_subscription_update_id_type_select(self):
        for rec in self:
            if rec.type_id.has_subscription_update_id != 'required':
                rec.subscription_update_id = None
            if rec.type_id.type_select == 'renovation' and rec.subscription_update_id:
                # SFR Control de renovacion
                # if not rec.subscription_update_id.to_renew:
                #    raise UserError('El contrato seleccionado no se encuentra disponible para renovar.')
                rec.order_line = None
                rec.order_line = [(0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.product_id.product_tmpl_id.name,
                    'subscription_id': rec.subscription_update_id.id,
                    'subscription_update_id': rec.subscription_update_id.id,
                    'product_uom': line.uom_id.id,
                    'product_uom1': line.uom_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom_qty1': line.quantity,
                    'price_unit': line.price_unit,
                    'price_unit1': line.price_unit,
                    'tax_id': line.product_id.sudo().taxes_id.filtered(lambda l: l.company_id.id == line.company_id.id),
                    'price_unit1_invisible': line.price_unit,
                    'price_unit_invisible': line.price_unit,
                    'discount': line.discount,
                    'service_id_2': line.service_id,
                    'partner_street_destination': line.partner_street_destination.id,
                    'partner_contact_id': line.partner_street_destination.id,
                    'price_subtotal': line.price_subtotal,
                    'currency_id': line.currency_id.id,
                }) for line in self.subscription_update_id.recurring_invoice_line_ids.filtered(
                    lambda l: l.state == 'done')]
                rec.subscription_management = 'renew'
            else:
                rec.order_line = None

    check_complete_confirm = fields.Boolean("Check", compute="get_check_complete_confirm", default=True)

    @api.depends("approval_sale_id.request_status")
    def get_check_complete_confirm(self):
        if len(self.order_line) == 0:
            self.check_complete_confirm = True
            return
        error = False
        for item in self.order_line:
            if item.bool_is_factibility:
                if not item.addresses_id.id:
                    error = True
                if not item.addresses_id.factibility_id.id or item.addresses_id.factibility_id.state not in (
                        "open",
                        "done",
                ):
                    error = True

        for permission in self.approval_sale_id:
            if permission.request_status != "approved":
                error = True
        self.check_complete_confirm = error

    check_temporary_factibility = fields.Boolean(
        string="Check", compute="get_check_temporary_factibility", default=False
    )

    @api.depends("order_line.factibility_id")
    def get_check_temporary_factibility(self):
        if len(self.order_line) == 0:
            self.check_temporary_factibility = True
            return
        tmp = False
        for line in self.order_line:
            if line.compute_have_factibility:
                if (
                        line.addresses_id.factibility_id.factibility_type == "temporary"
                        and line.addresses_id.factibility_id.state == "open"
                ):
                    tmp = True
        self.check_temporary_factibility = tmp

    # Confirma pedido
    def action_confirm(self):
        for line in self.order_line:
            if self.type_id.type_select in ['renovation', 'upgrade', 'downgrade', 'upgrade_temp']:
                if not line.service_id_2:
                    line.service_id_2 = self.env["ir.sequence"].next_by_code("service_id_code") or ""
            else:
                line.service_id_2 = self.env["ir.sequence"].next_by_code("service_id_code") or ""
        t = super(SaleOrder, self).action_confirm()
        error = False
        for item in self.order_line:
            # SFR Renovaciones no debe pedir factibilidad en plantilla económica
            if self.type_id.type_select in ['renovation']:
                continue
            if item.product_id.bool_is_study_economic:
                if not item.addresses_id.id:
                    error = True
            if item.product_id.bool_is_factibility:
                if not item.addresses_id.id:
                    error = True
                if not item.addresses_id.factibility_id.id:
                    error = True
                else:
                    if item.addresses_id.factibility_id.state == "draft":
                        error = True
        if error:
            raise UserError(
                _(
                    "The product : "
                    + str(item.product_id.name)
                    + " must be approved Feasibility study or Economic study "
                )
            )

        # SFR if any(app.request_status != "approved" for app in self.approval_sale_id):
        print('**************', self.approval_sale_id)
        if len(self.approval_sale_id) >= 1 and any(app.request_status != "approved" for app in self.approval_sale_id):
            raise UserError(
                "No se puede enviar correos en una solicitud que tiene aprobaciones en estado distinto de aprobado"
            )

        subscription_default = False
        mayor_plazo = 0
        if len(self.order_line) >= 1:
            mayor_plazo = self.order_line[0].addresses_id.recurring_interval
        for i in self.order_line:
            if i.subscription_id.id:
                subscription_default = i.subscription_id.id
            if i.addresses_id.recurring_interval > mayor_plazo:
                mayor_plazo = i.addresses_id.recurring_interval
        for i in self.order_line:
            i.fxo_subscription_id = subscription_default

        if self.type_id.is_migration and self.subscription_update_id.id:
            SubLine = line.subscription_update_line_id
            rewind = False
            for linea in self.order_line:
                # URO comentareo para que no se actualice la direccion directo en el item
                # linea_contrato = self.env["sale.subscription.line"].search(
                #     [
                #         ("analytic_account_id", "=", self.subscription_update_id.id),
                #         ("partner_street_destination", "=", linea.partner_street_destination.id),
                #     ]
                # )
                # if len(linea_contrato) == 1:
                #     linea_contrato[0].partner_street_destination = linea.partner_street_destination_replace.id
                self._agregate_migration_in_contract(self.subscription_update_id, SubLine, linea, rewind,
                                                     self.date_update_from)

        if self.type_id.change_state:
            for linea in self.order_line:
                linea_contrato = self.env["sale.subscription.line"].search(
                    [
                        ("analytic_account_id", "=", self.subscription_update_id.id),
                        ("partner_street_destination", "=", linea.partner_street_destination.id),
                    ]
                )
                if len(linea_contrato) == 1:
                    linea_contrato[0].state = self.type_id.change_state
        if self.type_id.type_select in ['upgrade', 'downgrade', 'upgrade_temp']:
            self.get_upgrade_downgrade()
        if self.type_id.type_select in ['renovation']:
            date_due = self.add_month(date.today(), mayor_plazo)
            self.subscription_update_id.date_due = date_due
            self.subscription_update_id.date = date_due  # SFR fecha de vencimiento estandar (odoo, controla vencimientos)
        return t

    def action_draft(self):
        orders = super(SaleOrder, self).action_draft()
        for ord in self:
            ord.get_upgrade_downgrade(rewind=True)
            if ord.type_id.is_migration and ord.subscription_update_id.id:
                rewind = True
                for linea in ord.order_line:
                    SubLine = linea.subscription_update_line_id
                    self._agregate_migration_in_contract(ord.subscription_update_id, SubLine, linea, rewind,
                                                         ord.date_update_from)

        return orders

    # Funcion para calcular el upgrade o downgrade de una linea de cotizacion
    # El parametro rewind hace lo opuesto a las operaciones de cada caso para volver al estado original de la linea de subscripcion
    def get_upgrade_downgrade(self, rewind=False):
        for line in self.order_line:
            SubLine = line.subscription_update_line_id
            if self.has_subscription_update_id and SubLine:
                vals = dict()
                if rewind:
                    qty = line.subscription_qty
                    price_subtotal = line.subscription_price_subtotal
                    vals.update(
                        {
                            "quantity": qty,
                            "price_subtotal": price_subtotal,
                        }
                    )
                    SubLine.write(vals)
                # URO se agrega el metodo _agregate_upgrade_in_contract para almacenar el historial de lo upgrades
                self._agregate_upgrade_in_contract(self.subscription_update_id, SubLine, line, rewind,
                                                       self.date_update_from)

    def action_quotation_send(self):
        t = super(SaleOrder, self).action_quotation_send()
        error = False
        for item in self.order_line:
            if item.product_id.bool_is_study_economic:
                if not item.addresses_id.id:
                    error = True
            if item.product_id.bool_is_factibility:
                if not item.addresses_id.id:
                    error = True
                if not item.addresses_id.factibility_id.id:
                    error = True
                else:
                    if item.addresses_id.factibility_id.state == "draft":
                        error = True
        if error:
            raise UserError(
                _("The product : %s must be approved Feasibility study or Economic study ") % item.product_id.name
            )

        if any(app.request_status != "approved" for app in self.approval_sale_id):
            raise UserError(
                "No se puede enviar correos en una solicitud que tiene aprobaciones en estado distinto de aprobado"
            )

        subscription_default = False
        for i in self.order_line:
            if i.subscription_id.id:
                subscription_default = i.subscription_id.id

        for i in self.order_line:
            i.fxo_subscription_id = subscription_default

        return t

    def write(self, vals):
        for i in self:
            for permission in i.approval_sale_id:
                if permission.request_status == "approved" and (
                        "partner_id" in vals
                        or "partner_invoice_id" in vals
                        or "partner_shipping_id" in vals
                        or "subscription_update_id" in vals
                        or "date_update_from" in vals
                        or "date_update_to" in vals
                        or "sale_order_template_id" in vals
                        or "validity_date" in vals
                        or "pricelist_id" in vals
                        or "type_id" in vals
                        or "payment_term_id" in vals
                        or "user_id" in vals
                        or "team_id" in vals
                        or "company_id" in vals
                        or "warehouse_id" in vals
                        or "picking_policy" in vals
                ):
                    raise UserError("No se puede modificar una cotización con aprobaciones.")
        t = super(SaleOrder, self).write(vals)
        return t

    def _agregate_upgrade_in_contract(self, subscription, SubLine, line, rewind, date_update_from):
        line_upgrade = self.env["subscription.line.upgrade"]
        if rewind is False:
            dicct_upgrade = dict()
            dicct_upgrade['subscription_id'] = subscription.id
            dicct_upgrade['sale_id'] = self.id
            dicct_upgrade['product_id'] = line.product_id.id
            dicct_upgrade['name'] = SubLine.name
            dicct_upgrade['uom_id'] = SubLine.uom_id.id
            dicct_upgrade['quantity'] = line.product_uom_qty
            dicct_upgrade['price_unit'] = line.price_unit
            dicct_upgrade['price_subtotal'] = line.price_subtotal
            dicct_upgrade['quantity_prev'] = line.subscription_qty
            dicct_upgrade['price_unit_prev'] = line.subscription_price_unit
            dicct_upgrade['price_subtotal_prev'] = line.subscription_price_subtotal
            dicct_upgrade['state'] = 'pending'
            dicct_upgrade['service_id'] = SubLine.service_id
            dicct_upgrade['upgrade_date'] = date_update_from
            dicct_upgrade['stop_date'] = False
            dicct_upgrade['subscription_update_line_id'] = line.subscription_update_line_id.id
            dicct_upgrade['invoice_status'] = 'pending' if self.type_id.type_select in ['upgrade',
                                                                                        'upgrade_temp'] else 'not_invoiced'
            dicct_upgrade['company_id'] = self.company_id.id
            if self.type_id.type_select == 'upgrade':
                select_type = 'upgrade'
            elif self.type_id.type_select == 'upgrade_temp':
                select_type = 'upgrade_temp'
            else:
                select_type = 'downgrade'
            dicct_upgrade['type'] = select_type
            dicct_upgrade['is_renovation'] = True if self.type_id.type_select == 'renovation' else False
            dicct_upgrade['renovation_type'] = 'other'
            if self.type_id.type_select == 'upgrade_temp':
                dicct_upgrade['upgrade_temp_finish_date'] = self.date_update_to
            line_upgrade.create(dicct_upgrade)
            # self._get_recurring_next_date(subscription)
        else:
            line_upgrade_ids = line_upgrade.search(
                [('subscription_id', '=', subscription.id), ('sale_id', '=', self.id),
                 ('company_id', '=', self.company_id.id)])
            for line in line_upgrade_ids:
                line.unlink()
        return True

    # URO se comenta porque cambia la lógica del sistema
    # def _agregate_downgrade_in_contract(self, subscription, SubLine, line, rewind, date_update_from):
    #     line_upgrade = self.env["subscription.line.upgrade"]
    #     if rewind is False:
    #         dicct_upgrade = dict()
    #         dicct_upgrade['subscription_id'] = subscription.id
    #         dicct_upgrade['sale_id'] = self.id
    #         dicct_upgrade['product_id'] = line.product_id.id
    #         dicct_upgrade['name'] = SubLine.name
    #         dicct_upgrade['uom_id'] = SubLine.uom_id.id
    #         dicct_upgrade['quantity'] = line.product_uom_qty
    #         dicct_upgrade['price_unit'] = line.price_unit
    #         dicct_upgrade['price_subtotal'] = line.price_subtotal
    #         dicct_upgrade['state'] = 'pending'
    #         dicct_upgrade['service_id'] = SubLine.service_id
    #         dicct_upgrade['upgrade_date'] = date_update_from
    #         dicct_upgrade['stop_date'] = False
    #         dicct_upgrade['subscription_update_line_id'] = line.subscription_update_line_id.id
    #         dicct_upgrade['invoice_status'] = 'not_invoiced'
    #         dicct_upgrade['company_id'] = self.company_id.id
    #         dicct_upgrade['type'] = line.up_down_type
    #         dicct_upgrade['is_renovation'] = True if self.type_id.type_select == 'renovation' else False
    #         dicct_upgrade['renovation_type'] = line.up_down_type
    #         line_upgrade.create(dicct_upgrade)
    #     else:
    #         line_upgrade_ids = line_upgrade.search(
    #             [('subscription_id', '=', subscription.id), ('sale_id', '=', self.id),
    #              ('company_id', '=', self.company_id.id)])
    #         for line in line_upgrade_ids:
    #             line.unlink()
    #     return True

    def _agregate_migration_in_contract(self, subscription, SubLine, line, rewind, date_update_from):
        line_upgrade = self.env["subscription.line.upgrade"]
        if rewind is False:
            dicct_upgrade = dict()
            dicct_upgrade['subscription_id'] = subscription.id
            dicct_upgrade['sale_id'] = self.id
            dicct_upgrade['product_id'] = line.product_id.id
            dicct_upgrade['name'] = SubLine.name
            dicct_upgrade['uom_id'] = SubLine.uom_id.id
            dicct_upgrade['quantity'] = line.product_uom_qty
            dicct_upgrade['price_unit'] = line.price_unit
            dicct_upgrade['price_subtotal'] = line.price_subtotal
            dicct_upgrade['state'] = 'pending'
            dicct_upgrade['service_id'] = SubLine.service_id
            dicct_upgrade['upgrade_date'] = date.today()
            dicct_upgrade['stop_date'] = False
            dicct_upgrade['subscription_update_line_id'] = line.subscription_update_line_id.id
            dicct_upgrade['invoice_status'] = 'not_invoiced'
            dicct_upgrade['company_id'] = self.company_id.id
            dicct_upgrade['from_address'] = line.partner_street_destination_replace.id
            dicct_upgrade['current_address'] = line.partner_street_destination.id
            dicct_upgrade['type'] = 'migration'
            dicct_upgrade['is_renovation'] = False
            dicct_upgrade['renovation_type'] = 'other'
            line_upgrade.create(dicct_upgrade)
        else:
            line_upgrade_ids = line_upgrade.search(
                [('subscription_id', '=', subscription.id), ('sale_id', '=', self.id),
                 ('company_id', '=', self.company_id.id)])
            for line in line_upgrade_ids:
                line.unlink()
        return True

    # URO metodo actualizado teniendo en cuenta renovaciones y adendas
    def update_existing_subscriptions(self):
        """
        Update subscriptions already linked to the order by updating or creating lines.

        :rtype: list(integer)
        :return: ids of modified subscriptions
        """
        res = []
        for order in self:
            if order.type_id.type_select == 'renovation':
                subscriptions = order.subscription_update_id
                if not subscriptions:
                    raise UserError('Debe seleccionar el Contrato a Renovar.')
                subscriptions.increment_period()
                subscriptions.set_open()
                for line in order.order_line:
                    if line.product_id.recurring_invoice:
                        sub_line = subscriptions.recurring_invoice_line_ids.filtered(
                            lambda l: l.state == 'done' and l.service_id == line.service_id_2)
                        if not sub_line:
                            values = {
                                "analytic_account_id": subscriptions.id,
                                "product_id": line.product_id.id,
                                "name": line.name,
                                "quantity": line.product_uom_qty,
                                "uom_id": line.product_uom.id,
                                "price_unit": line.price_unit,
                                "discount": line.discount if line.order_id.subscription_management != "upsell" else False,
                                "partner_street_destination": line.partner_street_destination.id,
                                "partner_street_destination_header": line.partner_street_destination_header.id
                                if line.partner_street_destination_header
                                else None,
                                "service_id": line.service_id_2 if line.service_id_2 else "",
                                "type_conection": line.type_conection if line.type_conection else "",
                                "type_conection_relation": line.type_conection_relation
                                if line.type_conection_relation
                                else "",
                                "transport_physic_relation": line.transport_physic_relation
                                if line.transport_physic_relation
                                else "",
                                "customer_lead": line.customer_lead if line.customer_lead else "",
                                "type_item": line.type_item if line.type_item else "",
                                "sequence": line.sequence if line.sequence else "",
                                "sequence2": line.sequence2 if line.sequence2 else "",
                                "item_origin": line.item_origin if line.item_origin else "",
                                "way_to_pay_id": line.way_to_pay_id.id if line.way_to_pay_id else None,
                                "type_cut": line.type_cut if line.type_cut else "",
                            }
                            line_sub_obj = self.env['sale.subscription.line'].create(values)
                            if line_sub_obj.quantity != 0:
                                line_sub_obj.price_unit = line.price_subtotal / line_sub_obj.quantity
                        else:
                            rewind = False
                            type_renovation = 'other'
                            self._agregate_renovation_in_contract(subscriptions, sub_line, line, rewind,
                                                                  type_renovation)
                    else:
                        raise UserError(
                            'No puede renovar el producto %s debido a que no tiene marcado Producto de la suscripción' % line.product_id.name)
            elif order.type_id.type_select == 'adenda':
                subscriptions = order.subscription_update_id
                if not subscriptions:
                    raise UserError('Debe seleccionar el Contrato a Adendar.')
                for line in order.order_line:
                    if line.product_id.recurring_invoice:
                        values = {
                            "analytic_account_id": subscriptions.id,
                            "product_id": line.product_id.id,
                            "name": line.name,
                            "quantity": line.product_uom_qty,
                            "uom_id": line.product_uom.id,
                            "price_unit": line.price_unit,
                            "discount": line.discount if line.order_id.subscription_management != "upsell" else False,
                            "partner_street_destination": line.partner_street_destination.id,
                            "partner_street_destination_header": line.partner_street_destination_header.id
                            if line.partner_street_destination_header
                            else None,
                            "service_id": line.service_id_2 if line.service_id_2 else "",
                            "type_conection": line.type_conection if line.type_conection else "",
                            "type_conection_relation": line.type_conection_relation
                            if line.type_conection_relation
                            else "",
                            "transport_physic_relation": line.transport_physic_relation
                            if line.transport_physic_relation
                            else "",
                            "customer_lead": line.customer_lead if line.customer_lead else "",
                            "type_item": line.type_item if line.type_item else "",
                            "sequence": line.sequence if line.sequence else "",
                            "sequence2": line.sequence2 if line.sequence2 else "",
                            "item_origin": line.item_origin if line.item_origin else "",
                            "way_to_pay_id": line.way_to_pay_id.id if line.way_to_pay_id else None,
                            "type_cut": line.type_cut if line.type_cut else "",
                        }
                        line_sub_obj = self.env['sale.subscription.line'].create(values)
                        if line_sub_obj.quantity != 0:
                            line_sub_obj.price_unit = line.price_subtotal / line_sub_obj.quantity
                    else:
                        raise UserError(
                            'No puede adendar el producto %s debido a que no tiene marcado Producto de la suscripción' % line.product_id.name)
            else:
                subscriptions = order.order_line.mapped('subscription_id').sudo()
                if subscriptions and order.subscription_management != 'renew':
                    order.subscription_management = 'upsell'
                res.append(subscriptions.ids)
                if order.subscription_management == 'renew':
                    subscriptions.wipe()
                    subscriptions.increment_period()
                    subscriptions.set_open()
                for subscription in subscriptions:
                    subscription_lines = order.order_line.filtered(
                        lambda l: l.subscription_id == subscription and l.product_id.recurring_invoice)
                    line_values = subscription_lines._update_subscription_line_data(subscription)
                    subscription.write({'recurring_invoice_line_ids': line_values})
        return res

    def _agregate_renovation_in_contract(self, subscription, SubLine, line, rewind, type_renovation):
        line_upgrade = self.env["subscription.line.upgrade"]
        if rewind is False:
            dicct_upgrade = dict()
            dicct_upgrade['subscription_id'] = subscription.id
            dicct_upgrade['sale_id'] = self.id
            dicct_upgrade['product_id'] = line.product_id.id
            dicct_upgrade['name'] = SubLine.name
            dicct_upgrade['uom_id'] = SubLine.uom_id.id
            invoice_status = 'not_invoiced'
            dicct_upgrade['quantity'] = line.product_uom_qty
            dicct_upgrade['price_unit'] = line.price_unit
            dicct_upgrade['price_subtotal'] = line.price_subtotal
            dicct_upgrade['quantity_prev'] = line.subscription_qty
            dicct_upgrade['price_unit_prev'] = line.subscription_price_unit
            dicct_upgrade['price_subtotal_prev'] = line.subscription_price_subtotal
            dicct_upgrade['state'] = 'pending'
            dicct_upgrade['service_id'] = SubLine.service_id
            dicct_upgrade['stop_date'] = False
            dicct_upgrade['subscription_update_line_id'] = SubLine.id
            dicct_upgrade['invoice_status'] = invoice_status
            dicct_upgrade['company_id'] = self.company_id.id
            dicct_upgrade['upgrade_date'] = date.today()
            dicct_upgrade['is_renovation'] = True
            dicct_upgrade['renovation_type'] = 'other'
            if line.product_uom_qty > line.subscription_qty \
                    and line.price_subtotal > line.subscription_price_subtotal:
                dicct_upgrade['type'] = 'upgrade'
                dicct_upgrade['invoice_status'] = 'pending'
            line_upgrade.create(dicct_upgrade)
        else:
            line_upgrade_ids = line_upgrade.search(
                [('subscription_id', '=', subscription.id), ('sale_id', '=', self.id),
                 ('company_id', '=', self.company_id.id)])
            for line in line_upgrade_ids:
                line.unlink()
        return True

    # URO funciona para sumar meses a una fecha
    def add_month(self, mDate, months):
        nYear = mDate.year + months / 12
        dMonth = months % 12
        if dMonth + mDate.month > 12:
            nYear += 1
        nMonth = (mDate.month + dMonth) % 12 or 12
        nDay = mDate.day
        try:
            date_due = datetime(int(nYear), nMonth, nDay)
        except Exception as e:
            pass
        if nMonth == 2:
            nDay = 28
            if (nYear % 4 == 0 and nYear % 100 != 0) or nYear % 400 == 0:
                nDay = 29
            else:
                nDay = 30
            date_due = datetime(int(nYear), nMonth, nDay)
        return date_due

    def _split_subscription_lines(self):
        """Split the order line according to subscription templates that must be created."""
        self.ensure_one()
        res = dict()
        template = self.subscription_template_id
        lines = self.order_line.filtered(lambda l: l.product_id.recurring_invoice == True)
        res[template] = lines
        return res

    def _prepare_subscription_data(self, template):
        values = super(SaleOrder, self)._prepare_subscription_data(template)
        values['signature_date'] = self.signature_date
        return values


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    compute_have_factibility = fields.Boolean("Have Factibility", compute="get_compute_have_factibility")

    def get_compute_have_factibility(self):
        for i in self:
            if i.addresses_id.id:
                if i.addresses_id.factibility_id.state in ("open", "done"):
                    i.compute_have_factibility = True
                else:
                    i.compute_have_factibility = False
            else:
                i.compute_have_factibility = False

    service_id = fields.Char(related="subscription_update_line_id.service_id", string="Id Servicio")
    way_to_pay = fields.Char("Old Field")
    install_rate = fields.Float("Old Field")
    type_item = fields.Selection([("Cabecera", "Cabecera"), ("Direccion", "Remoto")], "Tipo de Item")
    way_to_pay_id = fields.Many2one("account.payment.term", "Forma de Pago")
    nro_quotes = fields.Integer("Nro. Cuotas")
    type_term = fields.Selection([("Indeterminado", "Indeterminado"), ("Forzoso", "Forzoso")], "Tipo de Plazo")
    type_term_qty = fields.Integer("Nro. Plazo Forzoso")
    type_term_time = fields.Selection([("Dias", "Dias"), ("Meses", "Meses"), ("Años", "Años")], "Tiempo Plazo Forzoso")
    grace_period = fields.Integer("Periodo Gracia")
    grace_period_time = fields.Selection(
        [("Dias", "Dias"), ("Meses", "Meses"), ("Años", "Años")], "Periodo Gracia Tiempo"
    )
    type_cut = fields.Selection([("cute", "Con Corte"), ("notcute", "Sin Corte"), ("free", "Libre")], "Tipo de corte")

    type_category = fields.Selection(
        [("1", "Internet"), ("2", "Remoto"), ("3", "Telefonia IP"), ("4", "Otros")], "Tipo Separacion"
    )
    type_conection_relation = fields.Char("Tipo de conexion relacional", help="Por ejemplo: (1:1)")
    type_conection = fields.Char("Tipo de Conexion", help="Por ejemplo OverBooking")  # overbooking
    transport_physic_relation = fields.Selection(
        [("Fibra Optica", "Fibra Optica"), ("Radioenlace", "Radioenlace"), ("Satelital", "Satelital")],
        "Medio Transporte Fisico",
    )
    fxo_subscription_id = fields.Many2one("sale.subscription", "Subscription", copy=False, check_company=True)

    bool_is_study_economic = fields.Boolean(related="product_id.bool_is_study_economic")
    bool_is_factibility = fields.Boolean(related="product_id.bool_is_factibility")
    bool_qty_street = fields.Boolean(related="product_id.bool_qty_street")
    addresses_id = fields.Many2one(comodel_name="sale.order.line.qty_street", string="Addresses", copy=False)
    factibility_id = fields.Many2one(
        comodel_name="sale.order.line.factibility",
        related="addresses_id.factibility_id",
        string="Factibility",
        store=True,
    )
    install_type = fields.Selection(related="order_id.install_type")
    edit_price_unit = fields.Selection(related="product_template_id.edit_price_unit", store=True)

    price_unit1 = fields.Float(string="Precio unidad", digits=(12, 4))
    product_uom_qty1 = fields.Float(string="Cantidad")
    product_uom1 = fields.Many2one(comodel_name="uom.uom", string="Unidad")
    price_subtotal1 = fields.Float(string="SubTotal", compute="get_price_subtotal1", store=True)

    is_migration = fields.Boolean("Is migration")
    type_rel = fields.Many2one("sale.order.type", "Type")

    order_partner_street_id = fields.Many2one(comodel_name="res.partner", string="Partner")
    partner_street_destination = fields.Many2one(comodel_name="res.partner", string="Direccion Destino")
    partner_street_destination_header = fields.Many2one("res.partner", string="Direccion Cabecera")
    service_id_2 = fields.Char(string="ID Servicio")
    partner_street_destination_replace = fields.Many2one(comodel_name="res.partner", string="Direccion Destino Nuevo")
    item_origin = fields.Char(string="IT/Referencia", default="0")
    sale_order_head_id = fields.Many2one("sale.order.line", "Cabecera")
    # Registrar persona de contacto por cada direccion de instalación, por defecto debe importar de  partner_order_id (cabecesa)
    partner_order_id = fields.Many2one(comodel_name="res.partner", string="Persona Contacto")
    partner_contact_id = fields.Many2one(comodel_name="res.partner", string="Persona Contacto")
    price_unit1_invisible = fields.Float(string="Precio unidad", compute="get_price_unit1_invisible", digits=(12, 4))
    price_unit_invisible = fields.Float(string="Precio unidad", compute="get_price_unit_invisible", digits=(12, 4))
    # @api.onchange('partner_id')
    # def onchange_partner_id_(self):
    # if self.partner_id:
    # if self.partner_id.child_ids:
    # self.partner_contact_id = self.partner_id.child_ids[0].id

    # Campo para definir el tipo de downgrade o upgrade que se va a utilizar
    up_down_type = fields.Selection(
        [
            ("up_same", "Upgrade Solo Mbps"),
            ("up_reduction", "Upgrade Reduccion de Tarifa"),
            ("up_add", "Upgrade Mbps y Renta"),
            ("down_same", "Downgrade Solo Mbps"),
            ("down_reduction", "Downgrade Reduccion de Tarifa"),
            ("down_add", "Downgrade Mbps Renta"),
        ],
        string="Tipo de Upgrade o Downgrade",
    )
    subscription_qty = fields.Float(related="subscription_update_line_id.quantity", string="Cantidad de Subscripcion")
    subscription_qty_total = fields.Float(string="Nueva Cantidad de Subscripcion")
    subscription_price_unit = fields.Float(
        related="subscription_update_line_id.price_unit", string="Precio Unitario de Subscripcion"
    )
    subscription_price_unit_total = fields.Float(string="Nuevo Precio Unitario Subscripcion")
    subscription_price_subtotal = fields.Float(
        related="subscription_update_line_id.price_subtotal", string="Subtotal de Suscripcion"
    )
    subscription_price_subtotal_total = fields.Float(string="Nuevo Subtotal de Subscripcion")
    qty_streets = fields.One2many("sale.order.line.qty_street", "name")
    is_renovation = fields.Boolean(string='Renovación', compute='_compute_is_renovation')

    @api.depends('order_id')
    def _compute_is_renovation(self):
        for line in self:
            if line.order_id.type_id.type_select == 'renovation':
                line.is_renovation = True
            else:
                line.is_renovation = False

    @api.onchange("up_down_type", "subscription_update_line_id")
    def get_subscription_data(self):
        if self.subscription_update_line_id and self.up_down_type:
            up_qty = self.subscription_qty + self.product_uom_qty
            down_qty = self.subscription_qty - self.product_uom_qty
            if self.up_down_type == "up_same":
                self.subscription_qty_total = up_qty
                self.subscription_price_unit_total = self.subscription_price_subtotal / up_qty
                self.subscription_price_subtotal_total = (
                        self.subscription_price_unit_total * self.subscription_qty_total
                )
            elif self.up_down_type == "up_reduction":
                new_subtotal = self.subscription_price_subtotal - self.price_subtotal
                self.subscription_qty_total = up_qty
                self.subscription_price_unit_total = new_subtotal / up_qty
                self.subscription_price_subtotal_total = (
                        self.subscription_price_unit_total * self.subscription_qty_total
                )
            elif self.up_down_type == "up_add":
                new_subtotal = self.subscription_price_subtotal + self.price_subtotal
                self.subscription_qty_total = up_qty
                self.subscription_price_unit_total = new_subtotal / up_qty
                self.subscription_price_subtotal_total = (
                        self.subscription_price_unit_total * self.subscription_qty_total
                )
            elif self.up_down_type == "down_same":
                self.subscription_qty_total = down_qty
                self.subscription_price_unit_total = self.subscription_price_subtotal / down_qty
                self.subscription_price_subtotal_total = (
                        self.subscription_price_unit_total * self.subscription_qty_total
                )
            elif self.up_down_type == "down_reduction":
                new_subtotal = self.subscription_price_subtotal - self.price_subtotal
                self.subscription_qty_total = down_qty
                self.subscription_price_unit_total = new_subtotal / down_qty
                self.subscription_price_subtotal_total = (
                        self.subscription_price_unit_total * self.subscription_qty_total
                )
            elif self.up_down_type == "down_add":
                new_subtotal = self.subscription_price_subtotal - self.price_subtotal
                self.subscription_qty_total = down_qty
                self.subscription_price_unit_total = new_subtotal / down_qty
                self.subscription_price_subtotal_total = (
                        self.subscription_price_unit_total * self.subscription_qty_total
                )
            else:
                pass

    @api.onchange("subscription_update_line_id", "order_id.type_id")
    def get_subscription_destination(self):
        if self.order_id.type_id.type_select in ['downgrade', 'upgrade', 'upgrade_temp']:
            self.service_id_2 = self.subscription_update_line_id.service_id
        if not self.partner_street_destination_replace and self.subscription_update_line_id and \
                self.order_id.type_id.type_select in ['downgrade', 'upgrade', 'upgrade_temp']:
            self.partner_street_destination = self.subscription_update_line_id.partner_street_destination
            self.product_uom_qty = self.subscription_update_line_id.quantity
            self.price_unit1 = self.subscription_update_line_id.price_unit
            self.price_unit = self.subscription_update_line_id.price_unit
            self.price_subtotal1 = self.subscription_update_line_id.price_subtotal
        if not self.partner_street_destination_replace and self.subscription_update_line_id and \
                self.order_id.type_id.type_select in ['migration']:
            self.partner_street_destination_replace = self.subscription_update_line_id.partner_street_destination
            self.partner_street_destination = self.subscription_update_line_id.partner_street_destination if not self.product_id.bool_is_factibility else None
            self.nro_quotes = 1

    @api.onchange("sale_order_head_id")
    def onchange_sale_order_head_id(self):
        if self.sale_order_head_id.id:
            self.item_origin = self.sale_order_head_id.order_id.name + "|" + str(self.sale_order_head_id.sequence2)

    @api.onchange("type_rel")
    def onchange_type_rel(self):
        self.is_migration = self.type_rel.is_migration
        if self.type_rel.type_select == 'renovation':
            self.is_renovation = True
        else:
            self.is_renovation = False

    def _prepare_subscription_line_data(self):
        """Prepare a dictionnary of values to add lines to a subscription."""
        values = list()
        for line in self:
            values.append(
                (
                    0,
                    False,
                    {
                        "product_id": line.product_id.id,
                        "name": line.name,
                        "quantity": line.product_uom_qty,
                        "uom_id": line.product_uom.id,
                        "price_unit": line.price_unit,
                        "discount": line.discount if line.order_id.subscription_management != "upsell" else False,
                        "partner_street_destination": line.partner_street_destination.id,
                        "partner_street_destination_header": line.partner_street_destination_header.id
                        if line.partner_street_destination_header
                        else None,
                        "service_id": line.service_id_2 if line.service_id_2 else "",
                        "type_conection": line.type_conection if line.type_conection else "",
                        "type_conection_relation": line.type_conection_relation
                        if line.type_conection_relation
                        else "",
                        "transport_physic_relation": line.transport_physic_relation
                        if line.transport_physic_relation
                        else "",
                        "customer_lead": line.customer_lead if line.customer_lead else "",
                        "type_item": line.type_item if line.type_item else "",
                        "sequence": line.sequence if line.sequence else "",
                        "sequence2": line.sequence2 if line.sequence2 else "",
                        "item_origin": line.item_origin if line.item_origin else "",
                        "way_to_pay_id": line.way_to_pay_id.id if line.way_to_pay_id else None,
                        "type_cut": line.type_cut if line.type_cut else "",
                    },
                )
            )
        return values

    @api.depends("price_unit")
    def get_price_unit_invisible(self):
        for i in self:
            i.price_unit_invisible = i.price_unit

    def get_price_unit1_invisible(self):
        for i in self:
            i.price_unit1_invisible = i.price_unit1

    @api.depends("price_unit1", "product_uom_qty1")
    def get_price_subtotal1(self):
        for i in self:
            i.price_subtotal1 = i.price_unit1 * i.product_uom_qty1

    @api.onchange("price_unit1", "product_uom_qty1", "product_uom1")
    def onchange_price_unit1(self):
        self.price_unit1_invisible = self.price_unit1
        self.price_subtotal1 = self.price_unit1 * self.product_uom_qty1
        if self.addresses_id.id == False and self.state == "draft":
            self.price_unit = self.price_unit1
            self.product_uom_qty = self.product_uom_qty1
            self.product_uom = self.product_uom1.id

    @api.onchange("price_unit", "product_uom", "product_uom_qty")
    def onchange_price_unit_update(self):
        self.price_unit_invisible = self.price_unit
        if self.addresses_id.id == False:
            self.price_unit1 = self.price_unit
            self.product_uom_qty1 = self.product_uom_qty
            self.product_uom1 = self.product_uom.id

    @api.onchange("product_id", "product_uom_qty")
    def onchange_subscription_update_id(self):
        self.set_order_partner_street_id()
        self.set_subscription_update_id()

    def set_order_partner_street_id(self):
        self.order_partner_street_id = self.order_id.partner_id.id

    def set_subscription_update_id(self):
        self.subscription_update_id = self.order_id.subscription_update_id

    def action_qty_street(self):
        # verificar si existe un adresss y colocarlo al que corresponde
        try:
            if self.qty_streets:
                self.addresses_id = self.qty_streets[0]
        except:
            # para que no haga nada pi pi pi
            a = 1

        action = self.env.ref("fxo_feasibility.sale_order_line_qty_street_action").read()[0]
        parameter = self.env["fxo.sale.main.parameter"].search([("name", "=", self.env.company.id)])

        # raise ValueError(self.item_origin)
        if len(self.item_origin.split("|")) > 1:
            subscription_id = self.env["sale.order.line"].search(
                [
                    ("order_id.name", "=", self.item_origin.split("|")[0]),
                    ("sequence2", "=", int(self.item_origin.split("|")[1])),
                ]
            )
        else:
            subscription_id = self.env["sale.order.line"].search(
                [("order_id", "=", self.order_id.id), ("sequence2", "=", int(self.item_origin))]
            )
        recurring_interval = subscription_id.product_id.subscription_template_id.recurring_interval

        # if recurring_interval == 0:
        #   raise UserError(_("El Plazo del contrato del Item Origen debe ser mayor a 0" ))

        if parameter.gross_profit_percent == 0:
            raise UserError(_("Configurar en Parametro de factibilidad Porcentaje margen de utilidad"))

        if parameter.producto_renta_mensual.id == False:
            raise UserError(_("Configurar en Parametro de factibilidad pestaña Ingreso Producto Renta Mensual"))

        if parameter.producto_costo_instalacion.id == False:
            raise UserError(_("Configurar en Parametro de factibilidad pestaña Egreso Producto Costo Instalacion"))

        if self.partner_street_destination.id == False:
            raise UserError(_("Indique la direccion en este item"))

        # if self.partner_contact_id.id == False:
        # raise UserError(_("Indique persona contacto del cliente: Registrar en el Socio" ))

        # if self.product_uom_qty == 0:
        # 	raise UserError(_("la cantidad debe ser mayor a 0 "))

        # if self.price_unit == 0:
        # 	raise UserError(_("el precio debe ser mayor a 0 "))

        flag_nuevo = False
        if self.addresses_id.id:
            action["res_id"] = self.addresses_id.id
        else:
            is_migration_or_adenda = False
            if self.order_id.type_id.type_select in ['migration',
                                                     'adenda']:
                if not self.order_id.subscription_update_id.date:
                    raise UserError('El contrato seleccionado no tiene fecha final.')
                is_migration_or_adenda = True
            self.addresses_id = self.env["sale.order.line.qty_street"].create(
                {
                    "name": self.id,
                    "is_migration_or_adenda": is_migration_or_adenda
                }
            )
            flag_nuevo = True

        if self.product_id.bool_is_factibility:
            temp = self.env["sale.order.line.factibility"].search(
                [
                    ("state_id", "=", self.partner_street_destination.state_id.id),
                    ("province_id", "=", self.partner_street_destination.province_id.id),
                    ("district_id", "=", self.partner_street_destination.district_id.id),
                    ("type_via", "=", self.partner_street_destination.type_via.id),
                    ("name_via", "ilike", self.partner_street_destination.name_via),
                    ("number_via", "ilike", self.partner_street_destination.number_via),
                    ("number_new", "ilike", self.partner_street_destination.number_new),
                    ("product_id", "=", self.product_id.id),
                    ("state", "in", ["draft", "open", "done"]),
                ],
                limit=1,
            )
            if len(temp) == 0:
                user_obj = False
                cont_ob = 999999
                for oj in self.env.user.sale_team_id.user_factibility_id.members:
                    nro_f = len(self.env["sale.order.line.factibility"].search([("user_id", "=", oj.id)]))
                    if nro_f < cont_ob:
                        cont_ob = nro_f
                        user_obj = oj.id
                temp = self.env["sale.order.line.factibility"].create(
                    {
                        "origin_sale_order_id": self.order_id.id,
                        "state_id": self.partner_street_destination.state_id.id,
                        "province_id": self.partner_street_destination.province_id.id,
                        "district_id": self.partner_street_destination.district_id.id,
                        "type_via": self.partner_street_destination.type_via.id,
                        "name_via": self.partner_street_destination.name_via,
                        "number_via": self.partner_street_destination.number_via,
                        "number_new": self.partner_street_destination.number_new,
                        "state": "draft",
                        "duration_type": "Days",
                        "install_duration": 1,
                        "user_id": user_obj,
                        "product_id": self.product_id.id
                    }
                )

            if self.addresses_id.factibility_id.id == False:
                self.addresses_id.factibility_id = temp
                action["res_id"] = self.addresses_id.id

        if self.addresses_id.factibility_id.state != "draft":
            self.addresses_id.install_cost = self.addresses_id.factibility_id.install_cost

        # self.addresses_id.update()
        if flag_nuevo:
            self.addresses_id.porc_utilidad = self.product_id.porcent_aprove
            # URO asignacion de plazo del contrato si es traslado o adenda 
            if self.order_id.type_id.type_select in ['migration',
                                                     'adenda']:
                if not self.order_id.subscription_update_id.date:
                    raise UserError('El contrato seleccionado no tiene fecha final.')
                months = self._get_month_due_contract()
                if months < 1:
                    raise UserError('Contrato vencido, para realizar esta operacion es necesario renovar.')
                self.addresses_id.recurring_interval = months

        # URO asignando el plazo del contrato del campo nuevo plantilla de contrato puesto en las cotizaciones
        if self.order_id.type_id.type_select not in ['migration',
                                                     'adenda'] and self.order_id.subscription_template_id and self.order_id.type_id.has_subscription_template_id in [
            'required', 'optional']:
            months = self.order_id.subscription_template_id.recurring_rule_count
            if months < 1:
                raise UserError('# de periodos no definido en plantilla del contrato seleccionado')
            self.addresses_id.recurring_interval = months

        # URO comente este codigo de Sixto debido al nuevo proceso relacionado con el campo plantilla de contrato en las cotizaciones
        # SFR si es renovacion debe asignar el plazo de plantilla de contrato (recurring_rule_count)
        # if self.order_id.type_id.type_select in ['renovation']:
        #     months = self.order_id.subscription_update_id.template_id.recurring_rule_count
        #     if months < 1:
        #         raise UserError('# de periodos no definido en plantilla del contrato seleccionado')
        #     self.addresses_id.recurring_interval = months

        return action

    def action_factibility(self):
        action = self.env.ref("fxo_feasibility.action_sale_order_line_factibility").read()[0]
        if self.factibility_id.id:
            action["res_id"] = self.factibility_id.id
        else:
            self.factibility_id = self.env["sale.order.line.factibility"].create(
                {
                    "name": self.order_id.id,
                    "line": self.id,
                }
            )
            action["res_id"] = self.factibility_id.id
        return action

    def action_mapa(self):
        self.ensure_one()
        action = self.env.ref("fxo_feasibility.res_partner_view_map_extend_action").read()[0]
        action["context"] = {
            "search_default_name": self.partner_street_destination.display_name,
        }
        return action

    def write(self, vals):
        for i in self:
            # raise ValueError(i.order_id)

            for permission in i.order_id.approval_sale_id:
                if permission.request_status == "approved":
                    if len(vals) == 1 and "sequence" in vals:
                        pass
                    elif len(vals) == 1 and "sequence2" in vals:
                        pass
                    elif len(vals) == 1 and "subscription_id" in vals:
                        pass
                    elif len(vals) == 1 and "project_id" in vals:
                        pass
                    elif len(vals) == 1 and "fxo_subscription_id" in vals:
                        pass
                    elif len(vals) == 1 and "service_id_2" in vals:
                        pass
                    else:
                        raise UserError("No se puede modificar una cotización con aprobaciones.")

            if i.order_id.state != "draft":
                if "price_unit" in vals:
                    del vals["price_unit"]

                if "price_unit1" in vals:
                    del vals["price_unit1"]

                if "product_uom_qty" in vals:
                    del vals["product_uom_qty"]

                if "product_uom_qty1" in vals:
                    del vals["product_uom_qty1"]

                if "product_uom" in vals:
                    del vals["product_uom"]

                if "product_uom1" in vals:
                    del vals["product_uom1"]
            super(SaleOrderLine, i).write(vals)

    @api.model
    def create(self, vals):
        t = super(SaleOrderLine, self).create(vals)
        for i in t:
            if i.product_id.bool_is_factibility or i.product_id.bool_is_study_economic:
                i.action_qty_street()
        return t

    def unlink(self):
        return super(SaleOrderLine, self).unlink()

    @api.onchange("subscription_update_line_id")
    def _onchange_is_renovation(self):
        for rec in self:
            if rec.is_renovation and rec.subscription_update_line_id:
                if rec.subscription_update_line_id.service_id != rec.service_id_2:
                    raise UserError(
                        'Cuando es Renovación debe seleccionar el mismo Item del Contrato que coincide con el Id Servicio.')

    @api.constrains("subscription_update_line_id")
    def _constrains_is_renovation(self):
        for rec in self:
            if rec.is_renovation and rec.subscription_update_line_id:
                if rec.subscription_update_line_id.service_id != rec.service_id_2:
                    raise UserError(
                        'Cuando es Renovación debe seleccionar el mismo Item del Contrato que coincide con el Id Servicio.')

    # URO metodo para devolver el numero de meses que falta para vencer el contrato
    # SFR campo date, es capo original de sale_subscription, date_due es un campo referencial, no restringe facturacion ni vencimientos
    def _get_month_due_contract(self):
        # d1 = self.order_id.subscription_update_id.date_due
        if not self.order_id.subscription_update_id.date:
            raise UserError('El contrato seleccionado no tiene fecha final.')
        d1 = self.order_id.subscription_update_id.date
        d2 = date.today()
        months = (d1.year - d2.year) * 12 + d1.month - d2.month
        return months
