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
	
	def url_cpe(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		url_return = base_url + "/cpe/download_report/" + str(self.id)
		return url_return