from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    vendor_landed_cost_id = fields.Many2one('stock.landed.cost', string='Stock Landed Cost', copy=False)
    expenses_landed_cost_id = fields.Many2one('stock.landed.cost', string='Stock Landed Cost', copy=False)
    # import_number_order = fields.Many2one('purchase.order', string='Import N°')
    import_number = fields.Char(string='Import N°', copy=False)
    transit_move_line_id = fields.Many2one('account.move.line', string='Transit move line')

    @api.onchange('import_number')
    def _onchange_import_number(self):
        for line in self.line_ids:
            line.import_number = self.import_number

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    vendor_entry_landed_cost_id = fields.Many2one('stock.landed.cost', string='Stock Landed Cost', copy=False)
    entry_landed_cost_id = fields.Many2one('stock.landed.cost', string='Stock Landed Cost', copy=False)
    import_number = fields.Char(string='Import N°', copy=False)
