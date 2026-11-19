# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class VstkardexFisico(models.Model):
    _name = "vst.kardex.fisico"
    _description = "Sales by Channel (All in One)"
    _auto = False

    name = fields.Char('Order Reference', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)

    # def _so(self):
    #     so_str = """
    #             SELECT sol.id AS id,
    #                 so.name AS name,
    #                 so.partner_id AS partner_id,
    #                 sol.product_id AS product_id,
    #                 pro.product_tmpl_id AS product_tmpl_id,
    #                 so.date_order AS date_order,
    #                 so.user_id AS user_id,
    #                 pt.categ_id AS categ_id,
    #                 so.company_id AS company_id,
    #                 sol.price_total / CASE COALESCE(so.currency_rate, 0) WHEN 0 THEN 1.0 ELSE so.currency_rate END AS price_total,
    #                 so.pricelist_id AS pricelist_id,
    #                 rp.country_id AS country_id,
    #                 sol.price_subtotal / CASE COALESCE(so.currency_rate, 0) WHEN 0 THEN 1.0 ELSE so.currency_rate END AS price_subtotal,
    #                 (sol.product_uom_qty / u.factor * u2.factor) as product_qty,
    #                 so.analytic_account_id AS analytic_account_id,
    #                 so.team_id AS team_id

    #         FROM sale_order_line sol
    #                 JOIN sale_order so ON (sol.order_id = so.id)
    #                 LEFT JOIN product_product pro ON (sol.product_id = pro.id)
    #                 JOIN res_partner rp ON (so.partner_id = rp.id)
    #                 LEFT JOIN product_template pt ON (pro.product_tmpl_id = pt.id)
    #                 LEFT JOIN product_pricelist pp ON (so.pricelist_id = pp.id)
    #                 LEFT JOIN uom_uom u on (u.id=sol.product_uom)
    #                 LEFT JOIN uom_uom u2 on (u2.id=pt.uom_id)
    #         WHERE so.state in ('sale','done')
    #     """
    #     return so_str

    # def _from(self):
    #     return """(%s)""" % (self._so())

    def get_main_request(self):
        request = """
            CREATE OR REPLACE VIEW %s AS 
            SELECT stock_move.product_uom,
            --    stock_move.move_dest_id,
                    CASE
                        WHEN original.id <> uomt.id THEN round((stock_move.price_unit * original.factor::double precision / uomt.factor::double precision)::numeric, 6)::double precision
                        ELSE stock_move.price_unit
                    END AS price_unit,
                    CASE
                        WHEN uom_uom.id <> uomt.id THEN round((stock_move.product_uom_qty::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
                        ELSE stock_move.product_uom_qty
                    END AS product_qty,
                stock_move.location_id,
                stock_move.location_dest_id,
                stock_move.picking_type_id,
                stock_move.product_id,
                stock_move.picking_id,
            --  COALESCE(stock_picking.invoice_id, 0) AS invoice_id,
            --      CASE
            --          WHEN stock_picking.es_fecha_kardex THEN stock_picking.fecha_kardex::timestamp without time zone
            --          ELSE
            --          CASE
            --              WHEN ai.date_invoice IS NULL THEN stock_picking.fecha_kardex::timestamp without time zone
            --              ELSE ai.date_invoice::timestamp without time zone
            --           END
            --       END AS date,
                stock_picking.name,
                stock_picking.partner_id,
            --  einvoice_catalog_12.code AS guia,
            --  stock_move.analitic_id,
                stock_move.id,
                product_product.default_code,
                stock_move.state AS estado
            FROM stock_move
                JOIN uom_uom ON stock_move.product_uom = uom_uom.id
                JOIN stock_picking ON stock_move.picking_id = stock_picking.id
                JOIN stock_picking_type ON stock_picking.picking_type_id = stock_picking_type.id
                JOIN stock_location sl ON sl.id = stock_move.location_dest_id
                JOIN product_product ON stock_move.product_id = product_product.id
                JOIN product_template ON product_product.product_tmpl_id = product_template.id
            -- LEFT JOIN einvoice_catalog_12 ON stock_picking.einvoice_12 = einvoice_catalog_12.id
                JOIN uom_uom uomt ON uomt.id = product_template.uom_id
                JOIN uom_uom original ON original.id = product_template.uom_id
            --  LEFT JOIN account_move ai ON ai.id = stock_picking.invoice_id
            -- WHERE COALESCE(stock_picking.canceled_guide, false) = false AND (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL AND stock_move.production_id IS NULL AND stock_move.raw_material_production_id IS NULL AND "substring"(COALESCE(stock_picking.origin, '--'::character varying)::text, 1, 3) <> 'MO/'::text
            WHERE  (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL AND stock_move.production_id IS NULL AND stock_move.raw_material_production_id IS NULL AND "substring"(COALESCE(stock_picking.origin, '--'::character varying)::text, 1, 3) <> 'MO/'::text

            -- UNION ALL
            --  SELECT sm.product_uom,
            --     sm.move_dest_id,
            --     sm.price_unit,
            --         CASE
            --             WHEN uom_uom.id <> uomt.id THEN round((sm.product_uom_qty::double precision * uomt.factor::double precision / product_uom.factor::double precision)::numeric, 6)
            --             ELSE sm.product_uom_qty
            --         END AS product_qty,
            --     sm.location_id,
            --     sm.location_dest_id,
            --     mrp.picking_type_id,
            --     sm.product_id,
            --     sm.picking_id,
            --     sm.invoice_id,
            --     mrp.kardex_date::timestamp without time zone AS date,
            --     mrp.name,
            --     sm.partner_id,
            --     '99'::character varying(4) AS guia,
            --     sm.analitic_id,
            --     sm.id,
            --     product_product.default_code,
            --     sm.state AS estado
            --    FROM vst_mrp_moves sm
            --      JOIN product_uom ON sm.product_uom = product_uom.id
            --      JOIN mrp_production mrp ON sm.mrp_id = mrp.id
            --      JOIN stock_picking_type ON mrp.picking_type_id = stock_picking_type.id
            --      JOIN stock_location sl ON sl.id = sm.location_dest_id
            --      JOIN stock_location slo ON slo.id = sm.location_id
            --      JOIN product_product ON sm.product_id = product_product.id
            --      JOIN product_template ON product_product.product_tmpl_id = product_template.id
            --      JOIN product_uom uomt ON uomt.id =
            --         CASE
            --             WHEN product_template.unidad_kardex IS NOT NULL THEN product_template.unidad_kardex
            --             ELSE product_template.uom_id
            --         END
            --      JOIN product_uom original ON original.id = product_template.uom_id
            --   WHERE sm.state::text = 'done'::text AND product_template.type::text = 'product'::text AND sm.mrp_id IS NOT NULL;""" % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
