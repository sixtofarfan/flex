# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
 
class SplitInvoiceLine(models.TransientModel):
    _name = 'split.invoice.line'
    _description = 'Split Record Line'

    wizard_id = fields.Many2one("split.invoice.wizard")
    line_id = fields.Integer("Line ID")
    product_id = fields.Many2one("product.product", "Product")
    name = fields.Text("Description")
    quantity = fields.Float("Quantity")
    price = fields.Float("Unit Price")
    qty_to_split = fields.Float(string='Split Qty.')
    price_to_split = fields.Float(string='Split Price.')
    display_type = fields.Selection([
        ('line_section', "Section")], default=False, help="Technical field for UX purpose.")


class SplitInvoiceWizard(models.TransientModel):
    _name = 'split.invoice.wizard'
    _description = 'Split Invoice Record'

    split_selection = fields.Selection([
            ('invoice','Full Invoice'),
            ('lines','Invoice Lines'),
        ], 'Split Type', default='invoice')
    percentage = fields.Float("Percentage to Split", default=50)
    line_split_selection = fields.Selection([
            ('qty','Quantity'),
            ('price','Unit Price'),
        ], 'Split Line by', default='qty')
    line_ids = fields.One2many('split.invoice.line', 'wizard_id', string='Invoice Lines')
    partner_id = fields.Many2one('res.partner', 'Customer/Supplier', required=True)

    @api.model
    def default_get(self, fields):
        res = super(SplitInvoiceWizard, self).default_get(fields)
        active_model = self._context.get('active_model')
        if active_model == 'account.move':
            active_record = self.env['account.move'].browse(self._context.get('active_id'))
            if active_record.state!='draft':
                raise ValidationError(_('Invoice must be in draft state.'))
            lines = []
            for line in active_record.invoice_line_ids:
                lines.append((0,0,{
                    'name': line.name,
                    'product_id': line.product_id and line.product_id.id or False,
                    'line_id': line.id,
                    'quantity': line.quantity,
                    'price': line.price_unit,
                    'qty_to_split': 1,
                    'price_to_split': line.price_unit * 0.5,
                    'display_type': line.display_type,
                    'wizard_id': self.id
                }))
            res.update({'line_ids': lines, 'partner_id': active_record.partner_id.id })
        return res

    def update_invoice_data(self, invoice):        
        current_invoice_lines = invoice.line_ids.filtered(lambda line: not line.exclude_from_invoice_tab)
        others_lines = invoice.line_ids - current_invoice_lines
        if others_lines:
            credit = 0
            debit = 0
            for line in current_invoice_lines:
                credit += line.credit
                debit += line.debit
            total = credit - debit
            if total>0:
                others_lines[0].with_context(check_move_validity=False).debit = total
            else:
                others_lines[0].with_context(check_move_validity=False).credit = total

    def split_record(self):
        active_model = self._context.get('active_model')
        new_inv_id = False
        if active_model == 'account.move':
            InvLine = self.env['account.move.line']
            active_record = self.env['account.move'].browse(self._context.get('active_id'))

            #Create Splited Record
            if self.split_selection == 'invoice':
                if not self.percentage:
                    raise ValidationError(_('Please Enter Percentage To Split.'))
                new_inv_id = active_record.copy()
                new_inv_id.partner_id = self.partner_id.id
                for line in new_inv_id.line_ids:
                    new_price = line.price_unit * (self.percentage / 100)
                    line.with_context(check_move_validity=False).price_unit = new_price

                for active_line in active_record.line_ids:
                    new_price = active_line.price_unit - (active_line.price_unit * (self.percentage / 100))
                    active_line.with_context(check_move_validity=False).price_unit = new_price

            if self.split_selection == 'lines':
                for line in self.line_ids:
                    inv_line = InvLine.browse(line.line_id)
                    inv_line.with_context(check_move_validity=False).qty_to_split = line.qty_to_split
                    inv_line.with_context(check_move_validity=False).price_to_split = line.price_to_split

                if self.line_split_selection == 'qty':
                    lines_to_split = active_record.invoice_line_ids.filtered(lambda r: r.qty_to_split)
                    if len(lines_to_split) >= 1:
                        new_inv_id = active_record.with_context(from_split_invoice=True).copy()
                        new_inv_id.partner_id = self.partner_id.id
                        for line in new_inv_id.invoice_line_ids:
                            if not line.qty_to_split:
                                line.with_context(check_move_validity=False).unlink()
                            else:
                                line.with_context(check_move_validity=False).quantity = line.qty_to_split
                                line.with_context(check_move_validity=False).qty_to_split = 0
                        for line in active_record.invoice_line_ids:
                            if line.qty_to_split:
                                if line.quantity == line.qty_to_split:
                                    line.with_context(check_move_validity=False).unlink()
                                else:
                                    line.with_context(check_move_validity=False).quantity -= line.qty_to_split
                                    line.with_context(check_move_validity=False).qty_to_split = 0
                        new_inv_id.message_post(body=_("Record Splited."))
                        active_record.message_post(body=_("New Splited Record Created."))
                    else:
                        raise ValidationError(_('Please Enter Quantity To Split.'))

                if self.line_split_selection == 'price':
                    lines_to_split = active_record.invoice_line_ids.filtered(lambda r: r.price_to_split)
                    if len(lines_to_split) >= 1:
                        new_inv_id = active_record.copy()
                        new_inv_id.partner_id = self.partner_id.id
                        for line in new_inv_id.invoice_line_ids:
                            if not line.qty_to_split:
                                line.with_context(check_move_validity=False).unlink()
                            else:
                                line.with_context(check_move_validity=False).price_unit = line.price_to_split
                                line.with_context(check_move_validity=False).price_to_split = 0
                        for line in active_record.invoice_line_ids:
                            if line.price_to_split:
                                if line.price_unit == line.price_to_split:
                                    line.with_context(check_move_validity=False).unlink()
                                else:
                                    line.with_context(check_move_validity=False).price_unit -= line.price_to_split
                                    line.with_context(check_move_validity=False).price_to_split = 0
                        new_inv_id.message_post(body=_("Record Splited."))
                        active_record.message_post(body=_("New Splited Record Created."))
                    else:
                        raise ValidationError(_('Please Enter Amount To Split.'))

            new_inv_id._onchange_partner_id()
            self.update_invoice_data(new_inv_id)
            self.update_invoice_data(active_record)

        return new_inv_id
