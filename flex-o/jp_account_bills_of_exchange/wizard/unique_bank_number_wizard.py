# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class BankNumberWizard(models.TransientModel):
    _name = "bank.number.wizard"
    _description = "Unique Bank Number Wizard"

    first_number = fields.Char(string='First number')

    def update_numbers(self):
        active_ids = self.env.context.get('active_ids', [])
        bills = self.env['account.bill'].search([('id','in',active_ids)])
        first_number = int(self.first_number)
        if bills:
            first_bill = bills[0]
            if any(x.bill_form_id != first_bill.bill_form_id for x in bills):
                raise UserError(_("You can only update bank numbers of the bills from the same form."))
            if any(x.state_of_bill not in ['collection','discount','guarantee','disbursed'] for x in bills):
                raise UserError(_("You can only update bank numbers of the bills that are in the bank."))
        for bill in bills:
            bill.bank_number = first_number
            first_number += 1