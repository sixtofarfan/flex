# -*- encoding: utf-8 -*-
{
	'name': 'Job Task Cost Integration',
	'category': 'account',
	'author': 'Jean Pierre',
	'depends': ['project','odoo_job_costing_management'],
	'version': '1.0',
	'description':"""
	Integracion de Tareas con Costos de Trabajo
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
	 'task_cost.xml',
	],
	'qweb':[],
	'installable': True
}
