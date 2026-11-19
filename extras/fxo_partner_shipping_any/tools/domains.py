# -*- coding: utf-8 -*-


def domain_shipping_id(self):
    """
    Desarrollador: Jhosmel Patricio
    Cambios: Obtener todas las direcciones
    """
    res = {
        "domain": {}
    }
    default_domain = []

    if self.partner_id.partner_shipping_id:
        default_domain = [("id", "=", self.partner_id.partner_shipping_id.id)]
        self.sudo().write({'partner_shipping_id': self.partner_id.partner_shipping_id.id})

    else:
        default_domain = ["|", ("parent_id", "=", self.partner_id.id),("id", "=", self.partner_id.id)]

    res["domain"] = {
            "partner_shipping_id": default_domain
        }

    return res