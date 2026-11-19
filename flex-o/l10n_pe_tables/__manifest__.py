# -*- coding: utf-8 -*-
# ©  2015 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Tables Sunat',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'category': '',
    'author': "Tables Sunat",
    'summary': "Tables Sunat",
    'website': 'http://flexxoone.com/',
    'depends': [
        'account_base_it'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/einvoice_catalog_04.xml',
        'data/einvoice_catalog_03.xml',
        'views/einvoice_catalog_03.xml',
        'views/einvoice_catalog_04.xml'
    ],
    'installable': True,
}
