# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import base64
from lxml import etree
# import datetime

class import_xml_update(models.TransientModel):
    _name = 'import.xlm.update'

    cuenta = fields.Many2one('account.account','Cuenta',required=True)

    def update(self):
        for i in self.env['account.move.line'].search([('id','in',self.env.context['active_ids']),('move_id.state','=','draft')]):
            i.account_id = self.cuenta.id
        #if self.cuenta_ingreso.id:
        #    self.product_id.property_account_income_id = self.cuenta_ingreso.id
        #    self.env.cr.execute(""" update account_move_line set account_id = """ + str(self.cuenta_ingreso.id)  + """ where product_id =  """ + str(self.product_id.id) + """ and is_cpe_import = true and move_id in ( select id from account_move where type in ('out_invoice','out_refund') )  """ )

        #if self.cuenta_gasto.id:
        #    self.product_id.property_account_expense_id = self.cuenta_gasto.id
        #    self.env.cr.execute(""" update account_move_line set account_id = """ + str(self.cuenta_gasto.id)  + """ where product_id =  """ + str(self.product_id.id) + """ and is_cpe_import = true and move_id in ( select id from account_move where type in ('in_invoice','in_refund') )  """ )




class import_xml_file(models.TransientModel):
    _name = 'import.xml.file'

    #file_name = fields.Char(string='File Name')
    # journal_id = fields.Many2one(comodel_name='account.journal', string='Journal')
    lineas = fields.Many2many('ir.attachment', string='Files', required=True)
    tipe_import = fields.Selection([('in_invoice','Proveedor'),('out_invoice','Cliente'),('in_refund','Proveedor Refund'),('out_refund','Cliente Refund')],'Tipo de Facturas',default='in_invoice',required=True)
    diario = fields.Many2one('account.journal','Diario',required=True)
    tipo_document = fields.Many2one('einvoice.catalog.01','Tipo de Documento',required=True)


    def import_file(self):
        def _get_attachment_content(attachment):
            # Handle both _Attachment namedtuple in mail.thread or ir.attachment.
            return hasattr(attachment, 'content') and getattr(attachment, 'content') or base64.b64decode(attachment.datas)

        import os
        import zipfile


        for elem in self.lineas:               
            content = _get_attachment_content(elem)
            
            recibo = content.find(b'recibo.xsl')
            filename = elem.name
            # try:
            #     file_content = base64.b64decode(self.data_file)
            #     file_content = file_content.decode("utf-8")
            #     file_lines = file_content.split("\r\n")
            # except Exception as e:
            #     raise ValidationError('There was a problem importing %s' %self.filename + ' ' + e.reason)
            # if file_lines:
            #     for lines in file_lines:
            #         content += lines

            def get_value(target_tree, xpath, namespaces):
                try:
                    return target_tree.xpath(xpath, namespaces=namespaces)[0].text
                except IndexError as e:
                    print(e)
                    return ""
            # Check if the attachment is a xml.
            #if not filename.endswith('.xml') and not filename.endswith('.XML'):
            if not filename.upper().endswith('.XML'):
                raise ValidationError('Wrong file format.')

            invoice = self.env['account.move'].create({

                'partner_id' : self.env['res.partner'].search([])[0].id,
                'type' : self.tipe_import,
                'journal_id' : self.diario.id,
                'type_document_id' : self.tipo_document.id,
                'glosa': 'Importacion Facturas',
                'company_id' : self.env.company.id})


            Active_ID  = invoice.id
            type_invoice = invoice.type

            Issue_Date = False
            Sender_ID = False
            Currency_ID = False
            OrderReference = False
            Invoice_ID = False
            Tax_Amount_Total = False

            for line in invoice.invoice_line_ids:
                line.unlink()
            try:
                tree = etree.fromstring(content)

                ns = {"cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
                        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
                        "i2": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"}
                cabecera = True
                lines = self.env['account.move.line']
                # if tree.find
                if self.tipe_import in ('in_invoice','out_invoice'):
                    for x in tree.xpath("//cac:InvoiceLine", namespaces=ns):
                        print('***************************')
                        if cabecera:
                            Issue_Date = get_value(x, "../cbc:IssueDate", ns)
                            Invoice_ID = get_value(x, "../cbc:ID", ns)
                            OrderReference = get_value(x, "../cac:OrderReference/cbc:ID", ns)
                            Currency_Name = get_value(x, "../cbc:DocumentCurrencyCode", ns)
                            Sender_ID = get_value(x, "../cac:AccountingCustomerParty/cbc:CustomerAssignedAccountID", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
                            Receiver_ID = get_value(x, "../cac:AccountingSupplierParty/cbc:SupplierAssignedAccountID", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
                            Tax_Amount_Total = get_value(x, "../cac:TaxTotal/cbc:TaxAmount", ns)
                            Partner_Name = get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
                            Supplier_Name = get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
                            print(get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:StreetName", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cac:RegistrationAddress/cac:AddressLine/cbc:Line", ns))
                            print(get_value(x, "../cac:AccountingCustomerParty/cbc:CustomerAssignedAccountID", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID", ns))
                            print(get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:StreetName", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cac:RegistrationAddress/cac:AddressLine/cbc:Line", ns))
                            if type_invoice == 'in_invoice':
                                Sender_ID = Receiver_ID
                                Partner_Name = Supplier_Name
                            cabecera = False
                        print(get_value(x, "cbc:ID", ns))
                        print(get_value(x, "cbc:InvoicedQuantity", ns))
                        print(get_value(x, "cac:Item/cbc:Description", ns))
                        print(get_value(x, "cac:Price/cbc:PriceAmount", ns))
                        print(get_value(x, "cac:TaxTotal/cbc:TaxAmount", ns))
                        print(get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cbc:TaxableAmount", ns))
                        print(get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cbc:TaxAmount", ns))
                        print(get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:ID", ns))
                        print(get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:Percent", ns) or get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cbc:Percent", ns)) 
                        print(get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme/cbc:ID", ns))
                        print(get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme/cbc:Name", ns))
                        print('***************************')
                        Currency_ID = self.env['res.currency'].search([('name', 'ilike', Currency_Name)], limit=1)

                        Product_Name = get_value(x, "cac:Item/cbc:Description", ns)
                        Product_ID = self.env['product.product'].search([('name', 'ilike', Product_Name)], limit=1)
                        if not Product_ID:
                            # TODO cambiar por un producto desde la data por defecto
                            # el ID 6 lo cree a mano en esta bd
                            Product_ID = self.env['product.product'].create({'name':Product_Name})
                        Line_Quantity = get_value(x, "cbc:InvoicedQuantity", ns)
                        Price_Unit = get_value(x, "cac:Price/cbc:PriceAmount", ns)
                        # TODO cambiar por impuesto de factura electrónica esto puede mejorar
                        tax_ids = []
                        for t in tree.xpath("//cac:TaxTotal/cac:TaxSubtotal", namespaces=ns):
                            Taxable_Amount = get_value(t, "cbc:TaxableAmount", ns)
                            Tax_Percent = get_value(t, "cac:TaxCategory/cbc:Percent", ns) or get_value(t, "cbc:Percent", ns) 
                            Tax_Name = get_value(t, "cac:TaxCategory/cac:TaxScheme/cbc:Name", ns)
                            Tax_Amount = get_value(t, "cbc:TaxAmount", ns)
                            Tax_Line_ID = self.env['account.tax'].search([('name', 'ilike', Tax_Name)], limit=1)
                            if Tax_Line_ID.id:
                                tax_ids.append(Tax_Line_ID.id)
                    
                        cuentaL = False
                        if self.tipe_import in ('out_invoice','out_refund'):
                            cuentaL = Product_ID.property_account_income_id.id if Product_ID.property_account_income_id.id else Product_ID.categ_id.property_account_income_categ_id.id
                        else:
                            cuentaL = Product_ID.property_account_expense_id.id if Product_ID.property_account_expense_id.id else Product_ID.categ_id.property_account_expense_categ_id.id
                        vals = {
                            'move_id': Active_ID,
                            'product_id': Product_ID.id,
                            'name': Product_Name,
                            'quantity': float(Line_Quantity),
                            'price_unit': float(Price_Unit),
                            'tax_ids': [(6, 0, tax_ids)],
                            'account_id': cuentaL,
                            'is_cpe_import': True,
                            'discount':0,
                        }
                        lines.with_context({'check_move_validity':False}).create(vals)                
                else:
                    for x in tree.xpath("//cac:CreditNoteLine", namespaces=ns):
                        print('***************************')
                        if cabecera:
                            Issue_Date = get_value(x, "../cbc:IssueDate", ns)
                            Invoice_ID = get_value(x, "../cbc:ID", ns)
                            OrderReference = get_value(x, "../cac:InvoiceDocumentReference/cbc:ID", ns)
                            Currency_Name = get_value(x, "../cbc:DocumentCurrencyCode", ns)
                            Sender_ID = get_value(x, "../cac:AccountingCustomerParty/cbc:CustomerAssignedAccountID", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
                            Receiver_ID = get_value(x, "../cac:AccountingSupplierParty/cbc:SupplierAssignedAccountID", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
                            Tax_Amount_Total = get_value(x, "../cac:TaxTotal/cbc:TaxAmount", ns)
                            Partner_Name = get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
                            Supplier_Name = get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
                            print(get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:StreetName", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cac:RegistrationAddress/cac:AddressLine/cbc:Line", ns))
                            print(get_value(x, "../cac:AccountingCustomerParty/cbc:CustomerAssignedAccountID", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID", ns))
                            print(get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:StreetName", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cac:RegistrationAddress/cac:AddressLine/cbc:Line", ns))
                            if type_invoice == 'in_refund':
                                Sender_ID = Receiver_ID
                                Partner_Name = Supplier_Name
                            cabecera = False
                        print(get_value(x, "cbc:ID", ns))
                        print(get_value(x, "cbc:InvoicedQuantity", ns))
                        print(get_value(x, "cac:Item/cbc:Description", ns))
                        print(get_value(x, "cac:Price/cbc:PriceAmount", ns))
                        print(get_value(x, "cac:TaxTotal/cbc:TaxAmount", ns))
                        print(get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cbc:TaxableAmount", ns))
                        print(get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cbc:TaxAmount", ns))
                        print(get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:ID", ns))
                        print(get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:Percent", ns) or get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cbc:Percent", ns)) 
                        print(get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme/cbc:ID", ns))
                        print(get_value(x, "cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme/cbc:Name", ns))
                        print('***************************')
                        Currency_ID = self.env['res.currency'].search([('name', 'ilike', Currency_Name)], limit=1)

                        Product_Name = get_value(x, "cac:Item/cbc:Description", ns)
                        Product_ID = self.env['product.product'].search([('name', 'ilike', Product_Name)], limit=1)
                        if not Product_ID:
                            # TODO cambiar por un producto desde la data por defecto
                            # el ID 6 lo cree a mano en esta bd
                            Product_ID = self.env['product.product'].create({'name':Product_Name})
                        Line_Quantity = get_value(x, "cbc:CreditedQuantity", ns)
                        Price_Unit = get_value(x, "cac:Price/cbc:PriceAmount", ns)
                        # TODO cambiar por impuesto de factura electrónica esto puede mejorar
                        tax_ids = []
                        for t in tree.xpath("//cac:TaxTotal/cac:TaxSubtotal", namespaces=ns):
                            Taxable_Amount = get_value(t, "cbc:TaxableAmount", ns)
                            Tax_Percent = get_value(t, "cac:TaxCategory/cbc:Percent", ns) or get_value(t, "cbc:Percent", ns) 
                            Tax_Name = get_value(t, "cac:TaxCategory/cac:TaxScheme/cbc:Name", ns)
                            Tax_Amount = get_value(t, "cbc:TaxAmount", ns)
                            Tax_Line_ID = self.env['account.tax'].search([('name', 'ilike', Tax_Name)], limit=1)
                            if Tax_Line_ID.id:
                                tax_ids.append(Tax_Line_ID.id)
                    
                        cuentaL = False
                        if self.tipe_import in ('out_invoice','out_refund'):
                            cuentaL = Product_ID.property_account_income_id.id if Product_ID.property_account_income_id.id else Product_ID.categ_id.property_account_income_categ_id.id
                        else:
                            cuentaL = Product_ID.property_account_expense_id.id if Product_ID.property_account_expense_id.id else Product_ID.categ_id.property_account_expense_categ_id.id

                        vals = {
                            'move_id': Active_ID,
                            'product_id': Product_ID.id,
                            'name': Product_Name,
                            'quantity': float(Line_Quantity),
                            'price_unit': float(Price_Unit),
                            'tax_ids': [(6, 0, tax_ids)],
                            'account_id': cuentaL,
                            'is_cpe_import': True,
                            'discount':0,
                        }
                        lines.with_context({'check_move_validity':False}).create(vals)   

                        tem = invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)
                        if len(tem) == 0:
                            vals = {
                                'name': Partner_Name,
                                'vat': Sender_ID,
                                'l10n_latam_identification_type_id': self.env['l10n_latam.identification.type'].search([('name','=','DNI')])[0].id if len(Sender_ID)==8 else self.env['l10n_latam.identification.type'].search([('name','=','RUC')])[0].id,
                            }
                            self.env['res.partner'].create(vals)

                        fac_rel = self.env['account.move'].search([('ref','=',OrderReference),('partner_id','=',invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)[0].id) ])
                        if len(fac_rel)== 0:
                            raise UserError('No existe el comprobante relacionado a la nota de Credito')
                        else:
                            fac_rel= fac_rel[0]
                        self.env['doc.invoice.relac'].create({
                            'type_document_id':fac_rel.type_document_id.id,
                            'date':fac_rel.invoice_date,
                            'nro_comprobante':OrderReference,
                            'amount_currency':fac_rel.amount_total,
                            'amount':fac_rel.amount_total* fac_rel.currency_rate,
                            'bas_amount':fac_rel.amount_untaxed* fac_rel.currency_rate,
                            'tax_amount':fac_rel.amount_total* fac_rel.currency_rate - fac_rel.amount_untaxed* fac_rel.currency_rate,
                            'move_id':invoice.id,
                            })
                
            except Exception as e:
                print(e)
                import sys, traceback
                exc_type, exc_value, exc_traceback = sys.exc_info()
                t= traceback.format_exception(exc_type, exc_value,exc_traceback)
                print(t)
                raise UserError(_(e))
                
            invoice.invoice_date = Issue_Date
            tem = invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)
            if len(tem) == 0:
                vals = {
                    'name': Partner_Name,
                    'vat': Sender_ID,
                    'l10n_latam_identification_type_id': self.env['l10n_latam.identification.type'].search([('name','=','DNI')])[0].id if len(Sender_ID)==8 else self.env['l10n_latam.identification.type'].search([('name','=','RUC')])[0].id,
                }
                self.env['res.partner'].create(vals)
            invoice.partner_id = invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)
            invoice.partner_id.update_document()
            split_invoice_number = Invoice_ID.split('-')
            invoice.ref = split_invoice_number[0] + '-' + split_invoice_number[1].zfill(7)
            invoice.currency_id = Currency_ID

            type = invoice.type or self.env.context.get('type', 'out_invoice')
            rec_account = invoice.partner_id.property_account_receivable_id
            pay_account = invoice.partner_id.property_account_payable_id
            if not rec_account and not pay_account:
                action = self.env.ref('account.action_account_config')
                msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            if type in ('in_invoice', 'in_refund'):
                account_id = pay_account.id
                payment_term_id = invoice.partner_id.property_supplier_payment_term_id.id
            else:
                account_id = rec_account.id
                payment_term_id = invoice.partner_id.property_payment_term_id.id


            if len( self.env['account.move'].search([('ref','=',Invoice_ID)]) ) > 0:
                invoice.unlink()
            else:

                invoice.name = Invoice_ID if recibo == -1 else Invoice_ID
                invoice.invoice_name = Invoice_ID if recibo == -1 else Invoice_ID
                invoice.ref = Invoice_ID if recibo == -1 else Invoice_ID

                invoice.account_id = account_id
                invoice.date = Issue_Date
                invoice.partner_shipping_id = invoice.partner_id
                invoice.payment_term_id = payment_term_id
                invoice.amount_tax = Tax_Amount_Total
                invoice.amount_total = invoice.amount_untaxed + invoice.amount_tax
                invoice._compute_amount()
                #invoice._compute_sign_taxes()
                #invoice._compute_residual()
                #invoice.compute_taxes()


