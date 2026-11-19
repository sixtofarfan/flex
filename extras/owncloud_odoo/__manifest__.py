# -*- coding: utf-8 -*-
{
    "name": "OwnCloud / NextCloud Odoo Integration",
    "version": "13.0.1.3.8",
    "category": "Document Management",
    "author": "faOtools",
    "website": "https://faotools.com/apps/13.0/owncloud-nextcloud-odoo-integration-427",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "cloud_base"
    ],
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings.xml"
    ],
    "qweb": [
        
    ],
    "js": [
        
    ],
    "demo": [
        
    ],
    "external_dependencies": {
        "python": [
                "pyocclient",
                "six"
        ]
},
    "summary": "The tool to automatically synchronize Odoo attachments with OwnCloud / NextCloud files in both ways",
    "description": """

For the full details look at static/description/index.html

* Features * 

- Selectable documents types for sync

- Automatic and bilateral integration

- Direct access to NextCloud / OwnCloud items

- Fully integrated and compatible with Enterprise Documents

- NextCloud / OwnCloud Sync logs in Odoo

- Default folders for documents
 
* Extra Notes *

- Typical use cases

- How files and folders are synced from Odoo to NextCloud / OwnCloud

- How items are retrieved from NextCloud / OwnCloud to Odoo

- Internal and public URLs

- How Odoo Enterprise Documents are synced

- A few other peculiarities to take into account



#odootools_proprietary

    """,
    "images": [
        "static/description/main.png"
    ],
    "price": "264.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=46&ticket_version=13.0&url_type_id=3",
}