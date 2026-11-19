# -*- coding: utf-8 -*-
{
    'name': "Peruvian POS  Retail",

    'summary': """
        Peruvian Management POS Retail""",

    'description': """
        Peruvian Management POS Retail
    """,

    'author': "E&M",
    'website': "https://www.eymperu.net",
    'category': 'Localization/Peruvian',
    'version': '0.1',
    'depends': [
        'point_of_sale',
        'amount_to_text',
        'pos_journal_sequence',
        'l10n_pe_vat',
        'pos_ticket_extend',
        'pos_retail'
    ],

    # always loaded
    'data': [
        'views/l10n_pe_pos_templates.xml'
    ],
    'qweb': [
        'static/src/xml/pos.xml'
    ],
}
