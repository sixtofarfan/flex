# -*- encoding: utf-8 -*-
from PIL import Image
import requests
import pytesseract
from bs4 import BeautifulSoup
from bs4 import Comment
from lxml import etree
from io import StringIO , BytesIO
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from collections import OrderedDict
import re
import logging
import time
import zipfile
import os
from suds.client import Client
_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    # @api.constrains("vat","l10n_latam_identification_type_id")
    # def vat_l10n_fxo(self):
    #     self.doc_type =  self.doc_type #self.l10n_latam_identification_type_id.l10n_pe_vat_code
    #     self.doc_number =  self.doc_number #self.vat

    def action_update(self):
        active_ids = self.env.context.get('active_ids', [])
        partners = self.env['res.partner'].search([('id','in',active_ids),('vat','!=', False)])
        print(len(partners))
        i=1
        error_message = ''
        for partner in partners:
            print(str(i) + ' / ' + str(len(partners)))
            i += 1
            if len(partner.vat) != 8 and partner.l10n_latam_identification_type_id.l10n_pe_vat_code == '1':
                error_message += 'The DNI entered is incorrect for %s' % partner.name + '\n'
            if len(partner.vat) == 8 and partner.l10n_latam_identification_type_id.l10n_pe_vat_code == '1':
                respuesta = self.buscar_dni(partner.vat.strip())
                if respuesta and respuesta['detail'] == 'Not found.':
                    error_message += 'The DNI entered is not found for %s' % partner.name + '\n'
            if not self.validate_ruc(partner.vat) and partner.l10n_latam_identification_type_id.l10n_pe_vat_code == '6':
                error_message += 'The RUC entered is incorrect for %s' % partner.name + '\n'
        if error_message:
            raise UserError(_(error_message))
        i=1
        for partner in partners:
            print(str(i) + ' / ' + str(len(partners)))
            i += 1
            partner._doc_number_change()

    @staticmethod
    def _get_captcha(type, countdown):
        s = requests.Session()
        if type.upper() == 'R':
            # Solo para consulta de RUC el countdown sera de 2 intentos para resolver el captcha
            if countdown > 0:
                try:
                    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                    r = s.get('http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsmulruc/captcha?accion=image', headers=headers)
                    if r.status_code != 200:
                        return (False, r)
                # except requests.ConnectionException as e:
                #except s.exceptions .RequestException as e:
                # except requests.exceptions.ConnectionError as e:
                except s.exceptions.RequestException as e:
                    if countdown > 0:
                        consuta, captcha_val = cls._get_captcha("R", countdown - 1)
                        return (consuta, captcha_val)
                    else:
                        return (False, e)
                try:
                    img = Image.open(BytesIO(r.content))

                except Exception as e:

                    return (False, e)

                captcha_val = pytesseract.image_to_string(img)
                captcha_val = captcha_val.strip().upper()
                return (s, captcha_val)
            else:
                return (False, e)

    @classmethod
    def _get_sunat_details(cls, vat):
        # pudb.set_trace()
        print("_get_sunat_details - l10n_pe_vat")
        vals = {}
        if not cls.validate_ruc(vat):
            raise UserError(_('the RUC entered is incorrect'))
        texto_consulta = ''
        can=0
        while len(texto_consulta)<3000:
            can += 1 
            for i in range(10):
                consulta, captcha_val = cls._get_captcha("R", 1)
                if not consulta:
                    return  False
                #    raise UserError(_('El servidor de consulta no está en linea, por favor reitentelo más tarde.'))
                if captcha_val.isalpha():
                    break
            payload = OrderedDict()
            payload['accion'] = 'consManual'
            # payload['razSoc'] = ''
            payload['txtRuc'] = ''
            payload['selRuc'] = vat
            # payload['nrodoc'] = ''
            # payload['contexto'] = 'ti-it'
            # payload['tQuery'] = 'on'
            # payload['search1'] = vat
            payload['codigoM'] = captcha_val
            # payload['tipdoc'] = '1'
            # payload['search2'] = ''
            # payload['coddpto'] = ''
            # payload['codprov'] = ''
            # payload['coddist'] = ''
            # payload['search3'] = ''
            payload['data'] = 'downloadable_file1.tar'
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1 X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
            post = consulta.post("http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsmulruc/jrmS00Alias", params=payload,headers=headers, stream=True)
            if post.status_code != 200:
                return  False
            
            soup = BeautifulSoup(post.text, 'html.parser')
            table_td = soup.find_all('a')

            my_path = os.path.abspath(os.path.dirname(__file__))
            path = os.path.join(my_path, '../static/')
            time.sleep(0.01)
            # headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
            response = requests.post(table_td[0]['href'], headers=headers)
            with open(path + 'archivo.zip', "wb") as f:
                f.write(response.content)
            zip = zipfile.ZipFile(path + 'archivo.zip')
            file = zip.read(zip.filelist[0].filename)
            texto_consulta = file.decode('UTF-8')
                #raise UserError(_('El servidor de consulta no está en linea, por favor reitentelo más tarde.'))
            # texto_error = 'Surgieron problemas al procesar la consulta'
            # texto_consulta = post.text

            # if texto_error in (texto_consulta):
            #     return  False
            #    raise UserError(_('El servidor de consulta no responde, por favor reintentelo más tarde'))
            # if can > 5:
            #     return  False
            #    raise UserError(_('El servidor de consulta no responde, por favor reintentelo más tarde'))

        # texto_consulta = texto_consulta.replace('<br>', '\n')
        # texto_consulta = re.sub("(<!--.*?-->)", "", texto_consulta, flags=re.MULTILINE)
        # parser = etree.HTMLParser()
        # tree   = etree.parse(StringIO(texto_consulta), parser)
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(texto_consulta), parser)
        flag_nombre = False
        flag_comercial = False
        flag_tipo_contrib = False
        flag_sistema_emision = False
        flag_sistema_conta = False
        flag_direccion = False
        flag_estado = False
        flag_condicion = False
        flag_padrones = False
        flag_ciu = False

        flag_reg_date = False
        flag_start_date = False
        flag_export = False
        flag_esystem = False
        flag_esystem_from = False
        flag_esystem_receipts = False
        flag_ple_from = False

        # Busqueda de datos
        for _td in tree.findall("//div[@id='print']/table//td"):
            if _td.attrib['class'] == 'bgn':
                if re.findall(re.compile('N.mero.de RUC.'), _td.text):
                    flag_nombre = True
                elif re.findall(re.compile('Nombre Comercial.'), _td.text):
                    flag_comercial = True
                elif re.findall(re.compile('Tipo Contribuyente.'), _td.text):
                    flag_tipo_contrib = True
                elif re.findall(re.compile('Sistema de Emisi.n de Comprobante.'), _td.text):
                    flag_sistema_emision = True
                elif re.findall(re.compile('Sistema de Contabilidad.'), _td.text):
                    flag_sistema_conta = True
                elif re.findall(re.compile('Direcci.n.'), _td.text):
                    flag_direccion = True
                elif re.findall(re.compile('Estado.'), _td.text):
                    flag_estado = True
                elif re.findall(re.compile('Condici.n.'), _td.text):
                    flag_condicion = True
                elif re.findall(re.compile('Padrones.'), _td.text):
                    flag_padrones = True
                elif re.findall(re.compile('Actividad.es. Econ.mica.s.'), _td.text):
                    flag_ciu = True
                elif re.findall(re.compile('Fecha de Inscripci.n.'), _td.text):
                    flag_reg_date = True
                elif re.findall(re.compile('Fecha de Inicio.'), _td.text):
                    flag_start_date = True
                elif re.findall(re.compile('Actividad de Comercio Exterior.'), _td.text):
                    flag_export = True
                elif re.findall(re.compile('Sistema de Emision.'), _td.text):
                    flag_esystem = True
                elif re.findall(re.compile('Emisor electr.nico.'), _td.text):
                    flag_esystem_from = True
                elif re.findall(re.compile('Comprobantes Electr.nicos.'), _td.text):
                    flag_esystem_receipts = True
                elif re.findall(re.compile('Afiliado al PLE desde.'), _td.text):
                    flag_ple_from = True
            elif _td.attrib['class'] == 'bg':
                if flag_nombre:
                    flag_nombre = False
                    # vals['legal_name'] = _td.text.split(' - ')[1]
                    legal_names = _td.text.split('-')
                    var_name = ""
                    for i in range(1, len(legal_names)):
                        var_name += legal_names[i]
                    vals['legal_name'] = var_name.strip()

                if flag_comercial:
                    flag_comercial = False
                    vals['commercial_name'] = _td.text
                elif flag_direccion:
                    flag_direccion = False
                    street = _td.text.strip().split('-')
                    if not street:
                        street = _td.text.strip().split(' ')

                    for i in range(len(street)):
                        street[i] = street[i].strip()
                    if len(street) >= 3:
                        if street[-1]:
                            vals['district'] = street[-1]
                        if street[-2]:
                            vals['province'] = street[-2]
                        if len(street[-3].split(' ')) > 1:
                            vals['region'] = street[-3].split(' ')[-1]

                    vals['street'] = " ".join(street)
                elif flag_tipo_contrib:
                    flag_tipo_contrib = False
                    vals['type_taxpayer'] = _td.text
                elif flag_sistema_emision:
                    flag_sistema_emision = False
                    vals['emission_system'] = _td.text
                elif flag_sistema_conta:
                    flag_sistema_conta = False
                    vals['accounting_system'] = _td.text
                elif flag_estado:
                    flag_estado = False
                    vals['state'] = _td.text
                elif flag_condicion:
                    flag_condicion = False
                    vals['condition'] = _td.text.strip()
                elif flag_padrones:
                    flag_padrones = False
                    if re.findall(re.compile('.Agentes de Retenci.n de IGV.'), _td.text):
                        if len(_td.text.split('(')) > 1:
                            string_res = _td.text.split('(')[1]
                            if len(string_res.split(')')) > 1:
                                resol_val = string_res.split(')')[0]
                                vals['retention_agent_resolution'] = resol_val
                                string_date = _td.text.strip()[-10:]
                                vals['retention_agent_from'] = datetime.strptime(string_date, "%d/%m/%Y").strftime(
                                    "%Y-%m-%d")
                                vals['retention_agent'] = True

                elif flag_ciu:
                    flag_ciu = False
                    ciu_ids = []
                    if _td.text:
                        cius = _td.text.strip().split("\n")
                        for ciu in cius:
                            if ciu.strip():
                                ciu_sunat = ciu.strip().split("-")
                                element = {}
                                element['code'] = ciu_sunat[1].strip()
                                element['name'] = ciu_sunat[2].strip()
                                ciu_ids.append(element)
                    vals['activities'] = ciu_ids

                elif flag_reg_date:
                    flag_reg_date = False
                    if _td.text.strip() != "-":
                        vals['registration_date'] = datetime.strptime(_td.text.strip(' '), "%d/%m/%Y").strftime(
                            "%Y-%m-%d")
                elif flag_start_date:
                    flag_start_date = False
                    if _td.text.strip() != "-":
                        vals['started_activity_date'] = datetime.strptime(_td.text.strip(' '), "%d/%m/%Y").strftime(
                            "%Y-%m-%d")
                elif flag_export:
                    flag_export = False
                    vals['foreign_trade_activity'] = _td.text.strip() if _td.text != None else ''
                elif flag_esystem:
                    flag_esystem = False
                    vals['electronic_system'] = _td.text.strip()
                elif flag_esystem_from:
                    flag_esystem_from = False
                    if _td.text.strip() != "-":
                        vals['electronic_system_from'] = datetime.strptime(_td.text.strip(' '), "%d/%m/%Y").strftime(
                            "%Y-%m-%d")
                elif flag_esystem_receipts:
                    flag_esystem_receipts = False
                    vals['electronic_system_receipts'] = _td.text.strip()
                elif flag_ple_from:
                    flag_ple_from = False
                    if _td.text.strip() != "-":
                        vals['ple_from'] = datetime.strptime(_td.text.strip(' '), "%d/%m/%Y").strftime("%Y-%m-%d")

        # Busqueda del TELEFONO
        soup = BeautifulSoup(post.text, 'html.parser')
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        flag_temp = 0
        html_coment = ""
        for c in comments:
            if flag_temp == 1:
                html_coment = html_coment + c
            if c.find("PAS20134EA20000207") >= 0:
                flag_temp += 1
            if flag_temp == 1 and c.find("</tr>") >= 0:
                flag_temp += 1
        if flag_temp >= 2:
            newsoup = BeautifulSoup(html_coment, 'html.parser')
            table_td = newsoup.find_all('td')
            vals['phone_sunat'] = table_td[1].get_text().strip()
            vals['fax_sunat'] = table_td[3].get_text().strip()
        
        # Por Ing. Jean Paul Casis
        payload = OrderedDict()
        payload['accion'] = 'getRepLeg'
        payload['desRuc'] = vals.get('legal_name') or ''
        payload['nroRuc'] = vat
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        post = consuta.post("http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias", params=payload,headers=headers)
        if post.status_code != 200:
            return  False
        #    raise UserError(_('El servidor de consulta no está en linea, por favor reitentelo más tarde.'))
        texto_error = 'Surgieron problemas al procesar la consulta'
        texto_consulta = post.text

        if texto_error in (texto_consulta):
            return  False
        #    raise UserError(_('El servidor de consulta no responde, por favor reintentelo más tarde'))

        texto_consulta = texto_consulta.replace('<br>', '\n')
        texto_consulta = re.sub("(<!--.*?-->)", "", texto_consulta, flags=re.MULTILINE)
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(texto_consulta), parser)

        # Busqueda de datos
        reps = {}
        lista = []
        i = 0
        for _td in tree.findall("//div[@id='print']/table//td"):
            if _td.attrib:
                if _td.attrib['class'] == 'bg':
                    i+= 1
                    if i == 1:
                        reps['doc_type'] = _td.text.strip()
                    if i == 2:
                        reps['doc_number'] = _td.text.strip()
                    if i == 3:
                        reps['name'] = _td.text.strip()
                    if i == 4:
                        reps['position'] = _td.text.strip()
                    if i == 5:
                        reps['date_from'] = datetime.strptime(_td.text.strip(),'%d/%m/%Y').strftime('%Y-%m-%d')
                        i = 0

                        lista.append(reps)
                        reps = {}
                        
        vals['representatives'] = lista

        return vals

    @staticmethod
    def validate_ruc(vat):
        factor = '5432765432'
        sum = 0
        dig_check = False
        if len(vat) != 11:
            return False
        try:
            int(vat)
        except ValueError:
            return False
        for f in range(0, 10):
            sum += int(factor[f]) * int(vat[f])
        subtraction = 11 - (sum % 11)
        if subtraction == 10:
            dig_check = 0
        elif subtraction == 11:
            dig_check = 1
        else:
            dig_check = subtraction
        if not int(vat[10]) == dig_check:
            return False
        return True

    def buscar_mintra(self, nro_documento):
        str_parse = "|"
        reponse = False

        url = 'http://extranet.trabajo.gob.pe/extranet/web/citas/validarDNI'
        req = {'dni': nro_documento}
        try:
            reponse = requests.post(url, req, timeout=300)
        except Exception:
            reponse = False
        if reponse and reponse.status_code == 200 and reponse.text != "-2":
            print("respuesta:", reponse.text)
            str = reponse.text.split(str_parse)
            respuesta = {
                'detail': 'found',
                'paternal_surname': str[1],
                'maternal_surname': str[2],
                'name': str[3],
                'sexo': str[4],
                'fecha_nacimiento': str[5][:4] + '/' + str[5][4:6] + '/' + str[5][6:8]
            }
        else:
            respuesta = {'detail': "Not found."}
        return respuesta

    ##@api.multi
    def buscar_dni(self, nro_dni):
        respuesta = self.buscar_mintra(nro_dni)
        return respuesta

    # @api.model
    # def _get_pe_doc_type(self):
    #     res = []
    #     res.append(('0', 'DOC.TRIB.NO.DOM.SIN.RUC'))
    #     res.append(('1', 'DOCUMENTO NACIONAL DE IDENTIDAD (DNI)'))
    #     res.append(('4', 'CARNET DE EXTRANJERIA'))
    #     res.append(('6', 'REGISTRO ÚNICO DE CONTRIBUYENTES'))
    #     res.append(('7', 'PASAPORTE'))
    #     res.append(('A', 'CÉDULA DIPLOMÁTICA DE IDENTIDAD'))
    #     res.append(('B', 'DOC.IDENT.PAIS.RESIDENCIA-NO.D'))
    #     res.append(('C', 'Tax Identifi cation Number - TIN – Doc Trib PP.NN'))
    #     res.append(('D', 'Identifi cation Number - IN – Doc Trib PP. JJ'))
    #     res.append(('E', 'TARJETA ANDINA DE MIGRACION'))
    #     return res

    #doc_type= fields.Selection(selection=_get_pe_doc_type, string="Document Type")
    # doc_type= fields.Char( string="Document Type")
    # doc_number= fields.Char("Document Number")
    commercial_name = fields.Char("Commercial Name", default="-", help='If you do not have a commercial name, put "-" without quotes')
    legal_name = fields.Char("Legal Name", default="-", help='If you do not have a legal name, put "-" without quotes')
    
    state = fields.Selection([('ACTIVO', 'ACTIVO'),
                            ('BAJA DE OFICIO', 'BAJA DE OFICIO'),
                            ('BAJA DEFINITIVA', 'BAJA DEFINITIVA'),
                            ('BAJA PROVISIONAL', 'BAJA PROVISIONAL'),
                            ('SUSPENSION TEMPORAL', 'BAJA PROVISIONAL'),
                            ('INHABILITADO-VENT.UN', 'INHABILITADO-VENT.UN'),
                            ('BAJA MULT.INSCR. Y O', 'BAJA MULT.INSCR. Y O'),
                            ('PENDIENTE DE INI. DE', 'PENDIENTE DE INI. DE'),
                            ('OTROS OBLIGADOS', 'OTROS OBLIGADOS'),
                            ('NUM. INTERNO IDENTIF', 'NUM. INTERNO IDENTIF'),
                            ('ANUL.PROVI.-ACTO ILI', 'ANUL.PROVI.-ACTO ILI'),
                            ('ANULACION - ACTO ILI', 'ANULACION - ACTO ILI'),
                            ('BAJA PROV. POR OFICIO', 'BAJA PROV. POR OFICIO'),
                            ('ANULACION - ERROR SU', 'ANULACION - ERROR SU')], "Partner State", default="ACTIVO")
    condition = fields.Selection([('HABIDO', 'HABIDO'),
                                ('NO HABIDO', 'NO HABIDO'),
                                ('', 'NO HABIDO'),
                                ('NO HALLADO', 'NO HALLADO'),
                                ('PENDIENTE', 'PENDIENTE'),
                                ('NO HALLADO SE MUDO D', 'NO HALLADO SE MUDO D'),
                                ('NO HALLADO NO EXISTE', 'NO HALLADO NO EXISTE'),
                                ('NO HALLADO FALLECIO', 'NO HALLADO FALLECIO'),
                                ('-', 'NO HABIDO'),
                                ('NO HALLADO OTROS MOT','NO HALLADO OTROS MOT'),
                                ('NO APLICABLE', 'NO APLICABLE'),
                                ('NO HALLADO NRO.PUERT', 'NO HALLADO NRO.PUERT'),
                                ('NO HALLADO CERRADO', 'NO HALLADO CERRADO'),
                                ('POR VERIFICAR', 'POR VERIFICAR'),
                                ('NO HALLADO DESTINATA', 'NO HALLADO DESTINATA'),
                                ('NO HALLADO RECHAZADO', 'NO HALLADO RECHAZADO')], 'Condition')
    
    activities_ids = fields.Many2many("pe.datas", string= "Economic Activities", domain=[('table_code', '=', 'PE.CIIU')])
    main_activity = fields.Many2one("pe.datas", string= "Main Economic Activity", domain=[('table_code', '=', 'PE.CIIU')])
    retention_agent = fields.Boolean("Is Agent")
    retention_agent_from = fields.Date("From")
    retention_agent_resolution = fields.Char("Resolution")
    is_validate= fields.Boolean("Is Validated")
    type_taxpayer = fields.Char("Type Taxpayer")
    emission_system = fields.Char("Emission System")
    accounting_system = fields.Char("Accounting System")
    last_update = fields.Datetime("Last Update")
    representative_ids = fields.One2many("res.partner.representative", "partner_id", "Representatives")
    
    @api.constrains("vat")
    def check_doc_number(self):
        return
        for partner in self:
            if not partner.l10n_latam_identification_type_id and not partner.vat:
                continue
            elif partner.l10n_latam_identification_type_id.l10n_pe_vat_code=="0":
                continue
            elif not partner.l10n_latam_identification_type_id and partner.vat:
                raise ValidationError(_("Select a document type"))
            elif partner.l10n_latam_identification_type_id and not partner.vat:
                raise ValidationError(_("Enter the document number"))
            vat = partner.vat
            if partner.l10n_latam_identification_type_id.l10n_pe_vat_code == '6':
                check = self.validate_ruc(vat)
                if not check:
                    _logger.info("The RUC Number [%s] is not valid !" % vat)
                    raise ValidationError(_('the RUC entered is incorrect'))
            if self.search_count([('company_id','=', partner.company_id.id),
                                  ('l10n_latam_identification_type_id', '=', partner.l10n_latam_identification_type_id), ('doc_number', '=', partner.doc_number)])>1:
                raise ValidationError(_('Document Number already exists and violates unique field constrain'))

    @api.onchange('company_type')
    def onchange_company_type(self):
        res = super(Partner, self).onchange_company_type()
        it_RUC = self.env['l10n_latam.identification.type'].search([('name','=','RUC')])
        it_DNI = self.env['l10n_latam.identification.type'].search([('name','=','DNI')])
        self.l10n_latam_identification_type_id  = self.company_type == 'company' and it_RUC[0].id or it_DNI[0].id
        self.doc_number = self.vat
        return res

    def _onchange_country(self):
        res = super(Partner, self)._onchange_country()
        it_RUC = self.env['l10n_latam.identification.type'].search([('name','=','RUC')])
        it_DNI = self.env['l10n_latam.identification.type'].search([('name','=','DNI')])
        self.l10n_latam_identification_type_id  = self.company_type == 'company' and it_RUC[0].id or it_DNI[0].id
        self.doc_number = self.vat
        return res

    @staticmethod
    def validate_ruc(vat):
        factor = '5432765432'
        sum = 0
        dig_check = False
        if len(vat) != 11:
            return False
        try:
            int(vat)
        except ValueError:
            return False 
        for f in range(0,10):
            sum += int(factor[f]) * int(vat[f])
        subtraction = 11 - (sum % 11)
        if subtraction == 10:
            dig_check = 0
        elif subtraction == 11:
            dig_check = 1
        else:
            dig_check = subtraction
        if not int(vat[10]) == dig_check:
            return False
        return True
    
    # @api.onchange('doc_type','l10n_latam_identification_type_id')
    # def onchange_doc_type(self):
    #     self.doc_number = self.vat
    #     self.doc_type = self.l10n_latam_identification_type_id.l10n_pe_vat_code

    @api.onchange('vat')
    # @api.depends("doc_type", "doc_number")
    def _doc_number_change(self):
        vat = self.vat
        # self.doc_number = vat
        # self.type_doc = self.l10n_latam_identification_type_id.l10n_pe_vat_code
        if vat and self.l10n_latam_identification_type_id.l10n_pe_vat_code:
            vat_type = self.l10n_latam_identification_type_id.l10n_pe_vat_code
            if vat_type == '0':
                # self.vat="%s%s"%("PEO", self.doc_number)
                pass
            elif vat_type == '1':
                # if len(vat)!=8:
                #     raise UserError(
                #             _('the DNI entered is incorrect'))
                # try:
                #     response = requests.get("http://api.flexxoone.com/dni/%s/" % vat.strip(), timeout = 300)
                # except Exception:
                #     reponse=False
                # if response and response.status_code!=200:
                #     vals= {'detail':"Not found."}
                # else:
                #     vals = response and response.json() or {'detail':"Not found."}
                if len(vat) != 8:
                    raise UserError(
                        _('the DNI entered is incorrect'))
                self.update_dni_fx()
                # respuesta = self.buscar_dni(self.vat.strip())
                # if respuesta and respuesta['detail'] != 'Not found.':
                #     self.name = "%s %s %s" % ((respuesta['paternal_surname'] or ''),
                #                               (respuesta['maternal_surname'] or ''),
                #                               (respuesta['name'] or ''))
                #     self.name_p = respuesta['name'] or ''
                #     self.last_name = respuesta['paternal_surname'] or ''
                #     self.m_last_name = respuesta['maternal_surname'] or ''
                #     self.company_type = "person"
                #     self.is_validate = True
                    # self.vat = "%s%s" % ("PED", vat)
                # else:
                #     raise UserError(_('El Numero de DNI ingresado es incorrecto o no existe'))
            elif vat_type == '4':
                # self.vat="%s%s"%("PEE", self.doc_number)
                pass
            elif vat_type=="6":
                # if not self.validate_ruc(vat):
                #     raise UserError(
                #             _('the RUC entered is incorrect'))
                # try:
                #     if self.env.context.get('force_update'):
                #         response = requests.get("http://api.flexxoone.com/ruc/%s/?force_update=1" % vat.strip())
                #     else:
                #         response = requests.get("http://api.flexxoone.com/ruc/%s/" % vat.strip())
                # except Exception:
                #     reponse=False
                # vals = self._get_sunat_details(vat)
                # if vals == False:
                # vals = self.update_sunat_api_itgrupo()
                self.update_sunat_api_fx()
                # print('vals:', vals)
                #if response and response.status_code!=200:
                #    vals= self._get_sunat_details(vat)
                #else:
                #vals = response and response.json() or {'detail':"Not found."}
                #    if vals.get('detail', '') == "Not found.":
                #        vals= self._get_sunat_details(vat)
#             if vals:
#                 self.commercial_name = vals.get('commercial_name')
#                 self.legal_name = vals.get('legal_name')
#                 self.name = vals.get('legal_name') or  vals.get('legal_name')
#                 self.street = vals.get('street', False)
#                 #if vals.get('street', False).lstrip() != '':
#                 #    self.street = vals.get('street', False).lstrip() 
#                 self.company_type="company"
#                 self.state = vals.get('state', False)
#                 self.condition = vals.get('condition')
#                 self.type_taxpayer = vals.get('type_taxpayer')
#                 self.emission_system = vals.get('emission_system')
#                 self.accounting_system = vals.get('accounting_system')
#                # self.last_update = vals.get('last_update') and fields.Datetime.context_timestamp(self, datetime.strptime(vals.get('last_update'), '%Y-%m-%dT%H:%M:%S.%fZ')) or False
#                 self.is_validate = True
#                 if vals.get('activities'):
#                     activities_ids = []
#                     for activity in  vals.get('activities'):
#                         ciiu = self.env['pe.datas'].search([('code', '=', activity.get('code')),('table_code', '=', 'PE.CIIU')], limit=1)
#                         if ciiu:
#                             activities_ids.append(ciiu.id)
#                         else:
#                             activity['table_code']='PE.CIIU'
#                             ciiu = self.env['pe.datas'].sudo().create(activity)
#                             activities_ids.append(ciiu.id)
#                     if activities_ids:
#                         self.main_activity = activities_ids[-1]
#                         if self.activities_ids:
#                             self.activities_ids = [(6, None, activities_ids)]
#                         else:
#                             act=[]
#                             for activity_id in activities_ids:
#                                 act.append((4,activity_id))
#                             self.activities_ids = act
#                 if vals.get('representatives') and self.is_company:
#                     representatives=[]
#                     for rep in vals.get('representatives'):
#                         representatives.append((0, None,rep))
#                         if rep.get('position', '') in ["GERENTE GENERAL", "TITULAR-GERENTE", "GERENTE"]:
#                            contact={}
#                            contact['name']= rep.get('name')
#                            if self.search_count([('name', '=', contact['name']), ('parent_id', '=', self.id)]) == 0:
#                                contact['function']=rep.get('position')
#                                contact['type']='contact'
#                                contact['parent_id']=self.id
#                                contact['display_name']=self.name + ', ' + contact['name']
#                                contact['is_company']=False
#                                contact['commercial_partner_id']=self.id
#                                contact['commercial_company_name']=self.name
#                                #child_id=self.create(contact)
#                                self.child_ids=[(0, None, contact)]
#                     if self.representative_ids:
#                         self.representative_ids.unlink()
#                     self.representative_ids = representatives
#                 self.retention_agent = vals.get('retention_agent', False)
#                 self.retention_agent_from = vals.get('retention_agent_from', False)
#                 self.retention_agent_resolution = vals.get('retention_agent_resolution', False)
#                 if vals.get('district') and vals.get('province'):
#                     district = self.env['l10n_pe.res.city.district'].search([('name','=ilike', vals.get('district')),
#                                                                            ('city_id.name','ilike', vals.get('province'))])
#                     if len(district)==1:
#                         self.country_id = district.city_id.state_id.country_id
#                         self.state_id = district.city_id.state_id
#                         self.city_id = district.city_id
#                         self.l10n_pe_district = district
#                     # ITGRUPO
#                     district2 = self.env['res.country.state'].search([('name','=ilike', vals.get('district')),
#                                                                            ('province_id','ilike', vals.get('province'))])
#                     if len(district2)==1:
#                         self.state_id = district2.state_id
#                         self.province_id = district2.province_id
#                         self.district_id = district2
                        
#                     # elif len(district)==0:
#                     #     province = self.env['res.country.province'].search([('name','ilike', vals.get('province'))])
#                     #     if len(province)==1:
#                     #         self.city_id = province
#                     # else:
#                     #     province = self.env['res.country.province'].search([('name','ilike', vals.get('province'))])
#                     #     if len(province)==1:
#                     #         self.city_id = province
#                 if vals.get('ubigeo'):
#                     district2 = self.env['res.country.state'].search([('code','=', vals.get('ubigeo'))])
#                     if len(district2)==1:
#                         self.state_id = district2.state_id
#                         self.province_id = district2.province_id
#                         self.district_id = district2
                        
#             # self.vat= "PER%s"% vat

#             # self.vat = vat

#         elif vat_type == '7':
#             prefix="CC"
#             if self.country_id:
#                 prefix=self.country_id.code
#             # self.vat="%s%s"%(prefix, self.doc_number)
#         # elif vat_type == 'A':
#             # self.vat="%s%s"%("PEA", self.doc_number)
#         # elif vat_type == 'B':
#             # self.vat="%s%s"%("PEB", self.doc_number)
#         # elif vat_type == 'C':
#             # self.vat="%s%s"%("PEC", self.doc_number)
#         # elif vat_type == 'D':
#             # self.vat="%s%s"%("PEI", self.doc_number)
    
#     # print('************SUNAT***********')
#     # print('****************************')
#     # print(self.zip)
#     # print('****************************')
#     # print('****************************')

# # @api.onchange('vat')
# # def _vat_change(self):
# #     if self.vat:
# #         prefix= "PE" #len(self.vat)>=2 and self.vat[0:2] or False
# #         vat = self.vat #len(self.vat)>=2 and self.vat[2:] or ""
# #         # if prefix:
# #         #     if not self.country_id:
# #         #         country_id=self.env['res.country'].search([("code","=", prefix.upper())], limit=1)
# #         #         self.country_id=country_id.id
# #         if prefix and prefix.upper()== "PE": 
# #             doc_type = len(vat)>0 and vat[0:1] or False
# #             doc_number = vat #len(vat)>0 and vat[1:] or False
# #             if doc_type and doc_type.upper()=="O":
# #                 self.doc_type="0"
# #             elif doc_type and doc_type.upper()=="D":
# #                 if len(doc_number)!=8:
# #                         raise UserError(_('El número de DNI ingresado es incorrecto'))
# #                 self.doc_type="1"
# #             elif doc_type and doc_type.upper()=="E":
# #                 self.doc_type="4"
# #             elif doc_type and doc_type.upper()=="R":
# #                 if not self.validate_ruc(doc_number):
# #                         raise UserError(_('El número de DNI ingresado es incorrecto'))
# #                 self.doc_type="6"
# #             elif doc_type and doc_type.upper()=="A":
# #                 self.doc_type="A"
# #             if self.doc_number != doc_number:    
# #                 self.doc_number = doc_number
# #         else:
# #             self.doc_type="7"
# #             if self.doc_number != vat:
# #                 self.doc_number = vat

    def check_vat_pe(self, vat):
        vat_type, doc = vat and len(vat) >= 2 and (vat[0], vat[1:]) or (False, False)
        if vat_type.upper() in ['A', 'O', 'E', 'B', 'C', 'D', 'I']:
            return True
        return super(Partner, self).check_vat_pe(vat)    

    ##@api.multi
    def change_commercial_name(self):
        partner_ids=self.search([('commercial_name', '!=', '-'), ('l10n_latam_identification_type_id.l10n_pe_vat_code', '=', '6')])
        for partner_id in partner_ids:
            partner_id.update_document()

    ##@api.one
    def update_document(self):
        self._doc_number_change()
        # self._vat_change()

    @api.model
    def update_partner_datas(self):
        partner_ids = self.search([('l10n_latam_identification_type_id.l10n_pe_vat_code', '=', '6')])
        for partner in partner_ids:
            partner.name = partner.commercial_name
    
    @api.model
    def _commercial_fields(self):
        res = super(Partner, self)._commercial_fields()
        del res[res.index('vat')]
        del res[res.index('l10n_latam_identification_type_id')]
        return res
    #Ing Jose           
    def update_sunat_api(self):
        print('Api Sunat Secundaria')
        vals= {}
	#SFR
        #r = requests.get('https://apii.sistemerp.com/api/ruc/'+ str(self.doc_number))
        r = requests.get('https://api.sistemerp.com/ruc/'+ str(self.vat))
        if r.status_code:
            r = r.json()
            return r
        else:
            raise UserError(_('El servidor de consulta no está en linea, por favor reitentelo más tarde.'))
     ################################### 
    
    #Ing Jean Paul
    # def update_sunat_api_itgrupo(self):
    #     print('Api Sunat Secundaria ITgrupo')
    #     client = Client('http://ws.insite.pe/sunat/ruc.php?wsdl', faults = False, cachingpolicy = 1, location = 'http://ws.insite.pe/sunat/ruc.php?wsdl')
    #     try: 
    #         result = client.service.consultaRUC(str(self.vat),'jtejada@itgrupo.net','ZDI-9DJ-YA8-D8C','plain')
    #         texto = result[1].split('|')
    #         flag = False
    #         for i in texto:
    #             tmp = i.split('=')
    #             if tmp[0] == 'status_id' and tmp[1] == '1':
    #                 flag = True

    #         if flag:
    #             for j in texto:
    #                 tmp = j.split('=')
    #                 if tmp[0] == 'n1_alias':
    #                     self.name = tmp[1]
    #                 if tmp[0] == 'n1_direccion':
    #                     if tmp[1] != '-':
    #                         self.street = tmp[1]
    #                 if tmp[0] == 'n1_ubigeo':
    #                     ubi_t = tmp[1]
    #                     ubigeo = self.env['res.country.state'].search([('code','=',ubi_t)])

    #                     if ubigeo:
    #                         self.zip = tmp[1]
    #                         pais = self.env['res.country'].search([('code','=','PE')]) 
    #                         ubidepa = ubi_t[0:2]
    #                         ubiprov = ubi_t[0:4]
    #                         ubidist = ubi_t[0:6]

    #                         departamento = self.env['res.country.state'].search([('code','=',ubidepa),('country_id','=',pais.id)])
    #                         provincia  = self.env['res.country.state'].search([('code','=',ubiprov),('country_id','=',pais.id)])
    #                         distrito = self.env['res.country.state'].search([('code','=',ubidist),('country_id','=',pais.id)])

    #                         self.country_id = pais.id
    #                         self.state_id = departamento.id
    #                         self.province_id = provincia.id
    #                         self.district_id = distrito.id
    #                 if tmp[0] == 'n1_estado':
    #                     self.state = tmp[1]
    #                 if tmp[0] == 'n1_condicion':
    #                     self.condition = tmp[1]
    #     except Exception as e:
    #         raise UserError('No se encontro el RUC')
    #     return result
    def update_sunat_api_fx(self):
        #Nueva funcion para obtener el ruc 

        # fx_token_api = 'tboHRj_N1-BdommnFT0J6QEFMyc'
        # try:
        #     url ='https://consulta.sistemerp.com/api?ruc=%s&token=%s' % (self.vat, fx_token_api)
        #     result = requests.get(url)
        # except Exception as e:
        #     raise UserError('No se encontro el RUC')

        try:
            if self.env.context.get('force_update'):
                response = requests.get("http://api.grupoyacck.com/ruc/%s/?force_update=1" % self.vat.strip())
            else:
                response = requests.get("http://api.grupoyacck.com/ruc/%s/" % self.vat.strip())
        except Exception as msg:
            return UserError(msg)
        
        json_Response = response and response.json() or {'detail':"Not found."}
        if json_Response.get('detail', '') == "Not found.":
            raise UserError("No se pudo obtener la información del RUC")
        if not json_Response:
            return UserError("Vat no encontrado")
        

        if 'error' in json_Response:
            raise UserError('Error: %s'%json_Response['error'])
        if 'legal_name' in json_Response:
            self.name = json_Response['legal_name'].strip()
            self.name = self.name.replace("'", "")
        if 'state' in json_Response:
            self.state = json_Response['state']
        if 'condition' in json_Response:
            self.condition = json_Response['condition']

        pais = self.env['res.country'].search([('code','=','PE')])
        if 'street' in json_Response:
            self.street = json_Response['street']
        if pais:
            self.country_id = pais.id
        if 'ubigeo' in json_Response:
            district = self.env['l10n_pe.res.city.district'].search([('code','=', "%s" % json_Response['ubigeo'])],limit=1)
            self.l10n_pe_district=district and district.id or False
            self.state_id = district and district.city_id.state_id or False
            self.country_id = district and district.city_id.country_id or False
            self.city_id = district and district.city_id or False
            # self.state_id = self._get_l10n_pe_datas(json_Response['departamento']).id
            # self.province_id = self._get_l10n_pe_datas(json_Response['provincia']).id
            # self.district_id = self._get_l10n_pe_datas(json_Response['distrito']).id 
        
        return json_Response

    # def _get_l10n_pe_datas(self, res_ctry_state_name):
    #     res_ctry_state = self.env['res.country.state'].search(
    #         [('name', 'in', [res_ctry_state_name, res_ctry_state_name.upper(), res_ctry_state_name.lower()])], limit=1)
    #     return res_ctry_state

    # def update_dni_itgrupo(self):
    #     if not self.vat:
    #         raise UserError("Debe seleccionar un DNI")
    #     client = Client('http://reniec.insite.pe/?wsdl', faults = False, cachingpolicy = 1, location = 'http://reniec.insite.pe/?wsdl')
    #     try: 
    #         result = client.service.consultar(str(self.vat),'jtejada@itgrupo.net','ZDI-9DJ-YA8-D8C','plain')
    #     except Exception as e:
    #         raise UserError('No se encontro el DNI')
    #     texto = result[1].split('|')
    #     flag = False
    #     nombres = ''
    #     a_paterno = ''
    #     a_materno = ''
    #     for c in texto:
    #         tmp = c.split('=')
    #         if tmp[0] == 'status_id' and tmp[1] == '102':
    #             raise UserError('El DNI debe tener al menos 8 digitos de longitud')
    #         if tmp[0] == 'status_id' and tmp[1] == '103':
    #             raise UserError('El DNI debe ser un valor numerico')
    #         if tmp[0] == 'reniec_nombres' and tmp[1] != '':
    #             nombres = tmp[1]
    #             self.name_p = tmp[1]
    #         if tmp[0] == 'reniec_paterno' and tmp[1] != '':
    #             a_paterno = tmp[1]
    #             self.last_name = tmp[1]
    #         if tmp[0] == 'reniec_materno' and tmp[1] != '':
    #             a_materno = tmp[1]
    #             self.m_last_name = tmp[1]
    #     self.name = (nombres + " " + a_paterno + " " + a_materno).strip()

    def update_dni_fx(self):
        #Nueva funcion para obtener el dni
        if not self.vat:
            raise UserError("Debe seleccionar un DNI")
        # fx_token_api = 'tboHRj_N1-BdommnFT0J6QEFMyc'
        # try:
        #     url ='https://consulta.sistemerp.com/api?dni=%s&token=%s' % (self.vat, fx_token_api)
        #     result = requests.get(url)
        # except Exception as e:
        #     raise UserError('No se encontro el DNI')

        try:
            response = requests.get("http://api.grupoyacck.com/dni/%s/" % self.vat.strip())
        except Exception as msg:
            return UserError(msg)
        
        if response and response.status_code!=200:
            return UserError("DNI no encontrado")
        

        response = response and response.json()

        if 'error' in response:
            raise UserError('Error: %s'%response['error'])
        
        name_p = response.get('name','')
        last_name = response.get('paternal_surname','')
        m_last_name = response.get('maternal_surname','')

        self.name_p = name_p
        self.last_name = last_name
        self.m_last_name = m_last_name
        self.name = (name_p + " " + last_name + " " + m_last_name).strip()
        


class PartnerRepresentative(models.Model):
    _name = "res.partner.representative"
    _description = 'Partner Representative'
    
    name = fields.Char("Name")
    doc_type = fields.Char("Document Type")
    doc_number = fields.Char("Document Number")
    position = fields.Char("Position")
    date_from = fields.Date("Date From")
    partner_id = fields.Many2one("res.partner", "Partner")
    
    
