from odoo import fields, models, _
from odoo.exceptions import UserError

class StockValuationLayer(models.Model):

    _inherit = 'stock.valuation.layer'

    def unlink(self):
        res = super(StockValuationLayer, self).unlink()
        if not self._context.get('force_delete'):
            raise UserError(_('You cannot delete an stock valuation layer'))
        return res