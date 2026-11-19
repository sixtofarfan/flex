from odoo import api, fields, models, _

class CountryState(models.Model):
    _inherit = 'res.country.state'

    is_exonerated = fields.Boolean("Is Exonerated")

class City(models.Model):
    _inherit = 'res.city'

    is_exonerated = fields.Boolean("Is Exonerated")

class L10nPeResCityDistrict(models.Model):
    _inherit = 'l10n_pe.res.city.district'

    is_exonerated = fields.Boolean("Is Exonerated")