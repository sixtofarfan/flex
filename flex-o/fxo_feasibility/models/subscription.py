# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    sale_order_line_detalle = fields.One2many(
        comodel_name="sale.order.line", inverse_name="fxo_subscription_id", string="Lineas del Pedido"
    )
    historial_udt_ids = fields.One2many(
        comodel_name="subscription.line.upgrade", inverse_name="subscription_id", string="UDT"
    )

    # URO algoritmo para generar presupuesto de renovacion
    def _prepare_renewal_order_values(self):
        res = dict()
        for subscription in self:
            order_lines = []
            fpos_id = self.env['account.fiscal.position'].with_context(
                force_company=subscription.company_id.id).get_fiscal_position(subscription.partner_id.id)
            for line in subscription.recurring_invoice_line_ids.filtered(lambda l: l.state == 'done'):
                order_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.product_id.product_tmpl_id.name,
                    'subscription_id': subscription.id,
                    'product_uom': line.uom_id.id,
                    'product_uom1': line.uom_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom_qty1': line.quantity,
                    'price_unit': line.price_unit,
                    'price_unit1': line.price_unit,
                    'tax_id': line.product_id.sudo().taxes_id.ids,
                    'price_unit1_invisible': line.price_unit,
                    'price_unit_invisible': line.price_unit,
                    'discount': line.discount,
                    'service_id_2': line.service_id,
                    'partner_street_destination': line.partner_street_destination.id,
                    'partner_contact_id': line.partner_street_destination.id,
                    'price_subtotal': line.price_subtotal,
                    'currency_id': line.currency_id.id,
                }))
            addr = subscription.partner_id.address_get(['delivery', 'invoice'])
            sale_order = subscription.env['sale.order'].search(
                [('order_line.subscription_id', '=', subscription.id)],
                order="id desc", limit=1)
            type = self.env['sale.order.type'].search([('type_select', '=', 'renovation')], limit=1)
            if type:
                type_id = type.id
            else:
                type_id = False
            res[subscription.id] = {
                'pricelist_id': subscription.pricelist_id.id,
                'partner_id': subscription.partner_id.id,
                'partner_invoice_id': addr['invoice'],
                'partner_shipping_id': addr['delivery'],
                'currency_id': subscription.pricelist_id.currency_id.id,
                'order_line': order_lines,
                'analytic_account_id': subscription.analytic_account_id.id,
                'subscription_management': 'renew',
                'origin': subscription.code,
                'note': subscription.description,
                'fiscal_position_id': fpos_id,
                'user_id': subscription.user_id.id,
                'payment_term_id': sale_order.payment_term_id.id if sale_order else subscription.partner_id.property_payment_term_id.id,
                'company_id': subscription.company_id.id,
                'type_id': type_id,
                'subscription_update_id': subscription.id,
            }
        return res


class SaleSubscriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    is_nubyx = fields.Boolean(related="product_id.product_tmpl_id.is_nubyx")

    product_id = fields.Many2one(required=False)
    uom_id = fields.Many2one(required=False)
    product_uom_category_id = fields.Many2one(readonly=False)
    price_unit = fields.Float(required=False)
    sale_update_id = fields.Many2many(
        comodel_name="sale.order.line", string="Item Order Line", compute="_compute_sale_update_id"
    )
    type_conection = fields.Char(string="Tipo de Conexion")
    type_conection_relation = fields.Char(string="Tipo de Conexion Relacional")
    transport_physic_relation = fields.Selection(
        [("Fibra Optica", "Fibra Optica"), ("Radioenlace", "Radioenlace"), ("Satelital", "Satelital")],
        string="Medio Fisico",
    )
    customer_lead = fields.Float(string="Plazo de entrega")
    type_item = fields.Selection([("Cabecera", "Cabecera"), ("Direccion", "Remoto")], string="Tipo de Item")
    display_type = fields.Selection(
        [
            ("line_section", "Section"),
            ("line_note", "Note"),
        ],
        default=False,
        help="Technical field for UX purpose.",
    )
    state = fields.Selection(selection_add=[("pending", "Instalacion"), ("cancel", "Baja"), ("cancel-adm", " Baja-Adm")],
                             default="pending")

    sequence = fields.Integer(index=True, string="Secuencia")
    sequence2 = fields.Integer(string=u"# Item")
    item_origin = fields.Integer(string="IT/Referencia")
    way_to_pay_id = fields.Many2one("account.payment.term", "Forma de Pago")
    type_cut = fields.Selection([("cute", "Con Corte"), ("notcute", "Sin Corte"), ("free", "Libre")], "Tipo de corte")
    service_id = fields.Char(string="Id Servicio")
    active_sequence = fields.Boolean(default=True)
    partner_street_destination_header = fields.Many2one("res.partner", string="Direccion Cabecera")
    upgrade_date = fields.Date(string="Fecha Upgrade")

    @api.model
    def create(self, vals):
        rec = super(SaleSubscriptionLine, self).create(vals)
        if rec.active_sequence:
            # rec.service_id = self.env["ir.sequence"].next_by_code("service_id_code") or ""
            rec._compute_sale_update_id()
        return rec

    def _compute_sale_update_id(self):
        for item in self:
            item.sale_update_id = self.env["sale.order.line"].search(
                [("subscription_id", "=", item.analytic_account_id.id), ("product_id", "=", item.product_id.id)]
            )
            for order in item.analytic_account_id.sale_update_id:
                for line in order.order_line:
                    if item.order_partner_street_id.id == line.order_partner_street_id.id:
                        if order.state in ("done", "sale"):
                            item.sale_update_id += line
            # item.update_amaout()

    # def update_amaout(self):
    #     date_new = fields.Date.today()
    #     recurring_total = 0
    #     for line in self.sale_update_id:
    #         if line.date_update_from:
    #             if date_new >= line.date_update_from:
    #                 if line.date_update_to:
    #                     if line.date_update_to >= date_new:
    #                         recurring_total += line.price_subtotal
    #                 else:
    #                     recurring_total += line.price_subtotal
    #         else:
    #             recurring_total += line.price_subtotal
    #     if self.sale_update_id:
    #         self.price_unit = recurring_total

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s %s" % (record.service_id or "", record.name)))
        return result

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        subs_ids = []
        if name:
            subs_ids = self._search(
                ["|", ("name", "=", name), ("service_id", "=", name)] + args,
                limit=limit,
                access_rights_uid=name_get_uid,
            )
        if not subs_ids:
            subs_ids = self._search(
                ["|", ("name", operator, name), ("service_id", operator, name)] + args,
                limit=limit,
                access_rights_uid=name_get_uid,
            )
        return self.browse(subs_ids).name_get()


class SaleSubscriptionStage(models.Model):
    _inherit = 'sale.subscription.stage'

    type_id = fields.Many2one(
        comodel_name="project.type",
        string="Tipo",
        copy=False,
        domain="[('project_ok', '=', True)]",
    )
