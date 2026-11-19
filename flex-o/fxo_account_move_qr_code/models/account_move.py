# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from io import StringIO, BytesIO
from base64 import encodestring
def install(package):
    import sys, subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import qrcode
except:
    install('qrcode')

class AccountMove(models.Model):
    _inherit = 'account.move'

    sunat_qr_code = fields.Binary(string='QR Code')

    def compute_get_qr_code(self):
        for inv in self:
            if inv.hash_code:
                qr_string = inv.hash_code
                qr = qrcode.QRCode(
                    version=1, error_correction=qrcode.constants.ERROR_CORRECT_Q)
                qr.add_data(qr_string)
                qr.make(fit=True)
                image = qr.make_image()
                tmpf = BytesIO()
                image.save(tmpf, 'png')
                inv.sunat_qr_code = encodestring(tmpf.getvalue())
                print('QRCODE', qr, image, tmpf.getvalue())
            else:
                print('ELSE', inv.hash_code)
                inv.sunat_qr_code = False