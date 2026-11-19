from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_user_name = fields.Char(related='invoice_user_id.name', store=True)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_free = fields.Boolean(string='Is free', compute='get_is_free', store=True)
    tipo_clienteex = fields.Char(compute="get_data_report_excel", store=True, string="Tipo Cliente")
    direccion_completax = fields.Char(compute="get_data_report_excel", store=True, string="Direccion")
    cost_unitx = fields.Float(compute="get_data_report_excel", store=True, string="Costo unit.")
    doc_almacenx = fields.Char(compute="get_data_stock_picking", store=True, string="Doc. Almacen")
    numbergx = fields.Char(compute="get_data_stock_picking", store=True, string="Guia")
    albaran_originx = fields.Char(compute="get_data_stock_picking", store=True, string="Observaciones")
    destino_loccx = fields.Char(compute="get_data_stock_picking", store=True, string="Ubicacion Destino")
    origin_loccx = fields.Char(compute="get_data_stock_picking", store=True, string="Ubicacion Origin")
    demandadox = fields.Float(compute="get_data_stock_picking", store=True)
    cost_totalx = fields.Float(compute="get_data_stock_picking", store=True, string="Costo Total")
    lotesx = fields.Char(compute="get_data_stock_picking", store=True)
    type_operation_sunatx = fields.Many2one('type.operation.kardex', compute="get_data_stock_picking", store=True)
    type_picking_idx = fields.Many2one('stock.picking.type', compute="get_data_stock_picking", store=True,
                                       string="Tipo Picking")
    origin_locx = fields.Many2one('stock.location', compute="get_data_stock_picking", store=True,
                                  string="Ubicacion Origin")

    @api.depends('tax_ids')
    def get_is_free(self):
        for res in self:
            l10n_pe_edi_tax_code = res.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == '9996')
            if len(l10n_pe_edi_tax_code) >= 1:
                is_free = True
            else:
                is_free = False
        res.is_free = is_free

    @api.depends('move_id.partner_id.category_id', 'move_id.partner_id')
    def get_data_report_excel(self):
        for res in self:
            res.tipo_clienteex = res.move_id.partner_id.category_id[0].name if len(
                res.move_id.partner_id.category_id) > 0 else False
            res.direccion_completax = res.move_id.partner_id.contact_address if res.move_id.partner_id else False
            res.cost_unitx = res.product_id.standard_price if res.product_id else False

    @api.depends('move_id')
    def get_data_stock_picking(self):
        for res in self:
            doc_almacenx = ""
            albaran_originx = ""
            numbergx = ""
            destino_loccx = ""
            origin_loccx = ""
            demandadox = 0
            cost_totalx = 0
            lotesx = ''
            stock_move = self.env['stock.move'].search(
                [('state', '=', 'done'), ('invoice_id', '=', res.move_id.id),
                 ('product_id', '=', res.product_id.id)])
            demandadox = sum(stock_move.mapped('quantity_done'))
            cost_totalx = res.product_id.standard_price * demandadox
            stock_picking = stock_move.mapped('picking_id')
            if len(stock_picking) == 1:
                doc_almacenx = stock_picking[0].name
                albaran_originx = stock_picking[0].origin
                numbergx = stock_picking[0].numberg
                origin_loccx = stock_picking[0].location_id.display_name
                destino_loccx = stock_picking[0].location_dest_id.display_name
            else:
                i = 0
                for picking in stock_picking:
                    if i < len(stock_picking) - 1:
                        doc_almacenx += picking.name + '/' if picking.name else ""
                        albaran_originx += picking.origin + '/' if picking.origin else ""
                        numbergx += picking.numberg + '/' if picking.numberg else ""
                        origin_loccx += picking.location_id.display_name + '/' if picking.location_id.display_name else ""
                        destino_loccx += picking.location_dest_id.display_name + '/' if picking.location_dest_id.display_name else ""
                    else:
                        doc_almacenx += picking.name if picking.name else ""
                        albaran_originx += picking.origin if picking.origin else ""
                        numbergx += picking.numberg if picking.numberg else ""
                        origin_loccx += picking.location_id.display_name if picking.location_id.display_name else ""
                        destino_loccx += picking.location_dest_id.display_name if picking.location_dest_id.display_name else ""
                    i += 1
            str_lotes = ''
            for move in stock_move:
                stock_lines = move.move_line_ids
                if stock_lines:
                    for sl in stock_lines:
                        if sl.lot_id:
                            str_fv = ''
                            if sl.lot_id.life_date:
                                split_fv = str(sl.lot_id.life_date.strftime('%Y-%m-%d'))
                                str_fv = ' FV: ' + str(split_fv)

                            str_lotes += 'Lot: ' + str(sl.lot_id.display_name) + str_fv + ' cant: ' + str(
                                sl.qty_done) + '  |  '
            res.doc_almacenx = doc_almacenx
            res.albaran_originx = albaran_originx
            res.numbergx = numbergx
            res.destino_loccx = destino_loccx
            res.origin_loccx = origin_loccx
            res.demandadox = demandadox
            res.cost_totalx = cost_totalx
            res.lotesx = str_lotes
            if len(stock_picking) > 0:
                res.type_operation_sunatx = stock_picking[0].type_operation_sunat_id.id
                res.type_picking_idx = stock_picking[0].picking_type_id.id
                res.origin_locx = stock_picking[0].location_id.id
