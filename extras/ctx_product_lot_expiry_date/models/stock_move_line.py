# -*- coding: utf-8 -*-

import datetime
from odoo import models, fields, api


class stock_move_line(models.Model):
    _inherit = 'stock.move.line'

    code = fields.Selection(related="move_id.picking_code", string='Type of Operation')
    expiration_date = fields.Datetime(string='Expiration Date',
                                      help='This is the date on which the goods with this Serial Number may become dangerous and must not be consumed.')
    use_date = fields.Datetime(string='Best before Date',
                               help='This is the date on which the goods with this Serial Number start deteriorating, without being dangerous yet.')
    removal_date = fields.Datetime(string='Removal Date',
                                   help='This is the date on which the goods with this Serial Number should be removed from the stock.')
    alert_date = fields.Datetime(string='Alert Date',
                                 help='Date to determine the expired lots and serial numbers using the filter "Expiration Alerts".')
    manufacturing_date = fields.Date(string='Manufacturing Date',
                                     help='Product lot manufacturing date..')

    @api.model
    def create(self, vals):
        """
        Override stock move line create method to set the expiry dates in move line to lot expiry dates, otherwise set
        them to move line expiry date
        :param vals:
        :return:
        """
        ml = super(stock_move_line, self).create(vals)
        if ml and ml.lot_id:
            ml.use_date = ml.lot_id.use_date if ml.lot_id.use_date else ml.use_date
            ml.expiration_date = ml.lot_id.life_date if ml.lot_id.life_date else ml.expiration_date
            ml.removal_date = ml.lot_id.removal_date if ml.lot_id.removal_date else ml.removal_date
            ml.alert_date = ml.lot_id.alert_date if ml.lot_id.alert_date else ml.alert_date
            ml.manufacturing_date = ml.lot_id.manufacturing_date if ml.lot_id.manufacturing_date else ml.manufacturing_date
        return ml

    @api.onchange('lot_name', 'lot_id')
    def onchange_lot_name(self):
        """
        This method used to get the expiry dates if the lot_id changed in PO shipment picking with( use existing lot/sn)
        also in delivery and internal transfer picking
        :return:
        """
        if self.lot_id:
            self.use_date = self.lot_id.use_date
            self.expiration_date = self.lot_id.life_date
            self.removal_date = self.lot_id.removal_date
            self.alert_date = self.lot_id.alert_date
            self.manufacturing_date = self.lot_id.manufacturing_date


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for ml in self.move_line_ids:
            if ml.product_id.tracking != 'none':
                picking_type_id = ml.move_id.picking_type_id
                if picking_type_id:
                    # Check if the picking is incoming (Shipment) and use create lots is enabled
                    if picking_type_id.code == 'incoming' and picking_type_id.use_create_lots:
                        # Check if move lot is set
                        if ml.lot_id:
                            # Set all expiry dates of lot to  expiry dated in move line
                            ml.lot_id.use_date = ml.use_date if ml.use_date else ml.lot_id.use_date
                            ml.lot_id.life_date = ml.expiration_date if ml.expiration_date else ml.lot_id.life_date
                            ml.lot_id.removal_date = ml.removal_date if ml.removal_date else ml.lot_id.removal_date
                            ml.lot_id.alert_date = ml.alert_date if ml.alert_date else ml.lot_id.alert_date
                            ml.lot_id.manufacturing_date = ml.manufacturing_date if ml.manufacturing_date else ml.lot_id.manufacturing_date
                            mapped_fields = {
                                'use_date': 'use_time',
                                'removal_date': 'removal_time',
                                'alert_date': 'alert_time'
                            }
                            product = self.env['product.product'].browse(ml.product_id.id)
                            if product:
                                for field in mapped_fields:
                                    duration = getattr(product, mapped_fields[field])
                                    # If the expiry dates (Life, removal, alert) is not set in move line and best before
                                    # date is set then calculate the expiry dates (Life, removal, alert) as below:

                                    if not ml[field] and ml.expiration_date:
                                        date = fields.Date.from_string(ml.expiration_date) + datetime.timedelta(
                                            days=duration)
                                        # set value to date in production.lot
                                        ml.lot_id[field] = fields.Datetime.to_string(date)
        return res
