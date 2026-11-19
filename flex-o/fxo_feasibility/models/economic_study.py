# -*- coding: utf-8 -*-

import math
import subprocess
import sys
from statistics import mean

from odoo import tools
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round
from odoo.tools.date_utils import subtract


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


try:
    import numpy_financial as npf
except:
    install("numpy_financial")


class SaleOrderQtyStreet(models.Model):
    _name = "sale.order.line.qty_street"
    _description = "Economic Study"

    id = fields.Integer(string="ID", states={'posted': [('readonly', True)]})

    tc = fields.Float("Tipo de Cambio", digits=(12, 3), compute="get_tipo_cambio")
    name = fields.Many2one(comodel_name="sale.order.line", string="Order Line", states={'posted': [('readonly', True)]})
    currency_order_id = fields.Many2one("res.currency", related="name.currency_id")
    # FACTIBILIDAD
    factibility_id = fields.Many2one(comodel_name="sale.order.line.factibility", string="Factibility",
                                     states={'posted': [('readonly', True)]})
    recurring_interval = fields.Integer(string="Plazo de Contrato", default=24, readonly=True)
    partner_street_destination = fields.Char(
        related="name.partner_street_destination.street", string="Direccion Destino"
    )
    partner_street_destination_header = fields.Char(
        related="name.partner_street_destination_header.street", string="Direccion Cabecera"
    )

    feasibility_installation_cost = fields.Float(string="Costo de instalacion", related="factibility_id.install_cost")
    feasibility_installation_cost_pen = fields.Float(
        "Costo de instalacion", compute="_compute_feasibility_installation_cost_pen", store=True, readonly=True
    )
    feasibility_currency_id = fields.Many2one(related="factibility_id.currency_id")
    # Costo de producto
    product_id = fields.Many2one("product.product", related="name.product_id", string="Product")
    product_price = fields.Float(string="Price", compute="_compute_product", store=True, readonly=True)
    product_quantity = fields.Float(string="Quantity", related="name.product_uom_qty1")
    product_currency = fields.Many2one(
        comodel_name="res.currency", compute="_compute_product", store=True, readonly=True
    )
    product_uom = fields.Many2one(comodel_name="uom.uom", related="name.product_uom1")
    product_price_total = fields.Float("Costo Total", compute="_compute_product", store=True, readonly=True)

    template_id = fields.Many2one(comodel_name="fxo_feasibility.params", string="Template",
                                  states={'posted': [('readonly', True)]})
    is_migration_or_adenda = fields.Boolean(string='Traslado o Adenda', readonly=True)

    # resumen
    # Total Ingresos
    total_incomes = fields.Float("Total Incomes", compute="_compute_total_incomes", store=True, readonly=True)
    # Total Renta mensual
    incomes_monthly_rent = fields.Float("Incomes Monthly Rent", store=True, readonly=False,
                                        states={'posted': [('readonly', True)]})
    total_incomes_monthly_rent = fields.Float(
        "Total Incomes Monthly Rent", compute="_compute_total_incomes", store=True, readonly=True
    )
    # Total egresos
    total_expenses = fields.Float("Total Expenses", compute="_compute_total_expenses", store=True, readonly=True)
    # Utilidad bruta
    gross_profit = fields.Float("Gross Profit", compute="_compute_total_expenses", store=True, readonly=True)
    # Margen operativo (porcentaje de utilidad bruta)
    gross_profit_percentage = fields.Float("Gross Profit Percentage", digits=(6, 8),
                                           states={'posted': [('readonly', True)]})
    gross_with_additional_profit_percentage = fields.Float(
        "Margen Operativo con Pago Unico",
        compute="_compute_gross_with_additional_profit_percentage",
        store=True,
        readonly=True,
    )

    net_flow = fields.Float(string="Flujo Neto", compute="_compute_cash_flow", store=True, readonly=True)
    net_flow_total = fields.Float(string="Flujo Neto Total", compute="_compute_cash_flow", store=True, readonly=True)
    pay_back = fields.Float(string="Pay Back / ROI", compute="_compute_cash_flow", store=True, readonly=True)
    tir = fields.Float(string="TIR", compute="_compute_cash_flow", store=True, readonly=True)
    prevent_onchange = fields.Boolean(default=False, states={'posted': [('readonly', True)]})

    state = fields.Selection(
        string="Status",
        selection=[("draft", "Draft"), ("posted", "Posted")],
        default="draft",
        copy=False,
        readonly=False,
        required=True,
    )
    incomes = fields.One2many(
        comodel_name="economic_study.move",
        inverse_name="economic_study_incomes_id",
        string="Incomes",
        ondelete="cascade", states={'posted': [('readonly', True)]}

    )
    expenses = fields.One2many(
        comodel_name="economic_study.move",
        inverse_name="economic_study_expenses_id",
        string="Expenses",
        ondelete="cascade", states={'posted': [('readonly', True)]}
    )

    balance = fields.One2many(
        comodel_name="economic_study.move.balance", inverse_name="economic_study_id", string="Balance"
    )
    company_id = fields.Many2one('res.company', 'Compañía', index=True, default=lambda self: self.env.company.id,
                                 states={'posted': [('readonly', True)]})
    pricelist_id = fields.Many2one('product.pricelist', string="Tarifa", readonly=True)
    state_id = fields.Many2one(related="name.partner_street_destination.state_id", string='Estado')
    country_id = fields.Many2one(related="name.partner_street_destination.country_id", string='País')
    province_id = fields.Many2one(related="name.partner_street_destination.province_id", string='Provincia')
    district_id = fields.Many2one(related="name.partner_street_destination.district_id", string='Distrito')

    def open_pivot_view(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Economic Study Balance Report",
            "res_model": "economic_study.move.balance",
            "domain": [("economic_study_id", "=", self.id)],
            "view_mode": "pivot",
            "context": {},
        }

    @api.depends("product_id.fxo_cost_price", "product_id.fxo_cost_price_currency", "product_quantity")
    def _compute_product(self):
        for record in self:
            record.update(
                {
                    "product_price": record.product_id.fxo_cost_price,
                    "product_currency": record.product_id.fxo_cost_price_currency,
                    "product_price_total": record.product_quantity * record.product_id.fxo_cost_price,
                }
            )

    @api.depends("feasibility_installation_cost", "feasibility_currency_id")
    def _compute_feasibility_installation_cost_pen(self):
        for record in self:
            record.update(
                {
                    "feasibility_installation_cost_pen": record._compute_price(
                        record.feasibility_installation_cost, record.feasibility_currency_id
                    )
                }
            )

    @api.depends("incomes.price_total")
    def _compute_total_incomes(self):
        for record in self:
            total_incomes = total_incomes_monthly_rent = 0.0
            for line in record.incomes:
                total_incomes += line.price_total
                if not line.additional_profit:
                    total_incomes_monthly_rent += line.price_total
            record.update(
                {
                    "total_incomes": total_incomes,
                    "total_incomes_monthly_rent": total_incomes_monthly_rent,
                }
            )

    @api.onchange("incomes_monthly_rent")
    def _onchange_incomes_monthly_rent(self):
        for record in self:
            # if record.prevent_onchange:
            #    record.write({"prevent_onchange": False})
            # else:
            total_incomes = total_expenses = 0.0
            for line in record.expenses:
                total_expenses += line.price_total

            for line in record.incomes:
                if line.name == "Renta mensual":
                    line.write({"price_unit": record.incomes_monthly_rent})

                total_incomes += line.price_total

            gross_profit = total_incomes - total_expenses
            gross_profit_percentage = (gross_profit / total_incomes) * 100 if total_incomes > 0 else 0

            record.write({"prevent_onchange": True, "gross_profit_percentage": gross_profit_percentage})

    @api.depends("expenses.price_total", "incomes.price_total", "gross_profit_percentage")
    def _compute_total_expenses(self):
        for record in self:
            if record.prevent_onchange:
                record.update({"prevent_onchange": False})
            else:
                total_incomes = total_expenses = 0.0
                for line in record.expenses:
                    total_expenses += line.price_total
                porc = 100 - record.gross_profit_percentage if 100 - record.gross_profit_percentage > 0 else 1
                gross_profit = (total_expenses * record.gross_profit_percentage) / porc

                incomes_monthly_rent = (
                    (total_expenses + gross_profit) / record.recurring_interval if record.recurring_interval > 0 else 0
                )

                for line in record.incomes:
                    if line.name == "Renta mensual":
                        line.update({"price_unit": incomes_monthly_rent})

                    total_incomes += line.price_total

                record.update(
                    {
                        "prevent_onchange": True if incomes_monthly_rent != record.incomes_monthly_rent else False,
                        "incomes_monthly_rent": incomes_monthly_rent,
                        "total_expenses": total_expenses,
                        "gross_profit": gross_profit,
                        "gross_with_additional_profit_percentage": (total_incomes - total_expenses) / total_incomes
                        if total_incomes > 0
                        else 0,
                    }
                )

    @api.onchange("recurring_interval")
    def _onchange_recurring_interval(self):
        for i in self:
            for line in i.incomes.filtered(lambda l: not l.additional_profit):
                line.quotes = i.recurring_interval

            for line in i.expenses.filtered(lambda l: not l.additional_profit):
                line.quotes = i.recurring_interval

    @api.depends("total_expenses", "gross_profit")
    def _compute_cash_flow(self):
        total_incomes = self._get_fee_incomes()
        total_expenses = self._get_fee_expenses()

        if total_incomes <= 0 or total_expenses <= 0:
            self.update({"net_flow": 0, "net_flow_total": 0, "pay_back": 0, "tir": 0})
            return

        monthly_rent = [total_incomes] * self.recurring_interval
        additional_profit = [
            ([line.price_total / line.quotes] * int(line.quotes))
            + ([0] * (self.recurring_interval - int(line.quotes)))
            for line in self.incomes.filtered(lambda l: l.additional_profit)
        ]
        in_totals = [sum(vals) for vals in zip(monthly_rent, *additional_profit)]

        monthly_egress = [total_expenses] * self.recurring_interval
        loss_profit = [
            ([line.price_total / line.quotes] * int(line.quotes))
            + ([0] * (self.recurring_interval - int(line.quotes)))
            for line in self.expenses.filtered(lambda l: l.additional_profit)
        ]
        out_totals = [sum(vals) for vals in zip(monthly_egress, *loss_profit)]

        # flujo neto
        _in_out_totals = [x - y for x, y in zip(monthly_rent, monthly_egress)]

        _net_flow = _in_out_totals[self.recurring_interval - 1]  # Renta mensual
        _net_flow_total = sum(_in_out_totals)

        _pays = [x - y for x, y in zip(in_totals, out_totals)]
        # _net_flow_total = sum(_pays)
        # _pay_back = sum([sum(vals) for vals in zip(*loss_profit)]) / mean(_pays)

        _total_balance = []

        for index, elem in enumerate(_pays):
            if index == 0:
                _total_balance.append(elem)
            else:
                _total_balance.append(_total_balance[index - 1] + elem)

        _pay_back = len(list(filter(lambda f: f <= 0, _total_balance)))

        parsed_flow = npf.irr(_total_balance)
        _tir = 0 if math.isnan(parsed_flow) else float_round(parsed_flow, 2)
        self.update({"net_flow": _net_flow, "net_flow_total": _net_flow_total, "pay_back": _pay_back, "tir": _tir})

    def _get_fee_incomes(self):
        try:
            filtered = self.incomes.filtered(lambda l: not l.additional_profit)
            total_incomes = 0
            for line in filtered:
                if line.quotes != self.recurring_interval:
                    line.quotes = self.recurring_interval
                total_incomes += (line.price_unit * line.quantity) * self.recurring_interval

            return total_incomes / self.recurring_interval
        except:
            return 0

    def _get_fee_expenses(self):
        try:
            filtered = self.expenses.filtered(lambda l: not l.additional_profit)
            total_expenses = 0
            for line in filtered:
                if line.quotes != self.recurring_interval:
                    line.quotes = self.recurring_interval
                total_expenses += (line.price_unit * line.quantity) * self.recurring_interval

            return total_expenses / self.recurring_interval
        except:
            return 0

    def action_draft(self):
        for record in self:
            if record.state == "posted":
                if record.name.order_id.state != 'draft':
                    raise UserError(
                        'No puede poner en Borrador el Estudio Económico de una Orden que no está en estado Cotización.')
                record.state = "draft"

    def action_post(self):
        for record in self:
            if record.state == "draft":

                posted = record.name.qty_streets.filtered(lambda l: l.state == "posted")
                if len(posted) >= 1:
                    raise UserError("Existe un estudio economico publicado, no puede publicar otro registro")

                record.name.product_uom_qty = record.name.product_uom_qty1
                record.name.price_unit = record.incomes_monthly_rent / record.name.product_uom_qty1
                # SFR1 renta mensua = al monto digitado.  (Tambien se soluciona actualizando decimales del % de rentabilidad a 8 digitos)
                # for line in record.incomes:
                #    if line.name == "Renta mensual":
                #        line.write({"price_unit": record.incomes_monthly_rent})

                record.state = "posted"
            else:
                raise UserError("El registro se encuentra publicado")

    # URO se modifico teniendo en cuenta el tipo de cambio configurado en parametros de factibilidad
    def get_tipo_cambio(self):
        for i in self:
            MainParameter = self.env['fxo.sale.main.parameter'].search([('name', '=', self.company_id.id)],
                                                                       limit=1)
            if MainParameter.use_tc:
                tc = MainParameter.tc
                if tc <= 0:
                    raise UserError('El tipo de cambio configurado en parametros de factibilidad debe ser mayor que 0.')
                else:
                    i.tc = tc
            else:
                moneda = self.env["res.currency.rate"].search(
                    [("currency_id.name", "=", "USD"), ("name", "=", i.name.order_id.date_order)]
                )
                if len(moneda) > 0:
                    i.tc = moneda[0].sale_type
                else:
                    i.tc = 1

    def _compute_price(self, price, currency):
        # i.name.order_id.pricelist_id.currency_id.name
        if currency:
            currency_name = currency.name
        else:
            currency_name = "USD"

        if self.currency_order_id.name == "PEN":
            if currency_name == "USD":
                price = price * self.tc

        if self.currency_order_id.name == "USD":
            if currency_name == "PEN":
                price = price / self.tc

        return price

    def refresh_moves(self):
        for i in self:
            i.get_pricelist_id_by_partner()
            if not i.pricelist_id:
                raise UserError(
                    u'No se puede realizar la operación, debido a que la tarifa no pueder ser nula, revise la configuración de la dirección en el cliente o si existe una tarifa configurada para esta dirección.')
            if not i.template_id:
                continue

            incomes = [(5, 0, 0)]
            expenses = [(5, 0, 0)]

            parameter = self.env["fxo.sale.main.parameter"].search([("name", "=", self.env.company.id)])
            product_cost_install = parameter.producto_costo_instalacion or i.name.product_id

            incomes.append(
                (
                    0,
                    0,
                    {
                        "product_id": i.name.product_id.id,
                        "name": "Renta mensual",
                        "quotes": i.recurring_interval,
                        "quantity": 1,
                        "price_unit": 0,
                        "additional_profit": False,
                    },
                )
            )
            for line in i.template_id.incomes:
                incomes.append(
                    (
                        0,
                        0,
                        {
                            "product_id": line.product_id.id,
                            "name": line.name,
                            "quotes": 1 if line.additional_profit else i.recurring_interval,
                            "quantity": line.quantity,
                            "price_unit": i._compute_price(
                                line.product_id.fxo_cost_price, line.product_id.fxo_cost_price_currency
                            ),
                            "additional_profit": line.additional_profit,
                        },
                    )
                )

            fixed_price = self.get_product_price(i.product_id, 1, i.name.partner_street_destination, i.name.order_id,
                                                 i.name.order_id.company_id, i.pricelist_id)
            expenses.append(
                # Agregando al gasto, la linea de Costo de servicio
                (
                    0,
                    0,
                    {
                        "product_id": i.name.product_id.id,
                        "name": "Costo de servicio",
                        "quotes": i.recurring_interval,
                        "quantity": i.name.product_uom_qty1,
                        "price_unit": fixed_price,
                        "additional_profit": False,
                    },
                )
            )
            expenses.append(
                # Agregando al gasto, la linea de servicio de instalación
                (
                    0,
                    0,
                    {
                        "product_id": product_cost_install.id,
                        "name": "Costo de instalacion",
                        "quotes": 1,
                        "quantity": 1,
                        "price_unit": i._compute_price(i.feasibility_installation_cost, i.feasibility_currency_id),
                        "additional_profit": True,
                    },
                )
            )
            for line in i.template_id.expenses:
                expenses.append(
                    (
                        0,
                        0,
                        {
                            "product_id": line.product_id.id,
                            "name": line.name,
                            "quotes": 1 if line.additional_profit else i.recurring_interval,
                            "quantity": i.name.product_uom_qty1 if line.quantity == 0 else line.quantity,
                            "price_unit": i._compute_price(
                                line.product_id.fxo_cost_price, line.product_id.fxo_cost_price_currency
                            ),
                            "additional_profit": line.additional_profit,
                        },
                    )
                )

            i.gross_profit_percentage = i.template_id.gross_profit_percent

            context = i.with_context(force_delete=True)
            context.incomes = incomes
            context.expenses = expenses

    # URO obteniendo la tarifa teniendo en cuenta la direccion del partner
    def get_pricelist_id_by_partner(self):
        pricelist = self.env['product.pricelist']
        pricelist_ids = pricelist.search([('company_id', 'in', [False, self.company_id.id]),
                                          ('currency_id', '=', self.currency_order_id.id),
                                          ('country_id', '=', self.country_id.id)])

        pricelist_return_state = False
        pricelist_return_province = False
        pricelist_return_district = False

        if len(pricelist_ids) > 0:
            pricelist_return_country = pricelist_ids[0]
            for pricelist_obj in pricelist_ids:
                pricelist_obj_state = pricelist_obj.state_id.filtered(
                    lambda p: p.country_id.id == self.country_id.id and p.id == self.state_id.id)
                if len(pricelist_obj_state) > 0:
                    pricelist_return_state = pricelist_obj
                pricelist_obj_province = pricelist_obj.province_ids.filtered(
                    lambda
                        p: p.country_id.id == self.country_id.id and p.state_id.id == self.state_id.id and p.id == self.province_id.id)
                if len(pricelist_obj_province) > 0:
                    pricelist_return_province = pricelist_obj
                pricelist_obj_district = pricelist_obj.district_ids.filtered(
                    lambda
                        p: p.country_id.id == self.country_id.id and p.state_id.id == self.state_id.id and p.province_id.id == self.province_id.id
                           and p.id == self.district_id.id)
                if len(pricelist_obj_district) > 0:
                    pricelist_return_district = pricelist_obj
            if pricelist_return_country and not pricelist_return_state and not pricelist_return_province and not pricelist_return_district:
                self.pricelist_id = pricelist_return_country.id
            elif pricelist_return_country and pricelist_return_state and not pricelist_return_province and not pricelist_return_district:
                self.pricelist_id = pricelist_return_state.id
            elif pricelist_return_country and pricelist_return_state and pricelist_return_province and not pricelist_return_district:
                self.pricelist_id = pricelist_return_province.id
            elif pricelist_return_country and pricelist_return_state and pricelist_return_province and pricelist_return_district:
                self.pricelist_id = pricelist_return_district.id
            else:
                self.pricelist_id = False
        else:
            self.pricelist_id = False

    def get_product_price(self, product, quantity, partner, order, company_id, pricelist):
        product_context = dict(self.env.context)
        product_context.setdefault('lang', partner.lang)
        product_context.update({
            'partner': partner,
            'quantity': quantity,
            'date': order.date_order,
            'pricelist': pricelist.id,
            'force_company': company_id})
        price_unit = pricelist.with_context(product_context).get_product_price(product, quantity, partner,
                                                                               date=False, uom_id=False)
        return price_unit

    def get_update_pricelist_wizard(self):
        return {
            'name': 'Actualizar Tarifa',
            'type': 'ir.actions.act_window',
            'res_model': 'fxo_feasibility.update_pricelist_wzd',
            'views': [(self.env.ref('fxo_feasibility.view_fxo_feasibility_update_pricelist_wzd').id, 'form')],
            'context': self._context,
            'target': 'new',
        }


class EconomicStudyMove(models.Model):
    _name = "economic_study.move"
    _description = "Economic Study: Incomes/Expenses"

    economic_study_incomes_id = fields.Many2one("sale.order.line.qty_street", ondelete="cascade")
    economic_study_expenses_id = fields.Many2one("sale.order.line.qty_street", ondelete="cascade")

    product_id = fields.Many2one("product.product", string="Product", required=True)
    name = fields.Text(string="Description", required=True)
    quotes = fields.Float(string="Quotes", default=1.0, digits="Payment terms")
    quantity = fields.Float(string="Quantity", default=1.0, digits="Quantity")
    price_unit = fields.Float(string="Unit Price", required=True, digits="Product Price")
    additional_profit = fields.Boolean(string="Additional Profit", default=True)
    price_total = fields.Float(compute="_compute_price_total", string="Subtotal", store=True)
    company_id = fields.Many2one('res.company', 'Compañía', index=True, default=lambda self: self.env.company.id)

    @api.depends("price_unit", "quotes", "quantity")
    def _compute_price_total(self):
        for line in self:
            line.price_total = (line.price_unit * line.quantity) * line.quotes

    @api.onchange("product_id")
    def onchange_product_id(self):
        product = self.product_id
        self.name = product.get_product_multiline_description_sale()
        self.price_unit = (self.economic_study_expenses_id or self.economic_study_incomes_id)._compute_price(
            product.fxo_cost_price, product.fxo_cost_price_currency
        )

    def unlink(self):
        for record in self:
            if (
                    record.name in ("Renta mensual", "Costo de servicio", "Costo de instalacion")
                    and record.env.context.get("force_delete", False) == False
            ):
                raise UserError("No puede eliminar el item principal")

        return super(EconomicStudyMove, self).unlink()


class EconomicStudyMoveBalance(models.Model):
    _name = "economic_study.move.balance"
    _description = "Economic Study Balance"
    _auto = False
    _order = "type asc, name asc"

    id = fields.Integer(string="ID")
    economic_study_id = fields.Many2one("sale.order.line.qty_street")
    type = fields.Char(string="Type")
    name = fields.Char(string="Concept")
    fee = fields.Float(string="Fee")
    quote = fields.Integer(string="Quote")
    company_id = fields.Many2one('res.company', 'Compañía', index=True,
                                 default=lambda self: self.env.company.id)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """CREATE or REPLACE VIEW %s as (%s)"""
            % (
                self._table,
                """
                        WITH balance AS (
                            SELECT COALESCE(economic_study_move.economic_study_incomes_id,
                                            economic_study_move.economic_study_expenses_id) AS economic_study_id,
                                '3.- RESUMEN'                                            AS type,
                                sum(
                                            CASE
                                                WHEN economic_study_move.economic_study_incomes_id IS NOT NULL
                                                    THEN (economic_study_move.quantity * economic_study_move.price_unit)::numeric(19, 2)
                                                ELSE 0::numeric
                                                END -
                                            CASE
                                                WHEN economic_study_move.economic_study_expenses_id IS NOT NULL
                                                    THEN (economic_study_move.quantity * economic_study_move.price_unit)::numeric(19, 2)
                                                ELSE 0::numeric
                                                END)                                     AS fee,
                                quote.quote,
                                economic_study_move.company_id
                            FROM economic_study_move,
                                LATERAL generate_series(1::numeric, economic_study_move.quotes) quote(quote)
                            GROUP BY quote.quote, economic_study_move.company_id,
                                    (COALESCE(economic_study_move.economic_study_incomes_id, economic_study_move.economic_study_expenses_id))
                        )
                        SELECT row_number() over (order by economic_study_id asc, type asc, name asc, quote asc, company_id asc) as id, *
                        FROM (
                                SELECT COALESCE(economic_study_move.economic_study_incomes_id,
                                                economic_study_move.economic_study_expenses_id)                        AS economic_study_id,
                                        CASE
                                            WHEN economic_study_move.economic_study_expenses_id IS NULL THEN '1.- INGRESOS'::text
                                            WHEN economic_study_move.economic_study_incomes_id IS NULL THEN '2.- EGRESOS'::text
                                            ELSE NULL::text
                                            END                                                                         AS type,
                                        CASE economic_study_move.name
                                            WHEN 'Renta mensual' THEN '1.1 Renta mensual'
                                            WHEN 'Costo de servicio' THEN '2.1 Costo de servicio'
                                            WHEN 'Costo de instalacion' THEN '2.2 Costo de instalacion'
                                            ELSE economic_study_move.name END                                           as name,
                                        (economic_study_move.quantity * economic_study_move.price_unit)::numeric(19, 2) AS fee,
                                        quote.quote,
                                        economic_study_move.company_id
                                FROM economic_study_move,
                                    LATERAL generate_series(1::numeric, economic_study_move.quotes) quote(quote)
                                UNION ALL
                                SELECT balance.economic_study_id,
                                        type,
                                        '3.1. Saldo en mes',
                                        balance.fee,
                                        balance.quote,
                                        balance.company_id
                                FROM balance
                                UNION ALL
                                SELECT balance.economic_study_id,
                                        type,
                                        '3.2. Saldo acumulado'::text                                           AS name,
                                        COALESCE(balance.fee + ((SELECT sum(x.fee) AS sum
                                                                FROM balance x
                                                                WHERE x.economic_study_id = balance.economic_study_id
                                                                and x.quote < balance.quote)), balance.fee) AS fee,
                                        balance.quote,
                                        balance.company_id
                                FROM balance
                            ) as report
                        """,
            )
        )
