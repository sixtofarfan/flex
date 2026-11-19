# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from subprocess import Popen, PIPE

class contract_template(models.Model):
	_name = 'contract.template'

	name = fields.Char('Plantilla de Reporte', default="Formato por Defecto")
	description_contract = fields.Text("Texto en el contrato", help= "Es el formato del contrato.")

class sale_subscription(models.Model):
    _inherit = 'sale.subscription'

    description_contract_id = fields.Many2one("contract.template", "Formato de Contrato") 