# -*- coding: utf-8 -*-
# © <2016> <Flexxoone>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "fxo invoice stock picking",
    "summary": "Muestra Guías en una pestaña de factura",
    "category": "Uncategorized",
    "website": "http://flexxoone.com/",
    "author": "Flexxoone",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "base",
        "sale",
        #"invoice_so"
    ],
    "data": [
        "view/picking_ids.xml"
    ],
    #"demo": [],
    #"qweb": []
} 
