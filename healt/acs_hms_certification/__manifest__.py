# -*- coding: utf-8 -*-
#╔══════════════════════════════════════════════════════════════════╗
#║                                                                  ║
#║                ╔═══╦╗       ╔╗  ╔╗     ╔═══╦═══╗                 ║
#║                ║╔═╗║║       ║║ ╔╝╚╗    ║╔═╗║╔═╗║                 ║
#║                ║║ ║║║╔╗╔╦╦══╣╚═╬╗╔╬╗ ╔╗║║ ╚╣╚══╗                 ║
#║                ║╚═╝║║║╚╝╠╣╔╗║╔╗║║║║║ ║║║║ ╔╬══╗║                 ║
#║                ║╔═╗║╚╣║║║║╚╝║║║║║╚╣╚═╝║║╚═╝║╚═╝║                 ║
#║                ╚╝ ╚╩═╩╩╩╩╩═╗╠╝╚╝╚═╩═╗╔╝╚═══╩═══╝                 ║
#║                          ╔═╝║     ╔═╝║                           ║
#║                          ╚══╝     ╚══╝                           ║
#║ SOFTWARE DEVELOPED AND SUPPORTED BY ALMIGHTY CONSULTING SERVICES ║
#║                   COPYRIGHT (C) 2016 - TODAY                     ║
#║                   http://www.almightycs.com                      ║
#║                                                                  ║
#╚══════════════════════════════════════════════════════════════════╝
{
    'name': 'HMS Certificate Management System',
    'summary': """This Module will Add functionality to provide certificate to Patients. Maintain history of certificate allocation.""",
    'description': """
        This Module will Add functionality to provide certificate to Patients. Maintain history of certificate allocation.
        Certification hospital certificate medical certificate patient certification ACS HMS
    """,
    'version': '1.0.5',
    'category': 'Hospital Management System',
    'author': 'Odoo',
    'support': 'info@sistemerp.com',
    'website': 'https://www.odoo.com',
    'license': 'OPL-1',
    'depends': ["acs_hms", "acs_certification"],
    'data' : [
        'security/security.xml',
        'views/certificate_management_view.xml',
    ],
    'images': [
        'static/description/hms_certificate_almightycs_cover.jpg',
    ],
    'installable': True,
    'application': True,
    'sequence': 2,
    'price': 100,
    'currency': 'USD',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: