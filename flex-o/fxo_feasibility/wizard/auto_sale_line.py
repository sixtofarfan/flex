from odoo import models, fields, _


class Auto_Sale_Line(models.TransientModel):
    _name = "auto.sale.line"

    product_id = fields.Many2one("product.product", "Producto")
    product_uom_qty = fields.Float("Cantidad")
    item_origin = fields.Char("IT/Referencia", default="0")
    partner_id = fields.Many2one("res.partner")
    contact_ids = fields.Many2many("res.partner", "autosaleline_partner_rel", "auto_id", "partner_id", "Contactos")
    partner_order_id = fields.Many2one("res.partner")

    def create_lines(self):
        for i in self:
            pedido = self.env["sale.order"].browse(self.env.context["active_id"])
            ultima_seq = 1
            for elem in pedido.order_line:
                if ultima_seq < elem.sequence:
                    ultima_seq = elem.sequence

            ultima_seq += 1

            for contact in i.contact_ids:
                data = {
                    "product_id": i.product_id.id,
                    "product_uom_qty1": i.product_uom_qty,
                    "product_uom1": i.product_id.uom_id.id,
                    "partner_street_destination": contact.id,
                    "product_uom_qty": i.product_uom_qty,
                    "order_id": pedido.id,
                    "item_origin": self.item_origin,
                    "type_item": "Direccion",
                    "sequence": ultima_seq,
                }
                linea = self.env["sale.order.line"].create(data)
                if linea.product_id.bool_is_factibility or linea.product_id.bool_is_study_economic:
                    linea.action_qty_street()
                ultima_seq += 1
