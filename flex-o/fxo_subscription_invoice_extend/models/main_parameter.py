# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MainParameter(models.Model):
	_inherit = 'main.parameter'

	product_invoices = fields.Many2one('product.product', string='Producto para facturacion')
	name_product_invoices = fields.Char(string='Descripcion para la Factura')
	product_minutes = fields.Many2one('product.product', string='Producto para Minutos Adicionales')
	name_product_minutes = fields.Char(string='Descripcion para Minutos Adicionales')
	serie_control_ids = fields.One2many('serie.control.line', 'main_parameter_id')
	glosa = fields.Char(string='Glosa')
	billing_method = fields.Selection([
		('first', 'Desde el primer dia'),
		('period', 'Segun periodo de facturacion'),
	], string='Metodo de Facturacion', default='period')
	first_day_sub = fields.Boolean(string='Primer dia del mes', default=False, 
		help='Campo para definir si se quiere cambiar la fecha de renovacion de contrato cuando \
			se crea la primera factura')

	@api.onchange('product_invoices')
	def onchange_product_invoices(self):
		if self.product_invoices.id:
			self.name_product_invoices = self.product_invoices.name
		else:
			self.name_product_invoices = False

	@api.onchange('product_minutes')
	def onchange_product_invoices(self):
		if self.product_minutes.id:
			self.name_product_minutes = self.product_minutes.name
		else:
			self.name_product_minutes = False

class SerieControlLine(models.Model):
	_name = 'serie.control.line'
	_description = 'Serie Control Line'

	main_parameter_id = fields.Many2one('main.parameter', ondelete='cascade')
	serie_id = fields.Many2one('it.invoice.serie', string='Serie')
	l10n_latam_identification_type_ids = fields.Many2many('l10n_latam.identification.type', 'serie_control_l10n_rel', string='Tipos de Documento')
	journal_id = fields.Many2one('account.journal', string='Diario')
	type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo de Documento')

class L10nLatamIdentificationType(models.Model):
	_inherit = 'l10n_latam.identification.type'

	serie_control_id = fields.Many2one('serie.control.line')