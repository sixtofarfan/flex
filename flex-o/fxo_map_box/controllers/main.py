import logging
import werkzeug

from odoo import http, _

from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


_logger = logging.getLogger(__name__)

class WebsiteSale(WebsiteSale):

    def values_postprocess(self, order, mode, values, errors, error_msg):
        action = super(WebsiteSale, self).values_postprocess(order, mode, values, errors, error_msg)
        action[0]['longitud'] = values['longitud']
        action[0]['latitud']  = values['latitud']
        return action
