# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from io import StringIO, BytesIO
try:
	import qrcode
	qr_mod = True
except:
	qr_mod = False
from ast import literal_eval
import socket
from binascii import hexlify
from functools import partial
from base64 import encodestring

class AccountMove(models.Model):
	_inherit = 'account.move'
	
	@api.depends('name', 'ref','amount_tax', 'amount_total', 'invoice_date','partner_id.vat', 'partner_id.l10n_latam_identification_type_id','company_id.partner_id.vat')
	def _compute_get_qr_code(self):
		for invoice in self:


			if not all((invoice.ref != False, qr_mod)):
				invoice.account_qr_code = ""
				invoice.sunat_qr_code = ""
				continue
			res = [
				invoice.company_id.partner_id.vat or "-",
				invoice.serie_id.document_type_id.code or '',
				invoice.ref,
				str(invoice.amount_tax), str(invoice.amount_total),
				fields.Date.to_string(invoice.invoice_date) or '', 
				invoice.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or "-",
				invoice.partner_id.vat or "-", ""]
			qr_string = '|'.join(res)
			qr = qrcode.QRCode(
				version=1, error_correction=qrcode.constants.ERROR_CORRECT_Q)
			qr.add_data(qr_string)
			qr.make(fit=True)
			image = qr.make_image()
			tmpf = BytesIO()
			image.save(tmpf, 'png')
			invoice.account_qr_code = encodestring(tmpf.getvalue())
			invoice.sunat_qr_code   = invoice.account_qr_code


	account_qr_code = fields.Binary("QR Code", compute="_compute_get_qr_code")
