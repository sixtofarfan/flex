from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
import re

class res_partner_bank(models.Model):
    _inherit = 'res.partner.bank'
    
    type_of_account = fields.Selection(string='Type of account', selection=[
     ('0', 'Corriente'),
     ('1', 'Ahorros'),
     ('2', 'Detracciones'),
     ('3', 'CCI'),
     ('4', 'Otros')])

    @api.onchange('type_of_account', 'acc_number')
    def onchange_type_of_account(self):
        if self.type_of_account == '2':
            if self.acc_number:
                if len(re.sub('[^0-9]', '', self.acc_number)) != 11:
                    raise ValidationError(_('The number of digits for a detraction account must be 11.'))
        if self.type_of_account == '3':
            if self.acc_number:
                if len(re.sub('[^0-9]', '', self.acc_number)) != 20:
                    raise ValidationError(_('The number of digits for a CCI account must be 20.'))