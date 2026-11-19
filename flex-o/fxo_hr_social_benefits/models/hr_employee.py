# -*- coding:utf-8 -*-
from odoo import api, fields, models

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from odoo.exceptions import UserError
from calendar import monthrange
from datetime import *
import base64

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	

	def get_pdf_liquidation(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		Liquidation = self.liquidation_id
		year = int(Liquidation.fiscal_year_id.name)
		cts_period = MainParameter.get_month_name(int(Liquidation.cts_type))
		gratification_period = MainParameter.get_month_name(int(Liquidation.gratification_type))
		Gratification_Line = Liquidation.gratification_line_ids.filtered(lambda line: line.employee_id == self)
		Cts_Line = Liquidation.cts_line_ids.filtered(lambda line: line.employee_id == self)
		Vacation_Line = Liquidation.vacation_line_ids.filtered(lambda line: line.employee_id == self)
		vacation_period_start = MainParameter.get_month_name(int(Vacation_Line.compute_date.month))
		vacation_period_end = MainParameter.get_month_name(int(Vacation_Line.cessation_date.month))
		ExtraLine = Liquidation.liq_ext_concept_ids.filtered(lambda l: l.employee_id == self)
		total_income = Cts_Line.total_cts + Vacation_Line.total_vacation + Gratification_Line.total_grat + Gratification_Line.bonus_essalud + ExtraLine.income
		if Vacation_Line.is_worked_day:
			total_income += Vacation_Line.basic_worked_day
		total_discount = Vacation_Line.afp_jub + Vacation_Line.afp_mixed_com + Vacation_Line.afp_fixed_com + Vacation_Line.afp_si + Vacation_Line.onp + ExtraLine.expenses
		total = ReportBase.custom_round(total_income - total_discount, 2)
		Lot = Liquidation.payslip_run_id
		Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == self)
		Basic = Slip.line_ids.filtered(lambda l: l.salary_rule_id == MainParameter.basic_sr_id)
		Last_Contract = Slip.contract_id
		WorkedDays = Slip.worked_days_line_ids.filtered(lambda w: w.wd_type_id in MainParameter.wd_dlab)
		cessation_period = MainParameter.get_month_name(int(Last_Contract.date_end.month))
		First_Contract = self.env['hr.contract'].get_first_contract(self, Last_Contract)
		days, months = MainParameter.get_months_days_difference(First_Contract.date_start, Last_Contract.date_end)
		years = 0
		if months >= 12:
			while months >=12:
				years += 1
				months -= 12
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=10, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=7.0, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=7.0, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=7.0, fontName="times-roman")
		style_left_tab = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=7.0, fontName="times-roman", leftIndent=14)
		internal_width = [2.5 * cm]
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		bg_color = colors.HexColor("#c5d9f1")
		spacer = Spacer(5, 20)

		global_format = [
			('SPAN', (2, 1), (3, 1)),
			('SPAN', (2, 3), (3, 3)),
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]

		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 160.0, 32.0)
		data = [
			[I if I else '', Paragraph('<strong>LIQUIDACION BENEFICIOS SOCIALES </strong>', style_title)],
			['', Paragraph('<strong>LIQUIDACION BENEFICIOS SOCIALES QUE OTORGA %s</strong>' % self.env.company.name, style_cell)],
		]
		t = Table(data, [5 * cm, 15 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('ALIGN', (1, 0), (1, 0), 'CENTER'),
							   ('ALIGN', (1, 1), (1, 1), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(spacer)
		data = [
				[Paragraph('<strong>DATOS PERSONALES</strong>', style_left)],
				[Paragraph('<strong>Apellidos y Nombres</strong>', style_left_tab), ':', Paragraph(self.name or '', style_left)],
				[Paragraph(u'<strong>DNI N°</strong>', style_left_tab), ':', Paragraph(self.identification_id or '', style_left)],
				[Paragraph('<strong>Cargo</strong>', style_left_tab), ':', Paragraph(self.job_id.name or '', style_left)],
				[Paragraph('<strong>Fecha Ingreso</strong>', style_left_tab), ':', Paragraph(str(First_Contract.date_start) or '', style_left)],
				[Paragraph('<strong>Fecha Cese</strong>', style_left_tab), ':', Paragraph(str(Last_Contract.date_end) or '', style_left)],
				[Paragraph('<strong>Motivo</strong>', style_left_tab), ':', Paragraph(Last_Contract.situation_reason or '', style_left)],
				[Paragraph(u'<strong>Afiliación</strong>', style_left_tab), ':', Paragraph(Last_Contract.membership_id.name or '', style_left)],
				[Paragraph(u'<strong>Ultimo Sueldo Básico</strong>', style_left_tab), ':', Paragraph('S/ %d SOLES' % Last_Contract.wage, style_left),
				 Paragraph('<strong>Tipo de Cambio</strong> %d' % Liquidation.exchange_type, style_left)],
				[Paragraph(u'<strong>Tiempo de Servicios</strong>', style_left_tab), ':', Paragraph('%d años, %d meses y %d dias' % (years, months, days) if years else '%d meses y %d dias' % (months, days), style_left)],
				[''],
				[Paragraph('<strong>BASES DE CALCULO</strong>', style_left)],
				[Paragraph('<strong>1. COMPENSACION POR TIEMPO DE SERVICIOS</strong>', style_left)],
				[Paragraph('<strong>(Periodo {start} {year} a {end} {year})</strong>'.format(start=cts_period, end=cessation_period, year=year), style_left)],
				[Paragraph('<strong>Monto a Pagar</strong>', style_left_tab), ':', Paragraph(str(Cts_Line.total_cts or 0.0), style_left)],
				[Paragraph('<strong>Tiempo</strong>', style_left_tab), ':', Paragraph(str('%d mes(es) %s' % (Cts_Line.months, 'y %d dia(s)' % Cts_Line.days if Cts_Line.days > 0 else '')), style_left)],
				[''],
				[Paragraph('<strong>2. VACACIONES</strong>', style_left)],
				[Paragraph('<strong>(Periodo {start} {start_year} a {end} {end_year})</strong>'.format(start=vacation_period_start,
																									   start_year=Vacation_Line.admission_date.year,
																									   end=vacation_period_end,
																									   end_year=Vacation_Line.cessation_date.year), style_left)],
				[Paragraph('<strong>Vacaciones Truncas</strong>', style_left_tab), ':', Paragraph(str(Vacation_Line.total_vacation or 0.0), style_left)],
				[Paragraph('<strong>Tiempo</strong>', style_left_tab), ':', Paragraph('%d mes(es) %s' % (Vacation_Line.months, 'y %d dia(s)' % Vacation_Line.days if Vacation_Line.days > 0 else ''), style_left)],
				[''],
				[Paragraph('<strong>3. GRATIFICACIONES</strong>', style_left)],
				[Paragraph('<strong>(Periodo {start} {year} a {end} {year})</strong>'.format(start=gratification_period, end=cessation_period, year=year), style_left)],
				[Paragraph(u'<strong>Gratificación Trunca</strong>', style_left_tab), ':', Paragraph(str(Gratification_Line.total_grat or 0.0), style_left)],
				[Paragraph('<strong>BONIF EX.L. 30334</strong>', style_left_tab), ':', Paragraph(str(Gratification_Line.bonus_essalud or 0.0), style_left)],
				[Paragraph('<strong>Tiempo</strong>', style_left_tab), ':', Paragraph(str('%d mes(es) %s' % (Gratification_Line.months, 'y %d dia(s)' % Gratification_Line.days if Gratification_Line.days > 0 else '')), style_left)],
				[''],
				#[Paragraph('<strong>4. LIQUIDACION</strong>', style_left)],
				#[Paragraph('<strong>(Periodo {start} {year} a {end} {year})</strong>'.format(start=gratification_period, end=cessation_period, year=year), style_left)],
				#[Paragraph('<strong>CTS Trunca</strong>', style_left_tab), ':', Paragraph(str(Cts_Line.total_cts or 0.0), style_left)],
				#[Paragraph('<strong>Vacaciones Truncas</strong>', style_left_tab), ':', Paragraph(str(Vacation_Line.total_vacation or 0.0), style_left)],
				#[Paragraph(u'<strong>Gratificación Trunca</strong>', style_left_tab), ':', Paragraph(str(Gratification_Line.total_grat or 0.0), style_left)],
				#[Paragraph('<strong>BONIF EX.L. 30334</strong>', style_left_tab), ':', Paragraph(str(Gratification_Line.bonus_essalud or 0.0), style_left)],
				#[''],
				[Paragraph('<strong>4. DIAS LABORADOS {0}</strong>'.format(sum(WorkedDays.mapped('number_of_days'))), style_left), ':', Paragraph('{0}-{1}-{2} al {3}-{4}-{5} S/ {6}'.format(
					Slip.date_from.day,
					MainParameter.get_month_name(Slip.date_from.month)[:3],
					Slip.date_from.year,
					Last_Contract.date_end.day,
					MainParameter.get_month_name(Last_Contract.date_end.month)[:3],
					Last_Contract.date_end.year,
					Vacation_Line.basic_worked_day,
					), style_left)] if Vacation_Line.is_worked_day else [''],
				[Paragraph('<strong>OTROS INGRESOS</strong>', style_left)],
		]
		In_Concepts = ExtraLine.concept_ids.filtered(lambda c: c.type == 'in')
		Out_Concepts = ExtraLine.concept_ids.filtered(lambda c: c.type == 'out')
		in_data, out_data = [], []
		for inc in In_Concepts:
			in_data.append([Paragraph('<strong>{0}</strong>'.format(inc.name), style_left_tab), ':', Paragraph('{0}'.format(inc.amount), style_left)])
		data += in_data
		data += [
				[''],
				[Paragraph('<strong>Total Ingresos</strong>', style_left_tab), '', Paragraph(str(ReportBase.custom_round(total_income, 2) or 0.0), style_right)],
				[''],
				[Paragraph('<strong>OTROS DESCUENTOS</strong>', style_left)],
				[Paragraph('<strong>Aportes Trabajador</strong>', style_left_tab)],
				[Paragraph('<strong>AFP. PENSIONES</strong>', style_left_tab), ':', Paragraph(str(Vacation_Line.afp_jub or 0.0), style_left)],
				[Paragraph('<strong>AFP. COM. FIJA</strong>', style_left_tab), ':', Paragraph(str(Vacation_Line.afp_fixed_com), style_left)] \
					if First_Contract.commision_type == 'flow' \
					else [Paragraph('<strong>AFP. COM. MIXTA</strong>', style_left_tab), ':', Paragraph(str(Vacation_Line.afp_mixed_com), style_left)],
				[Paragraph('<strong>AFP. SEGUROS</strong>', style_left_tab), ':', Paragraph(str(Vacation_Line.afp_si or 0.0), style_left)],
				[Paragraph('<strong>IMPORTE ONP</strong>', style_left_tab), ':', Paragraph(str(Vacation_Line.onp or 0.0), style_left)],
		]
		for ouc in Out_Concepts:
			out_data.append([Paragraph('<strong>{0}</strong>'.format(ouc.name), style_left_tab), ':', Paragraph('{0}'.format(ouc.amount), style_left)])
		data += out_data
		data += [
				[''],
				[Paragraph('<strong>Total Descuentos</strong>', style_left_tab), '', Paragraph(str(ReportBase.custom_round(total_discount, 2) or 0.0), style_right)],
				[Paragraph('<strong>Total a Pagar</strong>', style_left_tab), '', Paragraph(str(total or 0.0), style_right)],
		]
		t = Table(data, [8 * cm, 1 * cm , 5 * cm, 6 * cm], len(data) * [0.32 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		data = [
				[Paragraph('<strong>Neto a Pagar al Trabajador</strong>', style_left)],
				[Paragraph('<strong>SON {0} SOLES</strong>'.format(MainParameter.number_to_letter(total_income - total_discount)), style_left_tab)],
				['', '', '', Paragraph('{0} {1} de {2} del {3}'.format(self.env.company.city or '',
																	   Last_Contract.date_end.day,
																	   MainParameter.get_month_name(Last_Contract.date_end.month),
																	   Last_Contract.date_end.year), style_cell)],
				[Paragraph('<strong>__________________________<br/>Dpto. de personal<br/>%s</strong>' % self.env.company.name or '', style_cell)],
				[Paragraph('<strong>CONSTANCIA DE RECEPCION</strong>', style_left)],
				[Paragraph('Declaro estar conforme con la presente liquidación, haber recibido el importe de la misma \
							así como el importe correspondiente a todas y cada una de mis remuneraciones y beneficios no \
							teniendo que reclamar en el futuro, quedando asi concluida la relación laboral.', style_cell)],
				[''],
				[Paragraph('<strong>__________________________<br/>%s<br/>DNI Nro.%s</strong>' % (self.name or '', self.identification_id or ''), style_cell)],
		]
		t = Table(data, [8 * cm, 1 * cm , 5 * cm, 6 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('SPAN', (0, 5), (-1, 5)),
			('SPAN', (0, 7), (-1, 7)),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]))
		elements.append(t)
		elements.append(PageBreak())

		return elements
	
	def get_pdf_fifth_certificate(self, date_wizard, employee):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_fifth_values()
		ReportBase = self.env['report.base']
		Liquidation = self.liquidation_id
		FiscalYear = Liquidation.fiscal_year_id
		year = int(FiscalYear.name)
		Company = self.env.company
		Lot = Liquidation.payslip_run_id
		Fifth = self.env['hr.fifth.category'].search([('payslip_run_id', '=', Lot.id)])
		Fifth_Employee = Fifth.line_ids.filtered(lambda line: line.employee_id == self)
		Lots = self.env['hr.payslip.run'].search([('date_start', '>=', date(year, 1, 1)), ('date_start', '<=', Lot.date_start)])
		Slips = Lots.slip_ids.filtered(lambda slip: slip.employee_id == self)
		REQ_ROQ = sum(Slips.mapped('line_ids').filtered(lambda line: line.salary_rule_id in (MainParameter.fifth_afect_sr_id, MainParameter.fifth_extr_sr_id)).mapped('total'))
		Net_Rent = Fifth_Employee.real_other_emp_rem + REQ_ROQ
		Seven_Uit = 7 * FiscalYear.uit
		Total_Rent = Net_Rent - Seven_Uit
		Tax_Rent = self.env['hr.fifth.category.line'].get_tax_proy(Total_Rent, MainParameter.rate_limit_ids)
		Tax_Rent = 0 if Tax_Rent < 0 else Tax_Rent
		Lots = self.env['hr.payslip.run'].search([('date_start', '>=', FiscalYear.date_from),('date_end', '<=', Lot.date_end)])
		Slips = Lots.slip_ids.filtered(lambda slip: slip.employee_id == self)
		PastFifths = sum(Slips.input_line_ids.filtered(lambda line: line.input_type_id == MainParameter.fifth_category_input_id).mapped('amount'))
		elements = []
		style_title = ParagraphStyle(name='Title', alignment=TA_CENTER, fontSize=14, fontName="times-roman")
		style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=10, fontName="times-roman")
		style_right = ParagraphStyle(name='Right', alignment=TA_RIGHT, fontSize=10, fontName="times-roman")
		style_left = ParagraphStyle(name='Left', alignment=TA_LEFT, fontSize=10, fontName="times-roman")
		style_left_tab = ParagraphStyle(name='Left Tab', alignment=TA_LEFT, fontSize=10, fontName="times-roman", leftIndent=14)
		internal_width = [2.5 * cm]
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		spacer = Spacer(5, 20)

		global_format = [
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]

		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 160.0, 32.0)
		data = [[I if I else '']]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(spacer)

		data = [
				[Paragraph('<strong>CERTIFICADO DE RENTAS Y RETENCIONES POR RENTAS DE QUINTA CATEGORÍA</strong>', style_center)],
				[Paragraph('<strong>(Art. 45 D.S. Nº 122.94-EF del 21/09/1994) (R.S. Nº 010-2006/SUNAT del 13/01/2006)</strong>', style_center)],
		]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)
		elements.append(spacer)
		data = [
				[Paragraph('<strong>EJERCICIO GRAVABLE %s</strong>' % year, style_center)],
				[''],
				[Paragraph('{0} RUC Nro. {1} con domicilio fiscal en \
							{2} debidamente representada por el Sr./Sra./Srta. {3} en calidad\
							de Gerente General, identificado con DNI Nro. {4}'.format(Company.name or '',
																					  Company.vat or '',
																					  Company.street or '',
																					  employee.name or '',
																					  employee.identification_id or ''), style_left)],
				[''],
				[Paragraph('<strong>CERTIFICA:</strong>', style_left)],
				[''],
				[Paragraph(u'Que el Sr./Sra./Srta. {0} con Documento de identidad Nro. {1} \
							con domicilio en {2}, se le ha retenido por Impuesto a la Renta de Quinta \
							Categoría por sus funciones en el cargo de {3} correspondiente al ejercicio {4} \
							el importe de:'.format(self.name or '',
												   self.identification_id or '',
												   self.work_location or '',
												   self.job_title or '',
												   FiscalYear.name or ''), style_left)],
			]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)
		elements.append(spacer)
		data = [
				[Paragraph('<strong>1. Renta Bruta:</strong>', style_left)],
				[Paragraph('1.1. Sueldo, asignaciones, gratificaciones, bonificaciones, comisiones, etc.', style_left_tab), Paragraph('S/ %d' % REQ_ROQ, style_left)],
				[Paragraph('1.2. Ingresos percibidos en otros empleadores', style_left_tab), Paragraph('S/ %d' % Fifth_Employee.real_other_emp_rem, style_left)],
				[Paragraph(u'Remuneración Bruta Total', style_left_tab), Paragraph('S/ %d' % Net_Rent, style_left)],
				[''],
				[Paragraph(u'<strong>2. Deducción sobre renta de quinta categoría:</strong>', style_left)],
				[Paragraph('Menos: 7UIT', style_left_tab), Paragraph('S/ %d' % Seven_Uit, style_left)],
				[Paragraph('Total renta imponible ', style_left_tab), Paragraph('S/ %d' % Total_Rent, style_left)],
				[''],
				[Paragraph('<strong>3.	Impuesto a la renta:</strong>', style_left), Paragraph('S/ %d' % Tax_Rent, style_left)],
				[''],
				[Paragraph(u'<strong>4.	Total retención efectuada:</strong>', style_left), Paragraph('S/ %d' % PastFifths, style_left)],
				[''],
				[Paragraph('<strong>Saldo por regularizar:</strong>', style_left), Paragraph('S/ %d' % (Tax_Rent - PastFifths) if self._context.get('fifth') else 'S/ 0.0' , style_left)],
				[''],
				[Paragraph('{0} {1} de {2} del {3}'.format(Company.city or '',
														   date_wizard.day,
														   MainParameter.get_month_name(date_wizard.month),
														   date_wizard.year), style_left)],
				[''],[''],[''],
				[Paragraph('<strong>__________________________<br/>Empleador</strong>', style_center),
				Paragraph('<strong>__________________________<br/>Trabajador</strong>', style_center)],
		]
		t = Table(data, [10 * cm, 10 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]))
		elements.append(t)
		elements.append(PageBreak())

		return elements