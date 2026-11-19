# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from odoo.exceptions import UserError
from datetime import *
import base64

class SaleSubscription(models.Model):
	_inherit = 'sale.subscription'

	instalation_days = fields.Integer(string='Dias de Instalacion')
	child_protection_filter = fields.Boolean(string='Filtro para Proteccion a Menores', default=False)

	def concat_last(self, vals, last):
		if len(vals) > 1:
			vals = ', '.join(vals[:-1]) + ' y ' + vals[-1]
		else:
			vals = vals[0]
		return vals

	def get_template(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)],limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Contabilidad para su Compañía')
		doc = SimpleDocTemplate(MainParameter.dir_create_file + 'Formato de Contrato.pdf', pagesize=letter, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=30, bottomMargin=20)
		ContractParameter = self.env['contract.main.parameter'].get_main_parameter()
		ContractParameter.check_voucher_values()
		Manager = ContractParameter.manager_id
		Representative = self.partner_id.client_representative_id
		if Representative:
			rep_str = "debidamente representado por {partner_rep}, con {partner_rep_doc} Nro. {partner_rep_num},".format(
					partner_rep = Representative.name,
					partner_rep_doc = Representative.l10n_latam_identification_type_id.name if Representative.l10n_latam_identification_type_id else '',
					partner_rep_num = Representative.vat if Representative.vat else '',
				)
		else:
			rep_str = "sin representante legal,"
		annexes = []
		if not self.recurring_invoice_line_ids:
			raise UserError('No se puede procesar una suscripcion sin lineas')
		if all(not i.display_type for i in self.recurring_invoice_line_ids):
			raise UserError('No se puede procesar una suscripcion sin secciones')
		for i in range(2, len(self.recurring_invoice_line_ids) + 2):
			annexes.append(str(i))
		annexes = self.concat_last(annexes, 'y ') if annexes else ''
		
		proxies = []
		for proxy in ContractParameter.proxies_ids:
			if proxy.name and proxy.vat and proxy.l10n_latam_identification_type_id.name:
				proxies.append('%s %s Nro. %s' % (proxy.name, proxy.l10n_latam_identification_type_id.name, proxy.vat))
		proxies = self.concat_last(proxies, 'y ') if proxies else ''
		banks = []
		for rec in self.company_id.partner_id.bank_ids.filtered(lambda bank: bank.type_of_account != '2'):
			if rec.bank_id and rec.bank_id.name not in banks:
				banks.append(rec.bank_id.name)
		banks = self.concat_last(banks, 'y ') if banks else ''
		DetractionBank = self.company_id.partner_id.bank_ids.filtered(lambda bank: bank.type_of_account == '2')
		Months = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 
				'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
		elements = []
		ReportBase = self.env['report.base']
		style_title = ParagraphStyle(name='Title', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=8, fontName="times-roman")
		style_right = ParagraphStyle(name='Right', alignment=TA_RIGHT, fontSize=8, fontName="times-roman")
		style_left = ParagraphStyle(name='Left', alignment=TA_LEFT, fontSize=8, fontName="times-roman")
		style_justify = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontSize=8, fontName="times-roman")
		style_left_tab = ParagraphStyle(name='Left Tab', alignment=TA_LEFT, fontSize=8, fontName="times-roman", leftIndent=14)
		bg_color = '#B2A1BF'
		internal_width = [2.5 * cm]
		spacer = Spacer(5, 20)

		global_format = [
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'TOP')
		]
		TextNumbers = ['', 'un', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez', 'once', 'doce']
		elements = []
		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 160.0, 32.0)
		data = [[I if I else '']]
		t = Table(data, [18 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(spacer)

		data = [
				[Paragraph('<strong><u>CONTRATO CORPORATIVO DE PRESTACIÓN DE SERVICIOS DE TELECOMUNICACIONES</u></strong>', style_title)]
		]
		t = Table(data, [18 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)
		elements.append(spacer)
		data = [
				[Paragraph('Conste por medio del presente documento, el contrato de prestación de servicios de Telecomunicaciones, que celebran \
							de una parte, {company}, con R.U.C. Nro. {vat}, con domicilio en {street}, \
							debidamente representada por su Gerente General, {manager}, identificado con \
							{manager_doc} Nro. {manager_num}, y, por sus Apoderados {proxies}, y actuando indistintamente, según poderes inscritos \
							en la partida electrónica  Nro. {electronic} de los \
							Registros Públicos de Lima, a quien en adelante se denominará {company_slogan}; y de la otra parte, la empresa {partner}, \
							identificada con {partner_doc} Nro. {partner_num}, domiciliada en {partner_street} \
							{rep_str} \
							en adelante {client_slogan}; en los términos y condiciones siguientes:'.format(
				 								company = self.company_id.name,
				 								vat = self.company_id.vat,
				 								street = self.company_id.street_name,
				 								manager = Manager.name,
				 								manager_doc = Manager.l10n_latam_identification_type_id.name,
				 								manager_num = Manager.vat,
				 								proxies = proxies,
				 								electronic = ContractParameter.electronic_doc,
				 								company_slogan = ContractParameter.company_slogan,
				 								partner = self.partner_id.name,
				 								partner_doc = self.partner_id.l10n_latam_identification_type_id.name,
				 								partner_num = self.partner_id.vat,
				 								partner_street = self.partner_id.street_name,
				 								rep_str = rep_str,
				 								client_slogan = ContractParameter.client_slogan,
				 								), style_justify)],
			]
		t = Table(data, [18 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)
		elements.append(spacer)
		
		data = [
				[Paragraph('<strong><u>PRIMERA.- OBJETO:</u></strong>', style_left)],
				[Paragraph('Por el presente instrumento, {company_slogan} brinda a {client_slogan} el servicio detallado en el \
							Anexo {annexes} que forman parte integrante de este contrato. Las condiciones y atributos técnicos \
							del servicio son detallados en los referidos anexos.'.format(
								company_slogan = ContractParameter.company_slogan,
								client_slogan = ContractParameter.client_slogan,
								annexes = annexes,
								), style_justify)],
				[Paragraph('<strong><u>SEGUNDA.- PLAZO:</u></strong>', style_left)],
				[Paragraph('El plazo del presente contrato es {contract_life}, salvo que se pacte la contratación a plazo forzoso. \
							El plazo empieza a computarse desde el día siguiente de la fecha de activación del servicio; por el contrario, \
							si el estudio de factibilidad para la prestación del servicio fuese negativo, el presente contrato no surtirá efectos \
							legales.<br/><br/>En caso {client_slogan} opte por contratar a plazo forzoso, una vez que acabe su periodo de vigencia, \
							devendrá automáticamente en uno de plazo indeterminado.'.format(
								contract_life = 'fijo' if self.template_id.recurring_rule_boundary == 'limited' else 'indeterminado',
								client_slogan = ContractParameter.client_slogan,
								), style_justify)],
				[Paragraph('<strong><u>TERCERA.- RETRIBUCIONES Y PAGOS:</u></strong>', style_left)],
				[Paragraph('{client_slogan} se obliga a pagar la tarifa que se genere por el servicio de instalación y la tarifa mensual, de acuerdo \
							con el plan contratado que se describe en el Anexo {annexes}.  Queda establecido que la tarifa mensual y de \
							instalación incluyen el Impuesto General a las Ventas. Asimismo, queda establecido que los conceptos de servicios \
							están afectos al sistema de pago de detracciones del {percent} % ({percent_str} por ciento). El monto de la detracción deberá ser \
							depositado por {client_slogan} en la cuenta del Banco de la Nación Nro. {acc_number}, que mantiene {company_slogan} para estos fines.\
							<br/><br/>{client_slogan} pagará la tarifa mensual y la tarifa por instalación, según los plazos indicados en el Anexo \
							{annexes}, a más tardar dentro de los {days} días (Crear campo en cabecera de pedido) calendarios siguientes a la entrega \
							del recibo correspondiente, por los servicios efectivamente prestados.<br/><br/>{client_slogan} podrá efectuar los pagos a través \
							de cualquiera de las plataformas del {banks}, con el uso de su código \
							de cliente. El código de cliente figura en el comprobante electrónico.'.format(
								company_slogan = ContractParameter.company_slogan,
								client_slogan = ContractParameter.client_slogan,
								annexes = annexes,
								percent = self.partner_id.p_detraction if self.partner_id.p_detraction else '',
								percent_str = ContractParameter.number_to_letter(self.partner_id.p_detraction, False).lower() if self.partner_id.p_detraction else '',
								acc_number = DetractionBank.acc_number if DetractionBank else '',
								days = self.instalation_days if self.instalation_days else 0,
								banks = banks if banks else '',
								), style_justify)],
				]

		t = Table(data, [18 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		data = [
				[Paragraph('<strong><u>CUARTA.- CARACERISTICAS Y CONDICIONES DEL CONTRATO:</u></strong>', style_left)],
				[Paragraph('a)',style_left),
				 Paragraph('Las condiciones técnicas y comerciales se sujetarán a lo estipulado en el Anexo {annexes}.'.format(
				 				annexes = annexes,
				 				), style_justify)],
				[Paragraph('b)',style_left),
				 Paragraph('El plazo máximo de instalación de EL SERVICIO está estipulado en el Anexo {annexes}. En caso EL SERVICIO \
				 			contratado no pudiese instalarse por causas imputables a {client_slogan} y/o por facilidades técnicas, el plazo de instalación \
				 			se reiniciará. Si por causas imputables a {client_slogan}, EL SERVICIO no pudiera instalarse o si éste se desistiera de la \
				 			contratación de EL SERVICIO, {client_slogan} deberá cancelar los gastos incurridos por {company_slogan}; para ello, {company_slogan} contará con \
				 			los sustentos correspondientes.'.format(
				 				company_slogan = ContractParameter.company_slogan,
				 				client_slogan = ContractParameter.client_slogan,
				 				annexes = annexes,
				 				), style_justify)],
				[Paragraph('c)',style_left),
				 Paragraph('{company_slogan} entregará en calidad de Comodato, el equipo necesario para la instalación y funcionamiento de EL SERVICIO, \
				 			y será anotado, como tal, en el Anexo {annexes}. Los equipos propiedad de {company_slogan} serán devueltos al finalizar \
				 			el presente Contrato.'.format(
				 				company_slogan = ContractParameter.company_slogan,
				 				annexes = annexes,
				 				), style_justify)],
				[Paragraph('d)',style_left),
				 Paragraph('Por la naturaleza del servicio, considerando la rápida obsolescencia de la tecnología y equipos, {company_slogan} podrá modificar \
				 			en todo o en parte los circuitos instalados; teniendo en consideración que los reemplazos sean de igual calidad o superior. \
				 			Dichas modificaciones se realizarán sin costo alguno para el cliente.'.format(
				 				company_slogan = ContractParameter.company_slogan,
				 				), style_justify)],
				[Paragraph('e)',style_left),
				 Paragraph('Los niveles de servicio y disponibilidad, se sujetará a lo estipulado en el Anexo 1.', style_justify)],

				[Paragraph('<strong><u>QUINTA.- OBLIGACIONES DE FIBERLUX:</u></strong>', style_left)],
				[Paragraph('a)',style_left),
				 Paragraph('Proveer EL SERVICIO de acuerdo con los niveles de calidad del Anexo 1, y de conformidad con lo establecido en el reglamento \
				 			sobre las “Condiciones de uso de los servicios públicos de telecomunicaciones” (Resolución Nro. {resolution} y sus \
				 			modificatorias)'.format(
				 				resolution = ContractParameter.resolution,
				 				), style_justify)],
				[Paragraph('b)',style_left),
				 Paragraph('Proveer EL EQUIPO de acceso a la red de fibra óptica o a la red inalámbrica de {company_slogan}, de acuerdo con lo \
				 			estipulado en el Anexo {annexes}'.format(
				 				company_slogan = ContractParameter.company_slogan,
				 				annexes = annexes,
				 				), style_justify)],
				[Paragraph('c)',style_left),
				 Paragraph('Activar y configurar el servicio contratado por {client_slogan}.'.format(
				 				client_slogan = ContractParameter.company_slogan,
				 				), style_justify)],
				[Paragraph('d)',style_left),
				 Paragraph('Brindar información necesaria sobre la configuración de la red para que {client_slogan} pueda hacer uso de EL SERVICIO.'.format(
				 				client_slogan = ContractParameter.client_slogan,
				 				), style_justify)],
				[Paragraph('e)',style_left),
				 Paragraph('Reemplazar sin costo para {client_slogan}, aquellos componentes de EL EQUIPO que se hubieran deteriorado o que \
				 			no funcionen correctamente, siempre que dicho deterioro o mal funcionamiento no se hubiera generado por \
				 			causas atribuibles a {client_slogan} o por terceros.'.format(
				 				client_slogan = ContractParameter.client_slogan,
				 				), style_justify)],
				[Paragraph('f)',style_left),
				 Paragraph('{company_slogan}, contará con un centro de atención {client_slogan} y soporte técnico, que funcionará las 24 horas del día, \
				 			todos los días del año. En dicha área, se podrán realizar consultas y/o reclamos, siguiendo los procedimientos \
				 			establecidos por la autoridad regulatoria.'.format(
				 				company_slogan = ContractParameter.company_slogan,
				 				client_slogan = ContractParameter.client_slogan,
				 				), style_justify)],
				[Paragraph('g)',style_left),
				 Paragraph('A efectos de mantener altos niveles de disponibilidad, {company_slogan} deberá realizar táreas de mantenimiento preventivo \
				 			y correctivo, debiendo coordinar con el cliente, y comunicarle, vía correo electrónico, con una antelación mínima \
				 			de {anticipated_hours} horas, la fecha en que se producirá dicho mantenimiento; así como, su plazo estimado, siguiendo \
				 			las normativas establecidas por el organismo regulador ({organism}).'.format(
				 				company_slogan = ContractParameter.company_slogan,
				 				anticipated_hours = ContractParameter.anticipated_hours,
				 				organism = ContractParameter.organism,
				 				), style_justify)],
				[Paragraph('h)',style_left),
				 Paragraph('El procedimiento ante incidencias y los niveles de escalamiento se sujetará a lo estipulado en el anexo 1.', style_justify)],

				[Paragraph('<strong><u>SEXTA.- OBLIGACIONES DE {client_slogan}:</u></strong>'.format(
								client_slogan = ContractParameter.company_slogan,
								), style_left)],
				[Paragraph('a)',style_left),
				 Paragraph('Abonar, oportunamente, los pagos derivados del presente Contrato. Ante la falta de pago, {company_slogan} se reserva el \
				 			derecho de suspender el servicio y reconectarlo, de acuerdo con la normativa vigente.'.format(
				 				company_slogan = ContractParameter.company_slogan,
				 				), style_justify)],
				[Paragraph('b)',style_left),
				 Paragraph('Conservar de forma diligente, los equipos propiedad de {company_slogan}.'.format(
				 				company_slogan = ContractParameter.company_slogan,
				 				), style_justify)],
				[Paragraph('c)',style_left),
				 Paragraph('No manipular, modificar, trasladar, o alterar los equipos propiedad de {company_slogan}; en caso de detectar algún \
				 			problema en los equipos, se compromete a dar aviso inmediato a {company_slogan}.'.format(
				 				company_slogan = ContractParameter.company_slogan,
				 				), style_justify)],
				[Paragraph('d)',style_left),
				 Paragraph('Permitir el ingreso y dar las facilidades al personal de {company_slogan} o de sus contratistas, previa coordinación \
				 			con {client_slogan}, para labores de instalación, reparación y mantenimiento de EL SERVICIO. '.format(
				 				company_slogan = ContractParameter.company_slogan,
				 				client_slogan = ContractParameter.client_slogan,
				 				), style_justify)],
				[Paragraph('e)',style_left),
				 Paragraph('A la terminación del contrato, restituir a {company_slogan} los equipos y demás elementos, en perfecto estado de \
				 			funcionamiento, salvo aquellas consecuencias propias del buen uso y paso del tiempo.'.format(
				 				company_slogan = ContractParameter.company_slogan,
				 				), style_justify)],

				[Paragraph('<strong><u>SEPTIMA.- INCIDENCIAS Y AVERÍAS:</u></strong>', style_left)],
				[Paragraph('Frente a cualquier incidencia o avería, {client_slogan} deberá dar aviso inmediato a {company_slogan}, al número de atención \
							señalado en el Anexo 1; dándose inicio, de esta manera, el cómputo de los tiempos máximos de reparación establecidos \
							por la norma aplicable.'.format(
								company_slogan = ContractParameter.company_slogan,
								client_slogan = ContractParameter.client_slogan,
								), style_justify)],
				[Paragraph('<strong><u>OCTAVA.- LIMITACIÓN DE RESPONSABILIDAD:</u></strong>', style_left)],
				[Paragraph('{company_slogan}, no será responsable por cortes, averías y/o suspensión de EL SERVICIO en los siguientes casos:'.format(
								company_slogan = ContractParameter.company_slogan,
								), style_justify)],
				[Paragraph('a)',style_left),
				 Paragraph('Falta de pago de la Tarifa mensual, en la forma y oportunidad convenidas.', style_justify)],
				[Paragraph('b)',style_left),
				 Paragraph('Mal funcionamiento de los equipos adquiridos por {client_slogan} a terceros.'.format(
								client_slogan = ContractParameter.client_slogan,
								), style_justify)],
				[Paragraph('c)',style_left),
				 Paragraph('Manipulación indebida de {client_slogan} de los elementos de EL SERVICIO o de la configuración de la instalación.'.format(
								client_slogan = ContractParameter.client_slogan,
								), style_justify)],
				[Paragraph('d)',style_left),
				 Paragraph('Cualquier otra causa que no pueda ser, plenamente, atribuida a {company_slogan}.'.format(
								company_slogan = ContractParameter.company_slogan,
								), style_justify)],
			]

		t = Table(data, [1 * cm, 17 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
								   ('VALIGN', (0, 0), (-1, -1), 'TOP'),
								   ('SPAN', (0, 0), (1, 0)),
								   ('SPAN', (0, 6), (1, 6)),
								   ('SPAN', (0, 15), (1, 15)),
								   ('SPAN', (0, 21), (1, 21)),
								   ('SPAN', (0, 22), (1, 22)),
								   ('SPAN', (0, 23), (1, 23)),
								   ('SPAN', (0, 24), (1, 24)),
								]))
		elements.append(t)		

		data = [
				[Paragraph('<strong><u>NOVENA.- RESOLUCIÓN:</u></strong>', style_left)],
				[Paragraph('Si por causas NO atribuibles a {company_slogan}, {client_slogan} que hubiere contratado a plazo forzoso, decidiera resolver \
							el contrato durante su vigencia, o si {company_slogan} lo resolviera por falta de pago, siguiendo el procedimiento \
							establecido en el {article} de las Condiciones de Uso, {client_slogan} deberá abonar por concepto de penalidad el \
							equivalente a las mensualidades pendientes hasta el término de su contrato.<br/><br/>Las causales de resolución \
							del contrato se ajustan a lo establecido por lo establecido en los {articles} del texto único ordenado \
							de las “Condiciones de Uso de los Servicios Públicos de Telecomunicaciones” (Resolución Nro. {resolution} y \
							sus modificatorias).'.format(
								company_slogan = ContractParameter.company_slogan,
								client_slogan = ContractParameter.client_slogan,
								article = ContractParameter.article,
								articles = ContractParameter.articles,
								resolution = ContractParameter.resolution,
								), style_justify)],
				[Paragraph('<strong><u>DECIMA.- CESIÓN DE DERECHOS:</u></strong>', style_left)],
				[Paragraph('{client_slogan} no podrá ceder sus derechos u obligaciones contractuales, sin el consentimiento previo, expreso y por \
							escrito de {company_slogan}.<br/><br/>{company_slogan}, podrá ceder su posición contractual o cualquiera de sus derechos u \
							obligaciones, durante la vigencia del presente Contrato. Para ello, {client_slogan} otorga, de manera anticipada, su \
							conformidad.'.format(
								company_slogan = ContractParameter.company_slogan,
								client_slogan = ContractParameter.client_slogan,
								), style_justify)],
				[Paragraph('<strong><u>DECIMO PRIMERA.-PROTECCIÓN DE DATOS PERSONALES Y USO SEGURO Y RESPONSABLE DE TECONOLOGIAS DE INFORMACIÓN \
							POR NIÑOS Y ADOLESCENTES:</u></strong>', style_left)],
				[Paragraph('Los datos que {client_slogan} proporcione en virtud del presente contrato serán utilizados y tratados de conformidad con \
							la Ley Nro. {law}, Ley de Protección de Datos Personales y su Reglamento, aprobado por {approver}. Asimismo, a \
							{client_slogan} le asiste el derecho de información, acceso, actualización, inclusión, rectificación, supresión y oposición \
							sobre sus datos personales.<br/><br/>En cumplimiento de la Ley Nro. {law2}, se hace saber a {client_slogan} si desea contar con \
							un filtro para bloquear páginas web con contenido pornográfico u otras de contenido violento, para protección de niños, \
							niñas y adolescentes.<br/><br/>{bool}'.format(
								client_slogan = ContractParameter.client_slogan,
								law = ContractParameter.law,
								approver = ContractParameter.approver,
								law2 = ContractParameter.law2,
								bool = 'Si' if self.child_protection_filter else 'No',
								), style_justify)],
				[Paragraph('<strong><u>DECIMO SEGUNDA.- DOMICILIO:</u></strong>', style_left)],
				[Paragraph('Ambas partes señalan como sus domicilios los indicados en la introducción de este Contrato; y, en donde válidamente \
							se cursarán las comunicaciones a que hubiere lugar. Cualquier cambio de domicilio, para surtir efecto legal, deberá \
							ser comunicado con una anticipación, no menor, de quince (15) días calendarios.', style_justify)],
				[Paragraph('<strong><u>DECIMO TERCERA.- LEGISLACION APLICABLE Y COMPETENCIA:</u></strong>', style_left)],
				[Paragraph('Son aplicables al presente contrato las disposiciones contenidas en el texto único ordenado de las “Condiciones de \
							Uso de los Servicios Públicos de Telecomunicaciones” (Resolución Nro. {resolution} y sus modificatorias), el reglamento \
							para la “Atención de Reclamos de Usuarios de Servicios Públicos de Telecomunicaciones” (Resolución Nro. {resolution}), \
							y las normas que regulan el sector Telecomunicaciones.<br/><br/>Para todo litigio o controversia derivado o relacionado \
							con este acto jurídico, las partes se someten a la jurisdicción de los jueces y tribunales de la ciudad donde se \
							prestará el servicio; sin perjuicio de la competencia del OSIPTEL, para la atención de reclamos de usuarios.<br/><br/>\
							{city}, {day} de {month} de {year}'.format(
								resolution = ContractParameter.resolution,
								city = self.company_id.city,
								day = self.date_start.day,
								month = Months[self.date_start.month],
								year = self.date_start.year,
								), style_justify)],
			]

		t = Table(data, [18 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'TOP')
							]))
		elements.append(t)
		elements.append(spacer)
		elements.append(spacer)
		elements.append(spacer)

		data = [
				[Paragraph('<strong>__________________________</strong>', style_center), 
				 Paragraph('<strong>__________________________</strong>', style_center)],
				[Paragraph('<strong>Nombre:..................</strong>', style_center), 
				 Paragraph('<strong>Nombre:..................</strong>', style_center)],
				[Paragraph('<strong>Cargo:...................</strong>', style_center), 
				 Paragraph('<strong>Cargo:...................</strong>', style_center)],
				[Paragraph('<strong>DNI:.....................</strong>', style_center), 
				 Paragraph('<strong>DNI:.....................</strong>', style_center)],
			]
		t = Table(data, [9 * cm, 9 * cm])
		t.setStyle(TableStyle([
							('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
						]))
		elements.append(t)
		elements.append(PageBreak())

		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 160.0, 32.0)
		data = [[I if I else '']]
		t = Table(data, [18 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(spacer)

		data = [
				[Paragraph('<strong><u>ANEXO 1 - ACUERDO DE NIVEL DE SERVICIO Y PENALIDADES LIMA Y PROVINCIAS (SLA)</u></strong>', style_title)],
			]
		t = Table(data, [18 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'TOP')
							]))
		elements.append(t)
		elements.append(spacer)

		data = [
				[Paragraph('El acuerdo de nivel de servicio (SLA) define a través de “Niveles de Servicio Garantizados”, los parámetros para \
							Pérdida de Paquetes, Latencia, Disponibilidad de Servicio, y Tiempo Promedio de Reparación. {company_slogan} otorgará un \
							crédito a favor de CLIENTE, en el caso de que estos niveles de servicio no sean alcanzados. Este crédito será \
							reconocido en los cobros mensuales mediante notas de crédito (N/C).'.format(
								company_slogan = ContractParameter.company_slogan,
								), style_justify)],
				[Paragraph('<strong><u>A.- DEFINICIONES</u></strong>', style_left)],
				[Paragraph('<strong>1.- Pérdidas de Paquetes.</strong>', style_left)],
				[Paragraph('La pérdida de paquetes se produce cuando uno o más paquetes de datos que son transmitidos dentro de la red de \
							{company_slogan}, no llegan a su destino.'.format(
								company_slogan = ContractParameter.company_slogan,
								), style_justify)],
				[Paragraph('<strong>2.- Latencia (Delay).</strong>', style_left)],
				[Paragraph('Técnicamente, la “Latencia” es el intervalo de tiempo (en milisegundos) que le toma a un paquete de datos de prueba, \
							viajar de ida y vuelta entre un punto de origen y un punto de destino.', style_justify)],
				[Paragraph('<strong>3.- Disponibilidad.</strong>', style_left)],
				[Paragraph('La disponibilidad es el tiempo promedio en que el servicio se encuentra disponible.<br/>El cálculo de la \
							Disponibilidad del Servicio está hecho en función a la siguiente fórmula:<br/>%Disponibilidad = 100 * [1- (TC/TD)]<br/> \
							TC = Tiempo total de cortes acumulados en el mes (minutos)<br/> TD = Tiempo total disponible en minutos \
							(Total días del mes x minutos en el día)<br/>El tiempo de corte inicia cuando {client_slogan} reporta la caída y \
							finaliza cuando {company_slogan} haya solucionado el mismo (posterior reporte al cliente). Toda vez que una sede no esté \
							disponible, debe ser documentado por medio de un Ticket de Reclamo.'.format(
								company_slogan = ContractParameter.company_slogan,
								client_slogan = ContractParameter.client_slogan,
								), style_justify)],
				[Paragraph('<strong>4.- Tiempo promedio de reparación por Circuito (TPR).</strong>', style_left)],
				[Paragraph('El Tiempo promedio de reparación (TPR), establece el tiempo máximo que transcurre, desde el momento en que se reporta \
							la avería del servicio y su registro en nuestro sistema hasta que el problema es solucionado y el servicio se restaura. \
							Los tiempos especificados son promedios mensuales y no incluyen averías por hecho fortuito o fuerza mayor, causas fuera \
							del control de la empresa, o falta de acceso de facilidades a ser otorgadas por {client_slogan} para la solución de la \
							avería.<br/><br/>Todos los términos serán considerados hasta con dos decimales para efecto de la determinación de la \
							penalidad.<br/>El tiempo de mantenimiento preventivo no se contabilizará para los índices de indisponibilidad del \
							servicio. Si el mantenimiento no es comunicado con anticipación, este tiempo se considerará como tiempo de inoperatividad.\
							<br/>Los mantenimientos correctivos y/o de emergencia se regirán por lo establecido en el contrato, del que este Anexo \
							forma parte.'.format(
								client_slogan = ContractParameter.client_slogan,
								), style_justify)],
				[Paragraph('<strong><u>B.- NIVELES DE LOS SERVICIOS Y PENALIDADES</u></strong>', style_left)],
				[Paragraph('<strong>Objetivo Mensual</strong>', style_left)],
				[Paragraph('Lima: {capital_percent}%<br/>Provincia: {province_percent}'.format(
								capital_percent = ContractParameter.capital_percent,
								province_percent = ContractParameter.province_percent,
								), style_left)],
				[Paragraph('<strong>Fórmula para el calculo de la penalidad/descuento por la disponibilidad del servicio:</strong>', style_left)],
				[Paragraph('Formula: {formula}'.format(
								formula = ContractParameter.formula,
								), style_left)],
			]
		for line in ContractParameter.var_lines:
			data.append([Paragraph('{name} : {description}'.format(
						name = line.name,
						description = line.description if line.description else '',
						), style_left)])
		data += [
				[Paragraph('<strong><u>C.- GUÍA DE REPORTE DE INCIDENCIAS Y ESCALAMIENTO</u></strong>', style_left)],
				[Paragraph('<strong>1.- Descripción</strong>', style_left)],
				[Paragraph('Este proceso es parte integral del contrato adquirido para los servicios adquiridos (ver Anexos) y \
							solo debe ser aplicado a los servicios que provee la empresa {company_slogan}.'.format(
								company_slogan = ContractParameter.company_slogan,
								), style_justify)],
				[Paragraph('<strong>2.- Objetivos</strong>', style_left)],
				[Paragraph('El presente documento provee los procedimientos asociados con la administración de incidencias reportadas \
							al Área Especializada de Soporte Técnico {support}, así como la apertura de tickets y escalamiento.'.format(
								support = ContractParameter.support,
								), style_justify)],
				[Paragraph('<strong>3.- Procesos para la administración de incidencias y solicitudes</strong>', style_left)],
				[Paragraph('{company_slogan} monitorea y {monitoring}. Para reportar incidencias o averías el cliente podrá comunicarse directamente \
							al Área Especializada de Soporte Técnico de {support} siendo estos el principal contacto con el cliente \
							para comunicar una avería o solicitar soporte técnico.'.format(
								company_slogan = ContractParameter.company_slogan,
								monitoring = ContractParameter.monitoring,
								support = ContractParameter.support,
								), style_justify)],
				[Paragraph('<strong>a) Detección y reporte de incidencias</strong>', style_left)],
				[Paragraph('Si {client_slogan} detecta una incidencia en el servicio; {client_slogan} deberá reportar al Área Especializada de Soporte \
							Técnico después de realizar una verificación inicial, realizar pruebas, etc.<br/><br/>El primer paso es comunicarse \
							con el área especializada y reportar la incidencia, posteriormente se creará y entregará un número de ticket que \
							identificará la incidencia. {client_slogan} es responsable de toda la información proporcionada al área especializada, \
							la misma no debe contener errores u omisiones.<br/><br/>Para resolver la incidencia eficientemente, se solicitará a \
							{client_slogan} información referida al servicio de acuerdo a lo siguiente:'.format(
								client_slogan = ContractParameter.client_slogan,
								), style_justify)],
			]
		for line in ContractParameter.service_lines:
			data.append([Paragraph('* {name}'.format(
						name = line.name,
						), style_justify)])
		data += [
				[Paragraph('<strong>b) Resolución de Incidencias</strong>', style_left)],
				[Paragraph('Inmediatamente después de la detección de la incidencia, {company_slogan} realiza un análisis de la misma y proveerá \
							a {client_slogan} una descripción del mismo y el tiempo estimado de solución.  El Área Especializada de Soporte Técnico \
							informará al cliente sobre el progreso de la solución del evento en un periodo de tiempo establecido. El problema \
							es resuelto cuando el servicio es restablecido de acuerdo a las especificaciones del servicio contratado.<br/> Después \
							de resolver la incidencia el Área Especializada de Soporte Técnico solicitará a {client_slogan} su conformidad, y \
							procederá a cerrar el ticket de avería.'.format(
								company_slogan = ContractParameter.company_slogan,
								client_slogan = ContractParameter.client_slogan,
								), style_justify)],
				[Paragraph('<strong>c) Reporte de Solicitud para soporte</strong>', style_left)],
				[Paragraph('{client_slogan} puede solicitar soporte mediante correo electrónico o vía telefónica:'.format(
								client_slogan = ContractParameter.client_slogan,
								), style_justify)],
			]
		t = Table(data, [18 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'TOP')
							]))
		elements.append(t)

		data = [
				[Paragraph('SERVICIO', style_center), 
				 Paragraph('CORREO ELECTRÓNICO', style_center), 
				 Paragraph('CONTACTO', style_center)],
			]
		for line in ContractParameter.contact_lines:
			data.append([Paragraph(line.name, style_center),
						 Paragraph(line.email if line.email else '', style_center),
						 Paragraph(line.contact if line.contact else '', style_center),
						])

		t = Table(data, [7 * cm, 5 * cm, 5 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'TOP'),
							   ('BACKGROUND', (0, 0), (-1, 0), bg_color),
							   ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
							   ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
							]))
		elements.append(t)

		data = [
				[Paragraph('<strong>4.- Escalamiento</strong>', style_left)],
				[Paragraph('Si {client_slogan} no está conforme con el nivel de soporte recibido por parte de la empresa {company_slogan} (por ejemplo. el \
							progreso de la resolución de la incidencia o solicitud), {client_slogan} está en la facultad de realizar el siguiente \
							escalamiento; por temas de seguridad solo contactos autorizados pueden escalar una incidencia o solicitud:'.format(
								company_slogan = ContractParameter.company_slogan,
								client_slogan = ContractParameter.client_slogan,
								), style_justify)],
			]
		
		t = Table(data, [18 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'TOP')
							]))
		elements.append(t)

		data = [
				[Paragraph('ITEM', style_center),
				 Paragraph('DESCRIPCIÓN', style_center)]
			]

		for line in ContractParameter.escalation_lines:
			data.append([Paragraph(line.name, style_center),
						 Paragraph(line.description if line.description else '', style_center),
						])

		t = Table(data, [4 * cm, 10 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'TOP'),
							   ('BACKGROUND', (0, 0), (-1, 0), bg_color),
							   ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
							   ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
							]))
		elements.append(t)

		data = [
				[Paragraph('<strong>5.- Teléfonos de Contacto</strong>', style_left)],
				[Paragraph('El Área Especializada de Soporte Técnico es el punto principal de contacto, cualquier evento o avería debe ser \
							reportada. Los teléfonos a los que {client_slogan} debe comunicarse son:'.format(
								client_slogan = ContractParameter.client_slogan,
								), style_justify)],
			]
		
		t = Table(data, [18 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'TOP')
							]))
		elements.append(t)

		data = [
				[Paragraph('Area Especializada de Soporte', style_center),
				 Paragraph('NOC', style_center),
				 Paragraph('Telefonia', style_center),
				 Paragraph('SOC', style_center),],
				[Paragraph('Tipo de Servicio', style_center),
				 Paragraph('Internet, Transmision de Datos, Fibra Oscura, Wifi Gestionado', style_center),
				 Paragraph('Telefonia IP, Cloud Server', style_center),
				 Paragraph('Seguridad Perimetral Gestionada', style_center),],
			]

		for line in ContractParameter.phone_lines:
			data.append([Paragraph(line.name, style_center),
						 Paragraph(line.noc if line.noc else '', style_center),
						 Paragraph(line.telephony if line.telephony else '', style_center),
						 Paragraph(line.soc if line.soc else '', style_center),
						])

		t = Table(data, [3 * cm, 5 * cm, 5 * cm, 5 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'TOP'),
							   ('BACKGROUND', (0, 0), (-1, 0), bg_color),
							   ('BACKGROUND', (0, 1), (-1, 1), bg_color),
							   ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
							   ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
							]))
		elements.append(t)

		data = [[Paragraph('<strong>6.- Glosario</strong>', style_left)],]

		for line in ContractParameter.glossary_lines:
			data.append([Paragraph('<strong>{name}.- </strong>{description}'.format(
							name = line.name,
							description = line.description,
							), style_left),
						])

		t = Table(data, [18 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'TOP')
							]))
		elements.append(t)
		elements.append(PageBreak())

		SubsLines = self.env['sale.subscription.line'].search([('analytic_account_id', '=', self.id)], order='sequence')
		Sections = SubsLines.filtered(lambda l: l.display_type == 'line_section')
		annex = 2
		for c, sec in enumerate(Sections, 0):
			locations_data, conditions_data, time_data = [], [], []
			if c + 1 < len(Sections):
				SectionLines = SubsLines.filtered(lambda l:l.sequence > sec.sequence and l.sequence < Sections[c + 1].sequence and not l.display_type)
				NotesLines = SubsLines.filtered(lambda l:l.sequence > sec.sequence and l.sequence < Sections[c + 1].sequence and l.display_type == 'line_note')
			else:
				SectionLines = SubsLines.filtered(lambda l:l.sequence > sec.sequence and not l.display_type)
				NotesLines = SubsLines.filtered(lambda l:l.sequence > sec.sequence and l.display_type == 'line_note')
			limit = len(SectionLines)
			locations_data = [
				[Paragraph('Lugar de Prestacion de Servicio', style_center)],
				[Paragraph('Remoto', style_center), Paragraph('Cabecera', style_center)],
			]
			conditions_data = [[
				Paragraph('Servicio/Producto', style_center),
				Paragraph('Importe', style_center),
				Paragraph('Mda', style_center),
				Paragraph('Forma de Pago', style_center),
				Paragraph('Tipo de Corte (TIP)', style_center),
			]]
			for d, line in enumerate(SectionLines, 1):
				if d == 1:
					I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 160.0, 32.0)
					data = [[I if I else '']]
					t = Table(data, [18 * cm])
					t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
										   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
					elements.append(t)
					elements.append(spacer)
					data = [
							[Paragraph('<strong><u>ANEXO %d - %s</u></strong>' % (annex, sec.name), style_title)],
						]
					t = Table(data, [18 * cm])
					t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
										   ('VALIGN', (0, 0), (-1, -1), 'TOP')
										]))
					elements.append(t)
					elements.append(spacer)
					data = [
							[Paragraph('<strong>1. ESPECIFICACIONES TÉCNICAS</strong>', style_left)],
						]
					t = Table(data, [18 * cm])
					t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
										   ('VALIGN', (0, 0), (-1, -1), 'TOP')
										]))
					elements.append(t)
					elements.append(spacer)

					data = [
							[Paragraph('Servicio', style_center),
							 Paragraph('Cant.', style_center),
							 Paragraph('UM', style_center)],
							[Paragraph(line.name, style_left),
							 Paragraph(str(line.quantity), style_left),
							 Paragraph(line.uom_id.name, style_left)],
							[Paragraph('Tipo de Conexion', style_center),
							 Paragraph('Tipo de Conexion Relacional', style_center),
							 Paragraph('Medio Fisico', style_center)],
							[Paragraph(line.type_conection if line.type_conection else '', style_left),
							 Paragraph(line.type_conection_relation if line.type_conection_relation else '', style_left),
							 Paragraph(line.transport_physic_relation if line.transport_physic_relation else '', style_left)],
							[Paragraph('Plazo máximo estimado de instalación y/o activación del servicio', style_center),
							 Paragraph('Tipo', style_center)],
							[Paragraph(str(line.customer_lead) if line.customer_lead else '', style_left),
							 Paragraph(line.type_item if line.type_item else '', style_left)],
						]
					t = Table(data, [8 * cm, 5 * cm, 5 * cm])
					t.setStyle(TableStyle([
										('SPAN', (1, 4), (2, 4)),
										('SPAN', (1, 5), (2, 5)),
										('ALIGN', (0, 0), (-1, -1), 'CENTER'),
										('VALIGN', (0, 0), (-1, -1), 'TOP'),
										('BACKGROUND', (0, 0), (-1, 0), bg_color),
										('BACKGROUND', (0, 2), (-1, 2), bg_color),
										('BACKGROUND', (0, 4), (-1, 4), bg_color),
										('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
										('BOX', (0, 0), (-1, -1), 0.25, colors.black),
										]))
					elements.append(t)
					elements.append(spacer)
				Origin = None
				if line.item_origin != 0:
					Origin = SubsLines.filtered(lambda l: l.sequence2 == line.item_origin)
				if Origin:
					locations_data.append([
						Paragraph(line.partner_street_destination.street if line.partner_street_destination.street else '', style_left),
						Paragraph(Origin.partner_street_destination.street if Origin.partner_street_destination.street else '', style_left),
					])
				conditions_data.append([
					Paragraph(line.name, style_left),
					Paragraph(str(line.price_subtotal), style_left),
					Paragraph(self.pricelist_id.currency_id.plural_name, style_left),
					Paragraph(line.way_to_pay_id.name if line.way_to_pay_id else '', style_left),
					Paragraph(dict(line._fields['type_cut'].selection).get(line.type_cut) if line.type_cut else '', style_left),
				])
				if d == limit:
					if locations_data:
						t = Table(locations_data, [9 * cm, 9 * cm])
						t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
											   ('VALIGN', (0, 0), (-1, -1), 'TOP'),
											   ('BACKGROUND', (0, 0), (-1, 0), bg_color),
											   ('BACKGROUND', (0, 1), (-1, 1), bg_color),
											   ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
											   ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
											   ('SPAN', (0, 0), (1, 0)),
											]))
						elements.append(t)
						elements.append(spacer)

					data = [
						[Paragraph('<strong>2. CONDICIONES COMERCIALES</strong>', style_left)],
					]
					t = Table(data, [18 * cm])
					t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
										   ('VALIGN', (0, 0), (-1, -1), 'TOP')
										]))
					elements.append(t)
					elements.append(spacer)
					if conditions_data:
						t = Table(conditions_data, [5 * cm, 2 * cm, 2 * cm, 3 * cm, 2 * cm])
						t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
											   ('VALIGN', (0, 0), (-1, -1), 'TOP'),
											   ('BACKGROUND', (0, 0), (-1, 0), bg_color),
											   ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
											   ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
											]))
						elements.append(t)
						elements.append(spacer)

					data = [
						[Paragraph('<strong>3. PLAZO</strong>', style_left)],
					]
					t = Table(data, [18 * cm])
					t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
										   ('VALIGN', (0, 0), (-1, -1), 'TOP')
										]))
					elements.append(t)
					elements.append(spacer)
					
					time_data = [
						[
							Paragraph('Plazo', style_center),
							Paragraph('Forsozo', style_center),
							Paragraph('', style_center),
						],
						[
							Paragraph(dict(self.template_id._fields['recurring_rule_boundary'].selection).get(self.template_id.recurring_rule_boundary) if self.template_id.recurring_rule_boundary else '', style_left),
							Paragraph(str(self.template_id.recurring_rule_count) if self.template_id.recurring_rule_count else '', style_left),
							Paragraph(dict(self.template_id._fields['recurring_rule_type'].selection).get(self.template_id.recurring_rule_type) if self.template_id.recurring_rule_type else '', style_left),
						]
					]
					t = Table(time_data, [4 * cm, 4 * cm, 4 * cm])
					t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
										   ('VALIGN', (0, 0), (-1, -1), 'TOP'),
										   ('BACKGROUND', (0, 0), (-1, 0), bg_color),
										   ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
										   ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
										]))
					elements.append(t)
					elements.append(spacer)
					if NotesLines:
						data = []
						for note in NotesLines:
							data.append([Paragraph(note.name, style_left)])
						t = Table(data, [16 * cm])
						t.setStyle(TableStyle([
											('ALIGN', (0, 0), (-1, -1), 'CENTER'),
											('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
											('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
											('BOX', (0, 0), (-1, -1), 0.25, colors.black),
										]))
						elements.append(t)
					elements.append(spacer)
					elements.append(spacer)
					elements.append(spacer)	
					data = [
							[Paragraph('<strong>__________________________</strong>', style_center), 
							 Paragraph('<strong>__________________________</strong>', style_center)],
							[Paragraph('<strong>Nombre:..................</strong>', style_center), 
							 Paragraph('<strong>Nombre:..................</strong>', style_center)],
							[Paragraph('<strong>Cargo:...................</strong>', style_center), 
							 Paragraph('<strong>Cargo:...................</strong>', style_center)],
							[Paragraph('<strong>DNI:.....................</strong>', style_center), 
							 Paragraph('<strong>DNI:.....................</strong>', style_center)],
						]
					t = Table(data, [9 * cm, 9 * cm])
					t.setStyle(TableStyle([
										('ALIGN', (0, 0), (-1, -1), 'CENTER'),
										('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
									]))
					elements.append(t)
					elements.append(PageBreak())
					annex += 1

		doc.build(elements)
		f = open(MainParameter.dir_create_file + 'Formato de Contrato.pdf', 'rb')
		return self.env['popup.it'].get_file('Formato de Contrato.pdf',base64.encodestring(b''.join(f.readlines())))