# -*- coding: utf-8 -*-
{
    'name':
    " SQL ITGRUPO ",
    'summary':
        """  SQL ITGRUPO  """,
    'description':
        """ SQL ITGRUPO
        debes de tener acceso Superuser en postgres si no lo tienes ejecuta este comando "ALTER USER tu_rol WITH SUPERUSER;"  """,
    'author': "Flexxoone",
    'website': "http://flexxoone.com/",
    'category': 'sale',
    'version': '0.1',
    'depends':[],
    'data': [
        'sql/cuentas_corrientes.sql',
        'sql/estados_financieros_peruanos.sql',
        'sql/kardex_fisico.sql',
        'sql/libro_contables_peruanos.sql',
    ],
}