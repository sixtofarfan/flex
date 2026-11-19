from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    det_percent = fields.Float(string='Detraction percent', digits=(16, 2), default=12.0)
    type_operation = fields.Many2one('type.operation', string='Type of Operation')
    type_good_service = fields.Many2one('good.service', string='Goods and Services')
    det_percent_by = fields.Selection([
        ('1', 'By Product'),
        ('2', 'By Partner'),
        ('3', 'Fixed')
    ], string='Show detraction fields', related='company_id.det_percent_by')
