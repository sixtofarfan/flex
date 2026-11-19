# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class ContractMainParameter(models.Model):
	_name = 'contract.main.parameter'
	_description = 'Contract Main Parameter'

	name = fields.Char(default="Parametros Principales")
	company_id = fields.Many2one('res.company', string=u'Compañía', default=lambda self: self.env.company.id)
	manager_id = fields.Many2one('res.partner', string='Gerente General')
	proxies_ids = fields.Many2many('res.partner', 'contract_partner_default_rel', string='Apoderados')
	electronic_doc = fields.Char(string='Partida Electronica')
	company_slogan = fields.Char(string='Denominacion para Compañia')
	client_slogan = fields.Char(string='Denominacion para Cliente')
	resolution = fields.Char(string='Resolucion', default='138-2012-CD/OSIPTEL')
	anticipated_hours = fields.Integer(string='Horas minimas de Antelacion')
	organism = fields.Char(string='Organismo Regulador', default='OSIPTEL')
	article = fields.Char(string='Condiciones de Uso', default=u'artículo 75°')
	articles = fields.Char(string='Condiciones de Uso de Sevicios Publicos de Telecomunicaciones', default=u'artículos 76° y 77°')
	law = fields.Char(string='Ley de Protección de Datos Personales', default='29733')
	approver = fields.Char(string='Aprobador de Ley de Proteccion', default='D.S. 003.2013-JUS')
	law2 = fields.Char(string='Ley de bloqueo de contenido pornografico', default='30254')
	capital_percent = fields.Float(string='Porcentaje Lima', default=99.50)
	province_percent = fields.Float(string='Porcentaje Provincia', default=98.50)
	formula = fields.Char(string='Formula', default='((TM x tiempo de la averia)/(24 x 60 x dias del mes de la averia))((FA)t/(FA)t-n)')
	var_lines = fields.One2many('formula.variables.line', 'parameter_id')
	support = fields.Char(string='Área Especializada de Soporte Técnico', default='NOC, SOC o Telefonía')
	monitoring = fields.Char(string='Monitoreo', default='opera las 24 horas por 7 días a la semana y 365 días por año (24 x 7)')
	service_lines = fields.One2many('service.information.line', 'parameter_id')
	contact_lines = fields.One2many('contact.support.line', 'parameter_id')
	escalation_lines = fields.One2many('escalation.level.line', 'parameter_id')
	phone_lines = fields.One2many('contact.phone.line', 'parameter_id')
	glossary_lines = fields.One2many('glossary.line', 'parameter_id')

	@api.model
	def create(self,vals):
		if len(self.search([('company_id', '=', self.env.company.id)])) > 0:
			raise UserError(u'No se puede crear mas de un Parametro Principal por Compañía')
		return super(ContractMainParameter,self).create(vals)

	def get_main_parameter(self):
		MainParameter = self.search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter:
			raise UserError('No se ha creado Parametros Generales para esta compañia')
		return MainParameter

	def check_voucher_values(self):
		if not self.manager_id or \
		   not self.proxies_ids or \
		   not self.electronic_doc or\
		   not self.company_slogan or \
		   not self.client_slogan or \
		   not self.resolution or \
		   not self.anticipated_hours or \
		   not self.organism or \
		   not self.article or \
		   not self.articles or \
		   not self.law or \
		   not self.approver or \
		   not self.law2 or \
		   not self.capital_percent or \
		   not self.province_percent or \
		   not self.formula or \
		   not self.var_lines or \
		   not self.support or \
		   not self.monitoring or \
		   not self.service_lines or \
		   not self.escalation_lines or \
		   not self.phone_lines or \
		   not self.glossary_lines:
		   raise UserError(u'Faltan Configuraciones en Parametros Principales de Contratos')

	def number_to_letter(self, number, flag=True):
		UNIDADES = (
			'',
			'UN ',
			'DOS ',
			'TRES ',
			'CUATRO ',
			'CINCO ',
			'SEIS ',
			'SIETE ',
			'OCHO ',
			'NUEVE ',
			'DIEZ ',
			'ONCE ',
			'DOCE ',
			'TRECE ',
			'CATORCE ',
			'QUINCE ',
			'DIECISEIS ',
			'DIECISIETE ',
			'DIECIOCHO ',
			'DIECINUEVE ',
			'VEINTE '
		)

		DECENAS = (
			'VENTI',
			'TREINTA ',
			'CUARENTA ',
			'CINCUENTA ',
			'SESENTA ',
			'SETENTA ',
			'OCHENTA ',
			'NOVENTA ',
			'CIEN '
		)

		CENTENAS = (
			'CIENTO ',
			'DOSCIENTOS ',
			'TRESCIENTOS ',
			'CUATROCIENTOS ',
			'QUINIENTOS ',
			'SEISCIENTOS ',
			'SETECIENTOS ',
			'OCHOCIENTOS ',
			'NOVECIENTOS '
		)

		MONEDAS = (
			{'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
			{'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
			{'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
			{'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
			{'country': u'Perú', 'currency': 'PEN', 'singular': u'SOL', 'plural': u'SOLES', 'symbol': u'S/.'},
			{'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
		)
		# Para definir la moneda me estoy basando en los código que establece el ISO 4217
		# Decidí poner las variables en inglés, porque es más sencillo de ubicarlas sin importar el país
		# Si, ya sé que Europa no es un país, pero no se me ocurrió un nombre mejor para la clave.

		def __convert_group(n):
			"""Turn each group of numbers into letters"""
			output = ''

			if(n == '100'):
				output = "CIEN"
			elif(n[0] != '0'):
				output = CENTENAS[int(n[0]) - 1]

			k = int(n[1:])
			if(k <= 20):
				output += UNIDADES[k]
			else:
				if((k > 30) & (n[2] != '0')):
					output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
				else:
					output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
			return output
		#raise osv.except_osv('Alerta', number)
		number=str(round(float(number),2))
		separate = number.split(".")
		number = int(separate[0])
		if flag:
			if int(separate[1]) >= 0:
				moneda = "con " + str(separate[1]).ljust(2,'0') + "/" + "100 " 

		"""Converts a number into string representation"""
		converted = ''
		
		if not (0 <= number < 999999999):
			raise UserError('Alerta %d' % number)
			#return 'No es posible convertir el numero a letras'
		
		number_str = str(number).zfill(9)
		millones = number_str[:3]
		miles = number_str[3:6]
		cientos = number_str[6:]		

		if(millones):
			if(millones == '001'):
				converted += 'UN MILLON '
			elif(int(millones) > 0):
				converted += '%sMILLONES ' % __convert_group(millones)

		if(miles):
			if(miles == '001'):
				converted += 'MIL '
			elif(int(miles) > 0):
				converted += '%sMIL ' % __convert_group(miles)

		if(cientos):
			if(cientos == '001'):
				converted += 'UN '
			elif(int(cientos) > 0):
				converted += '%s ' % __convert_group(cientos)
		if float(number_str)==0:
			converted += 'CERO '
		if flag:
			converted += moneda

		return converted.upper()

class FormulaVariablesLine(models.Model):
	_name = 'formula.variables.line'
	_description = 'Formula Variables Line'

	parameter_id = fields.Many2one('contract.main.parameter', ondelete='cascade')
	name = fields.Char(string='Nombre', required=True)
	description = fields.Char(string='Descripcion')

class ServiceInformationLine(models.Model):
	_name = 'service.information.line'
	_description = 'Service Information Line'

	parameter_id = fields.Many2one('contract.main.parameter', ondelete='cascade')
	name = fields.Char(string='Descripcion', required=True)

class ContactSupportLine(models.Model):
	_name = 'contact.support.line'
	_description = 'Contact Support Line'

	parameter_id = fields.Many2one('contract.main.parameter', ondelete='cascade')
	name = fields.Char(string='Servicio', required=True)
	email = fields.Char(string='Correo Electronico')
	contact = fields.Char(string='Contacto')

class EscalationLevelLine(models.Model):
	_name = 'escalation.level.line'
	_description = 'Escalation Level Line'

	parameter_id = fields.Many2one('contract.main.parameter', ondelete='cascade')
	name = fields.Char(string='Item', required=True)
	description = fields.Char(string='Descripcion')

class ContactPhoneLine(models.Model):
	_name = 'contact.phone.line'
	_description = 'Contact Phone Line'

	parameter_id = fields.Many2one('contract.main.parameter', ondelete='cascade')
	name = fields.Char(string='Area Especializada de Soporte', required=True)
	noc = fields.Char(string='NOC')
	telephony = fields.Char(string='Telefonia')
	soc = fields.Char(string='SOC')

class GlosaryLine(models.Model):
	_name = 'glossary.line'
	_description = 'Glosary Line'

	parameter_id = fields.Many2one('contract.main.parameter', ondelete='cascade')
	name = fields.Char(string='Area Especializada de Soporte', required=True)
	description = fields.Char(string='Descripcion')