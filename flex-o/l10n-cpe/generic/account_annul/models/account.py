from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    annul = fields.Boolean('Annulled', readonly=True, default=False)
    last_partner_id = fields.Many2one('res.partner', string='Last partner')
    # TODO no lo utilizo
    state = fields.Selection(selection_add=[
        ('annul', 'Anulled'),
    ],
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Pro-forma' status is used when the invoice does not have an invoice number.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Anulled' status is used when user annul invoice (keeping the invoice number).\n"
             " * The 'Cancelled' status is used when user cancel invoice.")

    def button_annul(self):
        # Verificamos que la factura no tenga pagos asociados.
        if self.amount_total != self.amount_residual:
            raise UserError(_('The invoce can\'t be annuled because there is some payments in progress.'))
        # Verificamos si esta instalado el modulo de letras
        module_boe = self.env['ir.module.module'].search([('name','=','jp_account_bills_of_exchange')])
        boe = True if module_boe and module_boe.state == 'installed' else False
        if boe:
            # Comprobar si no esta canjeada con una letra
            if self.bill_form_id:
                raise UserError(_('This invoice have been redeemed with a bill of exchange form %s. Please revert the process first.') %self.bill_form_id)
        # Para anular la factura al estilo ITGRUPO
        self.button_draft()
        self.button_cancel()
        annuled_partner = self.env['main.parameter'].search([])[0].cancelation_partner
        annuled_product = self.env['main.parameter'].search([])[0].cancelation_product
        if annuled_partner and annuled_product:
            self.last_partner_id = self.partner_id
            self.partner_id = annuled_partner
            for line in self.invoice_line_ids:
                # line.discount = 100
                val = {
                    'product_id': annuled_product.id,
                    # 'name': line.name,
                    'account_id': line.account_id.id,
                    'quantity': line.quantity,
                    'product_uom_id': line.product_uom_id,
                    'price_unit': line.price_unit,
                    'discount': 100,
                    'tax_ids': line.tax_ids.ids,
                }
                self.invoice_line_ids = [(2,line.id)]
                self.invoice_line_ids = [(0,0,val)]
            # Para ITgrupo
            # Tipo de comprobante y numero de documento para las lineas
            # Asi se pueden ver en los reportes contables de diario y mayor
            for line in self.line_ids:
                line.type_document_id = self.type_document_id
                line.nro_comp = self.ref
        else:
            raise UserError(_('You must select a partner and product for annuled vouchers in main parameter.'))
        self.annul = True
        self.campo_34_sale = '2'
        self.state = 'posted'
        # Verificamos si esta instalado el modulo de letras
        module_boe = self.env['ir.module.module'].search([('name','=','jp_account_bills_of_exchange')])
        boe = True if module_boe and module_boe.state == 'installed' else False
        if boe:
            bill = self.env['account.bill'].search([('protest_debit_note_id','=', self.id)])
            if bill:
                bill.protest_debit_note_id = False
        return True

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        if self.last_partner_id:
            self.partner_id = self.last_partner_id
        self.annul = False
        self.campo_34_sale = '1'
        return res

class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"
    _description = "Account Invoice report"

    state = fields.Selection(selection_add=[('annul', 'Anulled')])
