from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class detraction_create_file(models.Model):
    _name = 'detraction.create.file'
    name = fields.Char(string='Lot Number', default=(lambda self: _('New')))
    txt_file = fields.Binary(string='Text file SUNAT')
    file_name = fields.Char('File Name')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=(lambda self: self.env.user.company_id.currency_id))
    total_form = fields.Monetary(string='Total Amount', required=True)
    payment_ids = fields.Many2many('account.payment', string='Payments')
    state = fields.Selection(string='State', selection=[('0', 'Unpaid'), ('1', 'Paid')], default='0')

    @api.onchange('payment_ids')
    def onchange_payment_ids(self):
        self.total_form = 0
        for payment in self.payment_ids:
            self.total_form += payment.account_amount

    def pay_detractions(self):
        for payment in self.payment_ids:
            payment.detraction_state = '1'

        self.state = '1'

    def unpay_detractions(self):
        for payment in self.payment_ids:
            payment.detraction_state = '0'

        self.state = '0'

    def unlink(self):
        if self.state == '1':
            raise ValidationError(_('You can not delete a lot in paid state.'))
        else:
            return super(detraction_create_file, self).unlink()

    def update_account_amount_list(self):
        vals = {}
        vals.update({'id':self.id,  'active_ids':self.payment_ids.ids,  'name':self.name,  'update':True})
        create_file = self.env['detraction.create.file.wizard']
        create_file.create_file(vals)