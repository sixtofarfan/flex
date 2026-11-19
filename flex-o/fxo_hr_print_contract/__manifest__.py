# -*- coding: utf-8 -*-
{
    'name' : 'module for print contract',
    'version': '1.0',
    "author": "[Flexxoone]",
    'summary': 'Módulo para la impresión de contratos de empleados y operarios',
    'category': 'Tools',
    'description':"""""",
    'depends' : [
        'hr',
        'hr_contract',
        'hr_fields_it',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/view_hr_contract.xml',
        'views/hr_employee.xml',
        'report/report_paperformat.xml',
        'report/contract_employee.xml',
        'report/report.xml',
    ],
}
