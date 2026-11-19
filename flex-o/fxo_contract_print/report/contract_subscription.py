# -*- coding: utf-8 -*-

import time

import odoo.addons.decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import Warning

from jinja2 import Template


class report_sale_subscription_contract(models.AbstractModel):
    _name = 'report.fxo_contract_print.report_sale_subscription_contract'

    @api.model
    def _get_report_values(self, docids, data=None):
        edi_sale = self.env.ref('fxo_contract_print.report_sale_subscription_contract', False)
        subscription_report_form = self.env['sale.subscription'].browse(docids)[0].description_contract_id.description_contract
        if edi_sale:
            body_html = _("""
        <t t-name="fxo_contract_print.report_sale_subscription_contract">
            <t t-call="web.html_container">
                   <t t-if="company_id">
                <t t-set="company" t-value="company_id"/>
            </t>
            <t t-elif="o and 'company_id' in o">
                <t t-set="company" t-value="o.company_id.sudo()"/>
            </t>
            <t t-else="else">
                <t t-set="company" t-value="res_company"/>
            </t>
        <div t-attf-class="header o_company_#1_layout">
            <div class="row">
                <div class="col-3 mb4">
                    <img t-if="company.logo" t-att-src="image_data_uri(company.logo)" style="max-height: 45px;" alt="Logo"/>
                </div>
                <div class="col-9 text-right" style="margin-top:22px;" t-esc="'VS2020'" name="moto"/>
            </div>
            <div t-if="company.logo or company.report_header" class="row zero_min_height">
                <div class="col-12">
                    <div style="border-bottom: 1px solid black;"/>
                </div>
            </div>
        </div>
            <div t-attf-class="article o_report_layout_standard o_company_#1_layout"  t-att-data-oe-model="o and o._name" t-att-data-oe-id="o and o.id" t-att-data-oe-lang="o and o.env.context.get('lang')">
        
                <t t-foreach="docs" t-as="o">
                    <div class="page">
                        """+subscription_report_form+"""
                    </div>
                </t>
            </div>


        <div t-attf-class="footer o_standard_footer o_company_#1_layout">
            <div class="text-center" style="border-top: 1px solid black;">
                <div>
                    Page: <span class="page"/> / <span class="topage"/>
                </div>
            </div>
        </div>

            </t>
        </t>""")

            edi_sale.write({
                'arch_base': body_html,
            })
        return {
            'doc_ids': docids,
            'doc_model': 'sale.subscription',
            'docs': self.env['sale.subscription'].browse(docids),
            'report_type': data.get('report_type') if data else '',
        }

    #@api.model
    #def _get_report_values(self, docids, data=None):

    #    report_obj = self.env['report']
    #    self.model = self.env.context.get('active_model')

    #    docargs = {
    #        'doc_ids': self.ids,
    #        'doc_model': self.model,
    #        'docs': self.env['sale.subscription'].browse(docids),
    #        'time': time,
    #        'fecha_str': self._fecha_str,
    #        'conversion': self._conversion,

    #    }
    #    return report_obj.render('fxo_contract_print.report_sale_subscription_contract', docargs)


    def _fecha_str(self, city):

        date = time.strftime("%Y-%m-%d")
        day = time.strftime('%d', time.strptime(date,'%Y-%m-%d'))
        month = time.strftime('%B', time.strptime(date,'%Y-%m-%d')).upper()
        year = time.strftime('%Y', time.strptime(date,'%Y-%m-%d'))
        fecha = str(city).upper() + " , " + " " + day + " de " + month + " del " + year

        return fecha

    def get_num_month(self, start,end):
        num_month = 0
        for d in arrow.Arrow.range('month',start,end):
            num_month +=1
        return num_month
