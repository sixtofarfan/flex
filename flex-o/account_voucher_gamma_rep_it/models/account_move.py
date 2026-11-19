# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch,cm,mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER, TA_LEFT, TA_RIGHT
import time
import decimal

class AccountMove(models.Model):
	_inherit = 'account.move'

	def generate_voucher_pdf_rep_it(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			# c.drawCentredString((wReal/2)+20,hReal, "*** ASIENTO CONTABLE %s ***"%(self.name))
			# c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, self.company_id.name)
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,'')
			c.drawString(30,hReal-30,"COMPROBANTE DE %s %s # %s DEL %s" %(
																			 self.journal_id.code if self.journal_id.code else '',
																			 self.journal_id.name if self.journal_id.name else '',
																			 self.name if self.name else '',
																			 datetime.strftime((self.date), '%d-%m-%Y') if self.date else ''))
			c.drawString(30,hReal-40,'')
			c.drawString(30,hReal-50, self.glosa if self.glosa else '')

			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			# data= [['CUENTA','SOCIO','TD','NRO COMP','DESCRIPCION','CTA ANALITICA','IMPORTE MON','MON','DEBE','HABER','TC']]
			data= [['Cuenta','Debito','Credito','M','Imp.Mon','T/C','Codigo','T.doc','N°Doc','F.Doc.','F. Venc.','CC']]
			t=Table(data,colWidths=size_widths, rowHeights=[18])
			color_cab = colors.Color(red=(220/255),green=(230/255),blue=(241/255))
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('BACKGROUND', (0, 0), (12, 0),color_cab),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),8)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-110
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "voucher.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [120,60,60,30,60,60,80,40,65,50,50,70]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)

		for line in self.line_ids:
			first_pos = 30

			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( line.account_id.code + ' ' + line.account_id.name if line.account_id else '',120) )
			first_pos += size_widths[0]

			c.drawRightString( first_pos+50 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % line.debit)))
			first_pos += size_widths[1]

			c.drawRightString( first_pos+50 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % line.credit)))
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( line.currency_id.name if line.currency_id else '',50) )
			first_pos += size_widths[3]

			c.drawRightString( first_pos+50 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % line.amount_currency)))
			first_pos += size_widths[4]

			c.drawRightString( first_pos+35 ,pos_inicial,'{:,.4f}'.format(decimal.Decimal ("%0.4f" % line.tc)))
			first_pos += size_widths[5]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (line.partner_id.vat if line.partner_id.vat else '') if line.partner_id else '',180) )
			first_pos += size_widths[6]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( line.type_document_id.code if line.type_document_id else '',40) )
			first_pos += size_widths[7]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( line.nro_comp if line.nro_comp else '',65) )
			first_pos += size_widths[8]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( datetime.strftime((self.date), '%d-%m-%Y') if line.date else '',65) )
			first_pos += size_widths[9]

			c.drawRightString( first_pos+45 ,pos_inicial,particionar_text( datetime.strftime((line.date_maturity), '%d-%m-%Y') if line.date_maturity else '',65))
			first_pos += size_widths[10]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( line.analytic_account_id.name if line.analytic_account_id else '',90) )

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file(self.name+'.pdf',base64.encodestring(b''.join(f.readlines())))
