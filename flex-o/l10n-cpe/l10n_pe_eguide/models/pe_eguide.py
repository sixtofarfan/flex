# -*- coding: utf-8 -*-
from .eguide import get_document, get_sign_document, send_sunat_eguide, get_response, get_ticket_status, get_status_cdr
from base64 import b64decode, b64encode
from lxml import etree
from datetime import datetime
from odoo import models, api, fields
import json
import requests
from odoo.exceptions import UserError
from hashlib import sha256
import urllib3
import base64
from pytz import timezone


class PeSunatEguide(models.Model):
    _name = 'pe.eguide'
    _description = 'Guide Electronic'

    name = fields.Char("Name", readonly=True, default="/")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('generate', 'Generated'),
        ('send', 'Send'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)
    type = fields.Selection([
        ('sync', 'Synchronous'),
        ('low', 'Low communication'),
    ], string="Type", default='sync', states={'draft': [('readonly', False)]})
    date = fields.Date("Date", default=fields.Date.context_today, states={
        'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('pe.eguide'))
    xml_document = fields.Text("XML Document")
    datas = fields.Binary("XML Data", readonly=True)
    datas_fname = fields.Char("XML File Name", readonly=True)
    datas_sign = fields.Binary("XML Sign Data", readonly=True)
    datas_sign_fname = fields.Char("XML Sign File Name", readonly=True)
    datas_zip = fields.Binary("XML Zip Data", readonly=True)
    datas_zip_fname = fields.Char("XML Zip File Name", readonly=True)
    datas_response = fields.Binary("XML Response Data", readonly=True)
    datas_response_fname = fields.Char("XML Response File Name", readonly=True)
    response = fields.Char("Response", readonly=True)
    response_code = fields.Char("Response Code", readonly=True)
    note = fields.Text("Note", readonly=True)
    error_code = fields.Selection(
        "_get_error_code", string="Error Code", readonly=True)
    digest = fields.Char("Digest", readonly=True)
    signature = fields.Text("Signature", readonly=True)
    ticket = fields.Char("Ticket")
    date_end = fields.Datetime("End Date")
    send_date = fields.Datetime("Send Date")
    voided_ids = fields.One2many(
        "stock.picking", "pe_voided_id", string="Eguide Canceled")
    picking_ids = fields.One2many(
        "stock.picking", "pe_guide_id", string="Eguide")

    gre_reception_date = fields.Datetime(string='Fecha de recepción SUNAT', readonly=True)
    response_code = fields.Selection([('98', 'Envio en proceso'),
                                      ('99', 'Envio con error'),
                                      ('0', 'Envio OK')],
                                     string='Código de Respuesta', readonly=True)
    error_number = fields.Char(string="Número Error", readonly=True)
    error_description = fields.Char(string="Descripción Error", readonly=True)
    acr_cdr = fields.Text(string='acrCdr', readonly=True)
    id_cdr_generated = fields.Selection([('1', '1'), ('0', '0')], string='Ind Cdr Generado', readonly=True)

    _order = 'date desc, name desc'

    @api.model
    def _get_error_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.ERROR")

    @api.model
    def action_draft(self):
        if not self.xml_document and self.type == "sync":
            self._prepare_eguide()
        self.state = 'draft'

    def action_generate(self):
        if not self.xml_document and self.type == "sync":
            self._prepare_eguide()
            self._sign_eguide()
        # else:
        #    self._sign_eguide()
        self.state = 'generate'

    def action_send(self):
        state = self.send_eguide()
        self.state = state

    def action_verify(self):
        self.state = 'verify'

    def action_done(self):
        if self.ticket:
            status = self.get_sunat_ticket_status()
            if status:
                self.state = status
        else:
            self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    @api.model
    def create_from_stock(self, picking_id):
        vals = {}
        vals['picking_ids'] = [(4, picking_id.id)]
        vals['type'] = 'sync'
        vals['company_id'] = picking_id.company_id.id
        res = self.create(vals)
        return res

    @api.model
    def get_eguide_async(self, type, picking_id):
        res = None
        eguide_id = self.search([('state', '=', 'draft'), ('type', '=', type), ('date', '=', picking_id.pe_date_issue),
                                 ('name', '=', "/"), ('company_id', '=', picking_id.company_id.id)], limit=1,
                                order="date DESC")
        if eguide_id:
            res = eguide_id
        else:
            vals = {}
            vals['type'] = type
            vals['company_id'] = picking_id.company_id.id
            vals['date'] = picking_id.pe_date_issue
            res = self.create(vals)
        return res

    @api.model
    def get_document_name(self):
        self.ensure_one()
        ruc = self.company_id.partner_id.vat
        if self.type == "sync":
            doc_code = "-%s" % "09"
            number = self.picking_ids[0].pe_guide_number
        else:
            doc_code = "-%s" % "09"
            number = self.name
        return "%s%s-%s" % (ruc, doc_code, number)

    @api.model
    def prepare_sunat_auth(self):
        self.ensure_one()
        res = {}
        res['ruc'] = self.company_id.partner_id.vat
        res['username'] = self.company_id.pe_eguide_server_id.user
        res['password'] = self.company_id.pe_eguide_server_id.password
        res['url'] = self.company_id.pe_eguide_server_id.url
        return res

    @api.model
    def _prepare_eguide(self):
        if not self.xml_document and self.type != "low":
            file_name = self.get_document_name()
            xml_document = get_document(self)
            self.xml_document = xml_document
            self.datas = b64encode(xml_document)
            self.datas_fname = file_name + ".xml"

    def _sign_eguide(self):
        file_name = self.get_document_name()
        if not self.xml_document:
            self._prepare_eguide()
        elif self.xml_document.encode('utf-8') != b64decode(self.datas):
            self.datas = b64encode(self.xml_document.encode('utf-8'))
        key = self.company_id.pe_certificate_id.key
        crt = self.company_id.pe_certificate_id.crt
        self.datas_sign = b64encode(
            get_sign_document(self.xml_document, key, crt))
        self.datas_sign_fname = file_name + ".xml"
        self.get_sign_details()

    def send_eguide(self):
        self.ensure_one()
        file_name = self.get_document_name()
        # Odoo almacena los Datetime en UTC y los convierte a la tz del usuario al
        # mostrarlos: aplicar context_timestamp aqui causaba una doble conversion,
        # por lo que la fecha de envio se veia 5h antes de la hora real.
        self.send_date = fields.Datetime.now()
        if self.name == "/" and self.type != "low":
            self.name = self.picking_ids[0].pe_guide_number
        else:
            if self.name == "/":
                self.name = self.env['ir.sequence'].next_by_code(
                    'pe.eguide.cancel')
            file_name = self.get_document_name()
            xml_document = get_document(self)
            self.xml_document = xml_document
            self.datas = b64encode(xml_document)
            self.datas_fname = file_name + ".xml"
            self._sign_eguide()
        if self.xml_document.encode('utf-8') != b64decode(self.datas):
            self._sign_eguide()

        client = self.prepare_sunat_auth()
        document = {}
        document['document_name'] = file_name
        document['type'] = self.type
        document['xml'] = b64decode(self.datas_sign)
        self.datas_zip, response_status, response, response_data = send_sunat_eguide(
            client, document)
        self.datas_zip_fname = file_name + ".zip"
        res = None
        if response_status:
            res = "verify"
            if self.type == "sync":
                self.datas_response = response_data
                new_state = self.get_response_details()
                self.datas_response_fname = 'R-%s.zip' % file_name
                res = new_state or res
            else:
                self.ticket = response_data
        else:
            res = "send"
            self.response = response.get("faultcode")
            self.note = response.get("faultstring")
            if response.get("faultcode"):
                code = len(response.get("faultcode").split(".")) >= 2 and "%04d" % int(
                    response.get("faultcode").split(".")[-1].encode('utf-8')) or False
                self.response_code = code
            # self.error_code= code
        return res

    @api.model
    def get_sign_details(self):
        self.ensure_one()
        vals = {}
        tag = etree.QName('http://www.w3.org/2000/09/xmldsig#', 'DigestValue')
        xml_sign = b64decode(self.datas_sign)
        digest = etree.fromstring(xml_sign).find('.//' + tag.text)
        if digest != -1:
            self.digest = digest.text
        tag = etree.QName(
            'http://www.w3.org/2000/09/xmldsig#', 'SignatureValue')
        sign = etree.fromstring(xml_sign).find('.//' + tag.text)
        if sign != -1:
            self.signature = sign.text

    @api.model
    @api.depends('datas_response')
    def get_response_details(self):
        self.ensure_one()
        vals = {}
        state = None
        file_name = self.get_document_name()
        xml_response = get_response(
            {'file': self.datas_response, 'name': 'R-%s.xml' % file_name})
        sunat_response = etree.fromstring(xml_response)
        cbc = 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        tag = etree.QName(cbc, 'ResponseDate')
        date = sunat_response.find('.//' + tag.text)
        tag = etree.QName(cbc, 'ResponseTime')
        time = sunat_response.find('.//' + tag.text)
        if time != -1 and date != -1:
            # fields.Datetime.context_timestamp(self, datetime.now())
            self.date_end = date.text + ' ' + time.text
        tag = etree.QName(cbc, 'ResponseCode')
        code = sunat_response.find('.//' + tag.text)
        res_code = ""
        if code != -1:
            res_code = "%04d" % int(code.text)
            self.response_code = res_code
            if res_code == "0000":
                self.error_code = False
                state = "done"
        tag = etree.QName(cbc, 'Description')
        description = sunat_response.find('.//' + tag.text)
        res_desc = ""
        if description != -1:
            res_desc = description.text
        self.response = "%s - %s" % (res_code, res_desc)
        notes = sunat_response.xpath(".//cbc:Note", namespaces={
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        res_note = ""
        for note in notes:
            res_note += note.text
        self.note = res_note
        return state

    def generate_eguide(self):
        self._prepare_eguide()
        self._sign_eguide()
        self.state = "generate"

    @api.model
    def get_sunat_ticket_status(self):
        self.ensure_one()
        client = self.prepare_sunat_auth()
        response_status, response, response_file = get_ticket_status(
            self.ticket, client)
        state = None
        if response_status:
            file_name = self.get_document_name()
            self.datas_response = response_file
            self.datas_response_fname = 'R-%s.zip' % file_name
            state = self.get_response_details()
        else:
            res = "send"
            self.response = response.get("faultcode")
            self.note = response.get("faultstring")
            code = len(response.get("faultcode").split(".")) >= 2 and "%04d" % int(
                response.get("faultcode").split(".")[-1].encode('utf-8')) or False
            self.error_code = code
        return state

    def action_document_status(self):
        client = self.prepare_sunat_auth()
        name = self.get_document_name()
        response_status, response, response_file = get_status_cdr(name, client)
        state = None
        if response_status:
            self.note = "%s - %s" % (response['statusCdr'].get(
                'statusCode', ""), response['statusCdr'].get('statusMessage', ""))
            if response_file:
                self.datas_response = response_file
                self.datas_response_fname = 'R-%s.zip' % name
                state = self.get_response_details()
        else:
            self.response = response.get("faultcode")
            self.note = response.get("faultstring") or str(response)
            code = len(response.get("faultcode").split(".")) >= 2 and "%04d" % int(
                response.get("faultcode").split(".")[-1].encode('utf-8')) or False
            self.error_code = code

    # URO metodo para enviar la GRE por API REST
    def send_eguide_apirest(self):
        access_token = self.generate_token_api_rest()
        url = self.company_id.pe_eguide_server_id.url
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer %s' % access_token
        }
        numRucEmisor = self.company_id.vat
        codCpe = '09'
        if len(self.picking_ids) != 0:
            picking = self.picking_ids[0]
        if not picking:
            raise UserError('Esta GRE no está asignada a un Movimiento de Almacén.')
        pe_guide_number = picking.pe_guide_number.split('-')
        if len(pe_guide_number) != 2:
            raise UserError('Error en el número de serie de la Guía.')
        numSerie = pe_guide_number[0]
        numCpe = pe_guide_number[1]
        url_complete = url % (numRucEmisor, codCpe, numSerie, numCpe)
        nomArchivo = self.get_document_name() + ".zip"
        arcGreZip = self.datas_zip
        hashZip = sha256(b64decode(self.datas_zip)).hexdigest()
        datas = {
            "archivo":
                {"nomArchivo": nomArchivo,
                 "arcGreZip": arcGreZip.decode('UTF-8'),
                 "hashZip": hashZip}
        }
        http = urllib3.PoolManager()
        try:
            print('URL envio: ', url_complete)
            print('Headers: ', headers)
            print('Body: ', datas)
            r = http.request('POST',
                             url_complete,
                             headers=headers,
                             body=json.dumps(datas))
        except urllib3.exceptions.HTTPError as e:
            raise UserError("Error al intentar conectarse: \n\t %s" % e.reason)
        if r.status != 200:
            raise UserError("Error: %s - %s" % (r.status,r.reason))
        response = json.loads(r.data.decode('utf-8'))
        print('Response: ', response)
        if 'numTicket' in response and 'fecRecepcion' in response:
            self.ticket = response['numTicket']
            self.response = 'El Comprobante número %s, ha sido enviado.' % picking.pe_guide_number
            # DatetImeObj = datetime.strptime(response['fecRecepcion'], '%Y-%m-%dT%H:%M:%S.%fZ')
            DatetImeObj = datetime.strptime(response['fecRecepcion'], '%Y-%m-%dT%H:%M:%S')
            # SUNAT devuelve fecRecepcion en hora de Peru y Odoo almacena en UTC.
            # convert_TZ_to_USER no convertia nada (formatea y reparsea), asi que
            # la hora quedaba guardada en local y se mostraba 5h antes de la real.
            _tz = timezone(self.env.user.tz or 'America/Lima')
            DatetImeObj = _tz.localize(DatetImeObj).astimezone(
                timezone('UTC')).replace(tzinfo=None)
            self.date_end = fields.Datetime.now()
            self.gre_reception_date = DatetImeObj
            self.get_eguide_apirest()
            self.state = 'done'
        else:
            raise UserError('Ocurrió un error, Respuesta: %s' % response)

    def generate_token_api_rest(self):
        vat = self.company_id.vat
        id_sunat = self.company_id.pe_eguide_server_id.id_sunat
        clave_sunat = self.company_id.pe_eguide_server_id.clave_sunat
        url_token = self.company_id.pe_eguide_server_id.url_token % id_sunat
        scope = self.company_id.pe_eguide_server_id.scope
        user = self.company_id.pe_eguide_server_id.user
        password = self.company_id.pe_eguide_server_id.password
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
        }
        datas = {
            'grant_type': 'password',
            'client_id': id_sunat,
            'client_secret': clave_sunat,
            'username': vat + user,
            'password': password,
            'scope': scope,

        }
        r = requests.post(url_token,
                          data=datas, headers=headers)
        try:
            validate = r.json()
        except Exception as err:
            raise UserError(r.text)
        if validate:
            if 'access_token' in validate:
                print('TOKEN GENERADO: ', validate['access_token'])
                return validate['access_token']
            else:
                raise UserError(
                    'No fue posible generar el token, revise su configuración. Respuesta: %s' % validate)
        else:
            raise UserError('No fue posible generar el token, revise su configuración.')

    def convert_TZ_to_USER(self, TZ_datetime):
        fmt = "%Y-%m-%d %H:%M:%S"
        local_datetime = datetime.strptime(str(TZ_datetime.strftime(fmt)), fmt)
        return local_datetime

    # URO metodo para consultar la GRE
    def get_eguide_apirest(self):
        access_token = self.generate_token_api_rest()
        url = self.company_id.pe_eguide_server_id.url_consult % self.ticket
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer %s' % access_token
        }
        http = urllib3.PoolManager()
        try:
            r = http.request('GET',
                             url,
                             headers=headers)

        except urllib3.exceptions.HTTPError as e:
            raise UserError("Error al intentar conectarse: \n\t %s" % e.reason)
        response = json.loads(r.data.decode('utf-8'))
        if response:
            if 'codRespuesta' in response:
                self.response_code = response['codRespuesta']
                if response['codRespuesta'] == '99':
                    if 'error' in response:
                        if 'numError' in response['error']:
                            self.error_number = response['error']['numError']
                        if 'desError' in response['error']:
                            self.error_description = response['error']['desError']
                if 'arcCdr' in response:
                    self.acr_cdr = response['arcCdr']
                    self._generate_zip_datas_response(response['arcCdr'])
                if 'indCdrGenerado' in response:
                    self.id_cdr_generated = response['indCdrGenerado']
        else:
            raise UserError('Ocurrió un error, Respuesta: %s' % response)
        return True

    def _generate_zip_datas_response(self, arcCdr):
        self.datas_response = arcCdr
        self.datas_response_fname = f'''R-{self.company_id.vat}-09-{self.name}.zip'''
        return True
