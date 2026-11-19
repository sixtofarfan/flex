# -*- coding: utf-8 -*-
# Copyright 2020 GregorioCode <Info@gregoriocode.com>

{
    "name": "Solicitud de Pago",
    "version": "13.0.1.0.1",
    "category": "Uncategorized",
    "author": "Ing Gregorio Blanco",
    "website": "https://gregoriocode.com",
    "license": "AGPL-3",
    "depends": [
        'base',
        'sale',
        'account',
        'purchase',
        'sale_order_type',
        'account_base_it',
        'fields_gamma',
        'nanotec_credit_limit',
        'fxo_product_refundable',
        'jp_advance_payment_widget',
        #'account_payment_account_destination',
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/fxo_payment_request.xml",
        "views/main_parameter.xml",
        "wizard/fxo_payment_request_wizard.xml",
        "wizard/invoice_payment_wizard.xml",
        "wizard/move_payment_wizard.xml",
        "wizard/payment_op_wizard.xml",
    ],
    'installable': True,
}
