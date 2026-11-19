# -*- coding: utf-8 -*-

from datetime import timedelta

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderFactibility(models.Model):
    _name = "sale.order.line.factibility"
    _description = "Factibility Order Lines"

    name = fields.Char(string="Name")

    def _set_country_id(self):
        return self.env["res.country"].browse([173])

    def _set_expiration_date(self):
        parameter = self.env["fxo.sale.main.parameter"].search([("name", "=", self.env.company.id)])
        date = fields.Date.today()
        if parameter.expiration_type == "Days":
            date = date + timedelta(days=parameter.expiration)
        elif parameter.expiration_type == "months":
            date = date + relativedelta(months=parameter.expiration)
        elif parameter.expiration_type == "year":
            date = date + relativedelta(years=parameter.expiration)

        return date

    country_id = fields.Many2one("res.country", string="Pais", default=_set_country_id)
    state_id = fields.Many2one("res.country.state", string="Departamento")
    province_id = fields.Many2one("res.country.state", string="Provincia")
    district_id = fields.Many2one("res.country.state", string="Distrito")
    origin_sale_order_id = fields.Many2one("sale.order", "Sale Order Origen")

    order_id = fields.Many2one(comodel_name="sale.order", string="Order")
    line = fields.Many2one(comodel_name="sale.order.line", string="Order Line")
    order_line_ids = fields.One2many("sale.order.line", "factibility_id", string="Lineas de Cotizacion")
    order_line_count = fields.Integer(compute="_compute_order_line_count")

    def _compute_order_line_count(self):
        for record in self:
            record.order_line_count = len(self.order_line_ids)

    factibility_date = fields.Date(string="Date", default=fields.Date.today())
    expiration_date = fields.Date(string="Expiration Date", default=_set_expiration_date)
    factibility_type = fields.Selection(
        [
            ("temporary", "Temporal"),
            ("definitive", "Definitivo"),
        ],
        string="Tipo de Factibilidad",
        default="temporary",
    )
    type_via = fields.Many2one(comodel_name="einvoice.catalog.04", string="Tipo de Via")
    name_via = fields.Char(string="Nombre Via")
    number_via = fields.Selection(
        [
            ("nro", "NRO"),
            ("mz", "MZ"),
            ("km", "KM"),
        ],
        string="Tipo Numero Via",
    )
    number_new = fields.Char(string="Numero")
    property_type = fields.Selection(
        string="Tipo de Inmueble",
        selection=[
            ("Edificio", "Edificio"),
            ("Residencia", "Residencia"),
            ("Quinta", "Quinta"),
            ("Casa", "Casa"),
            ("Otro", "Otro"),
        ],
    )

    type_cable = fields.Selection(
        string="Tipo de Cablea",
        selection=[
            ("Aereo", "Aereo"),
            ("Canalizado", "Canalizado"),
            ("Postes", "Postes"),
        ],
    )

    currency_id = fields.Many2one(
        "res.currency", string="Moneda", default=lambda self: self.env.company.currency_id.id
    )

    property_name = fields.Char(string="Nombre de Inmueble")
    floor = fields.Char(string="Piso")
    local = fields.Char(string="Local / Apartamento")
    apple = fields.Char(string="Manzana")
    lot = fields.Char(string="Lote")
    type_zone = fields.Many2one(comodel_name="einvoice.catalog.03", string="Tipo de Zona")
    name_zone = fields.Char(string="Nombre de Zona")
    street = fields.Text(string="Direccion")

    footage = fields.Float(string="Metraje")

    spliter_1_latitude = fields.Float(string="Longitud de Spliter 1", digits=(16, 5))
    spliter_1_longitude = fields.Float(string="Latitud de Spliter 1", digits=(16, 5))
    spliter_1_kmz = fields.Binary(string="KMZ")

    spliter_2_latitude = fields.Float(string="Longitud de Spliter 2", digits=(16, 5))
    spliter_2_longitude = fields.Float(string="Latitud de Spliter 2", digits=(16, 5))
    spliter_2_kmz = fields.Binary(string="KMZ")

    install_cost_temp = fields.Float(string="Costo de Instalacion")
    install_cost_def = fields.Float(string="Costo de Instalacion")

    install_cost = fields.Float(string="Costo de Instalacion")

    duration_type = fields.Selection(
        string="Tiempo de  (Dias/Mes/Años) ", selection=[("Days", "Days"), ("months", "Months"), ("year", "Year")]
    )
    install_duration = fields.Float(string="Duración de Instalación")
    user_id = fields.Many2one(comodel_name="res.users", string="Tecnico de Instalacion")

    state = fields.Selection(
        string="State",
        selection=[("draft", "Draft"), ("open", "Open"), ("done", "Done"), ("close", "close"), ("cancel", "cancel")],
        default="draft",
    )

    comment = fields.Text(string="Comentarios")
    company_id = fields.Many2one('res.company', 'Compañía', index=True,
                                 default=lambda self: self.env.company.id, readonly=True)
    product_id = fields.Many2one('product.product', 'Servicio')
    partner_latitude = fields.Float(string='Geo Latitude',
                                    digits=(16, 8), compute='_compute_geolocalization')
    partner_longitude = fields.Float(string='Geo Longitude', digits=(16, 8),
                                     compute='_compute_geolocalization'
                                     )

    @api.depends('origin_sale_order_id')
    def _compute_geolocalization(self):
        for rec in self:
            line = rec.origin_sale_order_id.order_line.filtered(lambda l: l.product_id.id == rec.product_id.id)
            if line:
                rec.partner_latitude = line[0].partner_street_destination.partner_latitude
                rec.partner_longitude = line[0].partner_street_destination.partner_longitude
            else:
                rec.partner_latitude = None
                rec.partner_longitude = None

    @api.onchange("factibility_type")
    def get_install_cost(self):
        Line = self.env["sale.order.line"].search([("factibility_id", "=", self.id)])
        Product = Line.product_id if Line else None
        if (
                self.install_cost_temp >= self.install_cost_def
                and self.origin_sale_order_id.state in ["draft", "sent"]
                and Product.bool_is_factibility
        ):
            self.install_cost = self.install_cost_temp
        elif (
                self.install_cost_temp <= self.install_cost_def
                and self.origin_sale_order_id.state in ["draft", "sent"]
                and Product.bool_is_factibility
        ):
            self.install_cost = self.install_cost_def

    def get_order_lines(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order.line",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [["id", "in", self.order_line_ids.ids]],
            "name": "Lineas de Cotizacion",
        }

    @api.model
    def create(self, vals):
        t = super(SaleOrderFactibility, self).create(vals)
        print("create_install", t.install_cost)
        t.name = self.env["ir.sequence"].next_by_code("sale.order.line.factibility")
        t.set_street_new()
        t.install_cost_def = t.install_cost
        t.install_cost_temp = t.install_cost
        print("create_install2", t.install_cost)
        return t

    def unlink(self):
        for item in self:
            if item.state in ["open", "done", "close", "cancel"]:
                raise UserError(
                    _("You cannot delete a document that is in %s state.")
                    % _(
                        item.state,
                    )
                )
        return super(SaleOrderFactibility, self).unlink()

    def set_open(self):
        cant = self.env["sale.order.line.factibility"].search(
            [("product_id", "=", self.product_id.id), ("street", "=", self.street), ("state", "=", "open")])
        if len(cant) > 0:
            raise UserError(_("No puede haber dos factibilidad  en estado Abierto en la misma direccion"))
        self.state = "open"
        Study = self.env["sale.order.line.qty_street"].search([("factibility_id", "=", self.id)])
        if Study:
            Study.install_cost = self.install_cost

    def set_done(self):
        self.state = "done"

    def set_close(self):
        self.state = "close"

    def set_cancel(self):
        self.state = "cancel"

    def set_draft(self):
        self.state = "draft"
        Study = self.env["sale.order.line.qty_street"].search([("factibility_id", "=", self.id)])
        if Study:
            Study.install_cost = 0

    @api.onchange("factibility_date")
    def onchange_factibility_date(self):
        if self.factibility_date:
            parameter = self.env["fxo.sale.main.parameter"].search([("name", "=", self.env.company.id)])
            date = self.factibility_date
            if parameter.expiration_type == "Days":
                self.expiration_date = date + timedelta(days=parameter.expiration)
            elif parameter.expiration_type == "months":
                self.expiration_date = date + relativedelta(months=parameter.expiration)
            elif parameter.expiration_type == "year":
                self.expiration_date = date + relativedelta(years=parameter.expiration)

    @api.onchange(
        "type_via",
        "state_id",
        "province_id",
        "district_id",
        "number_via",
        "name_via",
        "property_type",
        "property_name",
        "floor",
        "local",
        "apple",
        "lot",
        "type_zone",
        "name_zone",
        "number_new",
    )
    def set_street_new(self):
        self.street = ""
        for item in self.type_via:
            self.street += str(item.descriptio) + " "
        if self.name_via:
            self.name_via = self.name_via.upper()
            self.street += self.name_via.upper() + " "
        if self.number_via:
            self.street += dict(self._fields["number_via"].selection).get(self.number_via) + " "
        if self.number_new:
            self.street += str(self.number_new) + " "
        if self.property_type:
            self.street += self.property_type + " "
        if self.property_name:
            self.street += self.property_name + " "
        if self.floor:
            self.street += self.floor + " "
        if self.apple:
            self.street += self.apple + " "
        if self.lot:
            self.street += self.lot + " "
        for item in self.type_zone:
            self.street += str(item.name) + " "
        if self.name_zone:
            self.street += self.name_zone + " "
        if self.state_id.id:
            self.street += self.state_id.name + " "
        if self.province_id.id:
            self.street += self.province_id.name + " "
        if self.district_id.id:
            self.street += self.district_id.name + " "

    def get_data(self):
        t = {
            "type": "ir.actions.act_window",
            "name": "Factibilidad",
            "res_model": "sale.order.line.factibility",
            "view_mode": "tree,form",
            "context": {"search_default_my_factibility": 1},
            "views": [
                [self.env.ref("fxo_feasibility.view_sale_order_line_factibility_tree").id, "tree"],
                [self.env.ref("fxo_feasibility.view_sale_order_line_factibility_from").id, "form"],
            ],
        }
        if (
                self.env.uid in self.env.ref("fxo_feasibility.group_factibility_manager").users.ids
                or self.env.uid in self.env.ref("fxo_feasibility.group_factibility_administrator").users.ids
        ):
            pass
        else:
            t["domain"] = [("user_id", "=", self.env.uid)]
        return t
