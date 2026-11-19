# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Invoice Partner Category",
    'description': """
        Adiciona Estado de Cliente, visualiza en invoices y asientos
        El estado de cliente debe ser actualizado desde los contratos
        - Si al menos un contrato esta en estado activo, estado del Partner debe ser igual  ACTIVO
        - Si todos los estados del subscripciones esta en el mismo estado, estado de partner debe ser igual a uno de los estados de subscripcion.
    """,
    'author': "Flexxoone",
    'depends': [
        'account_fields_it',
    ],
    'website': "https://flexxoone.com",
    'category': 'account',
    'version': '0.1',
    'data': [
        'views/account_move.xml',
        'views/res_partner.xml',
        'data/catalog_100.xml',
        'views/catalog_100.xml',
        'security/ir.model.access.csv',

    ],
}
