from odoo import models, fields, api, _
import odoo.tools as tools
from base64 import b64decode, b64encode
from odoo.exceptions import ValidationError
import os

class detraction_create_file(models.TransientModel):
    _name = 'detraction.create.file.wizard'

    def create_file(self):
        vals = self.env['detraction.create.file']
        vals = {}
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=(vals['company_id'])).next_by_code('detraction.lot.number') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('detraction.lot.number') or _('New')
        if len(vals) == 0:
            raise ValidationError('Please Select Records, Without Records Detraction File Cannot be Created')
        else:
            #payments = self.env['account.payment'].search([('id', 'in', vals['active_ids'])])
            #vals.update({'payment_ids': [(6, 0, vals['active_ids'])]})

            payments = self.env['account.payment'].search([('id', 'in', self.env.context['active_ids'])])
            vals.update({'payment_ids': [(6, 0, self.env.context['active_ids'])]})
            lines = []
            str_line = '*'
            if self.env.user.company_id.partner_id.vat:
                str_line += self.env.user.company_id.partner_id.vat
            else:
                raise ValidationError(_('The main company does not have a RUC number'))
            str_line += self.env.user.company_id.partner_id.name[:35].ljust(35)
            str_line += vals['name']
            total = 0
            for imp in payments:
                total += imp.account_amount
                total = round(total, 2)

            str_line += str(int(total)).rjust(13, '0') + '00'
            str_line = str_line.encode('utf-8')
            lines.append(str_line)
            message = ''
            count_partners = 0
            partners_noacc = []
            for det in payments:
                if det.detraction_lot_id:
                    if not vals.get('update', False):
                        raise ValidationError(_("Payment %s it's allready posted in the detraction lot number %s" % (det.name, det.detraction_lot_id.name)))
                str_line = ''
                str_line += det.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code
                str_line += det.partner_id.vat
                str_line += '                                   '
                str_line += '000000000'
                str_line += det.type_good_service
                detraction_account = ''
                for account in det.partner_id.bank_ids:
                    if account.type_of_account == '2':
                        detraction_account = account.acc_number

                if count_partners > 4:
                    if det.partner_id.id not in partners_noacc:
                        count_partners += 1
                        partners_noacc.append(det.partner_id.id)
                    elif detraction_account == '':
                        if det.partner_id.id not in partners_noacc:
                            message = message + 'Partner %s does not have a detraction account please add one.' % det.partner_id.name + '\n'
                            count_partners += 1
                            partners_noacc.append(det.partner_id.id)
                    str_line += detraction_account
                    str_line += str(int(det.account_amount)).rjust(13, '0') + '00'
                    str_line += det.type_operation
                    str_line += str(det.payment_date)[:4] + str(det.payment_date)[5:7]
                    if not det.invoice_ids.journal_id.pe_invoice_code:
                        raise ValidationError(_('The journal does not have an Invoice Type Code in Peruvian Settings.'))
                    str_line += str(det.invoice_ids.journal_id.pe_invoice_code)
                    str_line += det.invoice_ids.reference[:det.invoice_ids.reference.find('-')].zfill(4) if det.invoice_ids.reference else 'ERRO'
                    str_line += det.invoice_ids.reference[det.invoice_ids.reference.find('-') + 1:].rjust(8, '0') if det.invoice_ids.reference else 'ERROR***'
                    str_line = str_line.encode('utf-8')
                    lines.append(str_line)

            if count_partners > 5:
                message = message + '\n There is %s more partners that have no detraction account.' % str(count_partners - 5)
            if message != '':
                raise ValidationError(_(message))
            file_name = self.env.user.company_id.partner_id.vat + vals['name']
            my_path = os.path.abspath(os.path.dirname(__file__))
            path = os.path.join(my_path, '../static/D' + file_name + '.TXT')
            path_unlink = os.path.join(my_path, '../static/')
            for filename in os.listdir(path_unlink):
                if filename.endswith('.TXT'):
                    os.unlink(path_unlink + filename)

            file = open(path, 'w+')
        if file:
            output = ''
            for line in lines:
                output += line.decode('ascii') + '\n'

            txt_file = output
            vals.update({'txt_file':b64encode(txt_file.encode('utf-8')),  'file_name':filename,  'total_form':total})
            file.write(txt_file)
            if not vals.get('update', False):
                wizard = self.env['detraction.create.file']
                wizard.create(vals)
            else:
                wizard = self.env['detraction.create.file'].browse(vals.get('id', 0))
                wizard.write(vals)
            addons_path = tools.config['addons_path'].split(',')
            for addons_folder in addons_path:
                if not path.find(addons_folder):
                    path = path[len(addons_folder):]

            return {'type':'ir.actions.act_url', 
             'name':'contract', 
             'url':path + '?download=true'}