# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models, SUPERUSER_ID, tools

class MailComposer(models.TransientModel):
	_inherit = 'mail.compose.message'

	def get_mail_values(self, res_ids):
		res = super(MailComposer, self).get_mail_values(res_ids)
		if self.model == 'account.move':
			for r in res_ids:
				Move = self.env[self.model].browse(r)
				mail_values = res[r]
				xml_version = Move.xml_version if Move.xml_version else None
				xml_txt = """
	<br /><br />
	Se adjunta la URL de la version XML del documento %s
</p>
				""" % xml_version
				if xml_version:
					mail_splited = mail_values['body'].split('</p>')
					new_body = mail_splited[0] + xml_txt + mail_splited[1]
					mail_values['body'] = new_body
					res[r] = mail_values
		return res