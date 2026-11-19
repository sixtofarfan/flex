# -*- encoding: utf-8 -*-
{
    'name': 'Reporte Suscripcion Facturacion',
    'category': 'uncategorize',
    'author': 'ITGRUPO',
    'depends': ['fxo_subscription_invoice_extend'],
    'version': '1.0',
    'description': """
     Descripcion
    """,
    'auto_install': False,
    'demo': [],
    'data': [
        'security/security.xml',
        'views.xml',
        'wizard.xml',
        'generate_invoices_wizard.xml'
    ],
    'installable': True
}
