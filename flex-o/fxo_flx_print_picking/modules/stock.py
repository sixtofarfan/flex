# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    nombre_mes = fields.Char(
        string=u'Mes',
        compute='_nombre_mes'    )
    dia= fields.Char(
        string=u'Mes',
        compute='_nombre_dia'    )
    years= fields.Char(
        string=u'Mes',
        compute='_nombre_year'    )

    type_print = fields.Boolean(string='Usar Lineas para la guia')

  

    def _nombre_dia(self):
        for item in self:
            dia= slice(8,11)
            item.dia = item.fecha_kardex[dia]

    def _nombre_year(self):
        for item in self:
            dia = slice(2,4)
            item.years = item.fecha_kardex[dia]

    def _nombre_mes(self):
        for item in self:
            mes = slice(5,7)
            fecha = item.fecha_kardex
            dato = fecha[mes]
            if dato == '01':
                item.nombre_mes = 'Enero'
            elif  dato == '02':
                item.nombre_mes = 'Febrero'
            elif  dato == '03':
                item.nombre_mes = 'Marzo'
            elif  dato == '04':
                item.nombre_mes = 'Abril'
            elif  dato == '05':
                item.nombre_mes = 'Mayo'
            elif  dato == '06':
                item.nombre_mes = 'Junio'
            elif  dato == '07':
                item.nombre_mes = 'Julio'
            elif  dato == '08':
                item.nombre_mes = 'Agosto'
            elif  dato == '09':
                item.nombre_mes = 'Setiembre'
            elif  dato == '10':
                item.nombre_mes = 'Octubre'
            elif  dato == '11':
                item.nombre_mes = 'Noviembre'
            elif  dato == '12':
                item.nombre_mes = 'Diciembre'
