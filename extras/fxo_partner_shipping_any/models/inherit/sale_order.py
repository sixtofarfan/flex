from odoo import models, fields, api
from odoo.exceptions import ValidationError, Warning
import re
from odoo.addons.fxo_partner_shipping_any.tools import domains as partner_domains
    
    
class InheritSaleOrder(models.Model):
    _inherit = ["sale.order"]
    
    # @api.onchange('partner_id')
    # def _onchange_partner_shipping_id(self):
    #     if self.partner_id:
    #         res = {}
    #         domain = partner_domains.domain_shipping_id(self)
    #         res.update(domain)
    #         return res
    
    """
    Comentario: Se debe revisar un poco mas a detalle por que se despues de 
    que se ejecuta el partner adhiere el id al shipping_id
    """
    @api.onchange('partner_shipping_id')
    def _onchange_partner_shipping_ids(self):
        res = {}
        domain = partner_domains.domain_shipping_id(self)
        res.update(domain)
        return res