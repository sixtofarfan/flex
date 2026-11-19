# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, date, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class ProductionLot(models.Model):
    _inherit = "stock.production.lot"

    manufacturing_date = fields.Date(string='Manufacturing Date',help='Product lot manufacturing date..')

