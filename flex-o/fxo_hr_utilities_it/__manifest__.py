# -*- encoding: utf-8 -*-
{
    'name': 'FXO Hr Utilities',
    'category': 'hr',
    'author': 'Flexxone-HR',
    'depends': ['hr_utilities_it'],
    'version': '1.0',
    'description': """
	    - Modulo que modifica el reporte de LIQUIDACION DE LA DISTRIBUCION DE LAS UTILIDADES, se mantiene el mismo botón solo cambia que se genera con Qweb'
        - Elimina la duplicación de empleados en las lineas con la misma informacion'
        - Envio por correo electronico de la liquidacion de utilidades, tanto masivo como por empleado
	""",
    'auto_install': False,
    'demo': [],
    'data': [
        'views/hr_utilities_it.xml',
        'wizard/send_email_utilities_wizard.xml',
        'reports/report_paperformat.xml',
        'reports/report_hr_utilities_it_all.xml',
    ],
    'installable': True
}
