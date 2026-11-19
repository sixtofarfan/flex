# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.tools.translate import _
from operator import itemgetter
import logging
_logger = logging.getLogger(__name__) 


class res_partner(models.Model):
    _inherit = "res.partner"


    def _get_default_currency(self):
        #user = self.env['res.users'].browse()
        return self.env.user.company_id.currency_id.id
        #return user.company_id.currency_id.id

    credit_ids = fields.One2many("res.partner.credit.detail", "partner_id", "")
    currency_id = fields.Many2one("res.currency", "Moneda", required=True, domain=[('name','in',['PEN','USD'])], readonly=True, default=_get_default_currency)
    credit_limit2 = fields.Float(compute='_get_credit_limit', string="Credit limit", store=True)
    status_credit = fields.Selection([
        ('active', 'Activo'),
        ('suspension', 'Suspendido'),
        ('annulment', 'Anulado')], "Estado de linea de crédito", default=False)
    credit_balance = fields.Monetary(compute='_get_credit_limit', string="Crédito disponible")
    nro_documento = fields.Char(string='Nro. Documento')

    @api.depends('credit_ids', 'check_credit_limit', 'credit')
    def _get_credit_limit(self):
        '''
        res = {}.fromkeys(self.ids, 0.0)
        return res
        if self.ids:
            self.env.cr.execute("""select rp.id, sum(amount_debit) - sum(amount_credit) as credit_limit from res_partner rp
                                inner join res_partner_credit_detail rpcd on(rpcd.partner_id=rp.id and rpcd.currency_id=rp.currency_id and rpcd.state='approve')
                                where rp.id in %s
                                group by rp.id""", (tuple(self.ids),))
            res.update(dict(self.env.cr.fetchall()))
        return res
        '''
        for record in self:
            record.credit_limit2 = sum([((item.amount_debit - item.amount_credit) if item.state=='approve' else 0) for item in record.credit_ids])


            ## check if this is a customer who doesn't need to be enforced
            if not record.check_credit_limit:
                return 1

            ## Find not invoiced sale orders
            all_so_notinv = self.env['sale.order'].search([
                    ('partner_id', '=', record.id),
                    ('company_id', '=', record.company_id.id),
                    ('invoice_status', 'in', ['to invoice']),
                ])

            due_notinv=0
            for so in all_so_notinv:            
                due=so.amount_total
                due_notinv+=due

            new_balance = 1 #record.credit

            ##get some parameters
            includenot = self.env['sale.main.parameter'].search([],limit=1).include_not_invoiced

            if includenot:
                new_balance=new_balance+due_notinv

            record.credit_balance = record.credit_limit2 - new_balance


    #Migracion de modulo
    check_credit_limit = fields.Boolean('Enforce the Credit Limit for Sale orders', default=True,required=True)
    #my_credit_limit = fields.Float('The Credit Limit :',default=0,required=True) 
    my_credit_agent_change = fields.Boolean('Allow Sale Managers to modify this limit ?', default=True)
    my_credit_is_over = fields.Boolean('is over credit ?', compute='compute_my_credit_is_over')
    date_validity = fields.Date(string='Fecha Validez', readonly=True)
    #over_limit = fields.Float('Debt over Limit', compute='compute_over_limit', search='search_over_limit')


    def search_over_limit(self, operation, operand):
        _logger.debug(' \n\n \t Having a shitty time here  \n\n\n'+str(self.display_name)+'\n\n\n')

        res = self._cr.execute('''
            SELECT partner.id, SUM(aml.amount_residual),credit_limit2
            FROM res_partner partner
            LEFT JOIN account_move_line aml ON aml.partner_id = partner.id
            RIGHT JOIN account_account acc ON aml.account_id = acc.id
            WHERE acc.internal_type = 'receivable' 
              AND NOT acc.deprecated
            GROUP BY partner.id
            HAVING  COALESCE(SUM(aml.amount_residual), 0) > partner.credit_limit2 ''' )
        res = self._cr.fetchall()
        for row in res:
                    _logger.debug(' \n\n \t '+str(row))
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', map(itemgetter(0), res))]


    @api.depends('credit','debit', 'credit_limit2')
    def _get_credit_balance(self):
        _logger.debug(' \n\n \t Calling Over Limit \n\n\n')
        for item in self:           
            item.over_limit=item.credit-item.credit_limit2
        
    

    @api.depends('credit','debit', 'credit_limit2')
    def compute_my_credit_is_over(self):
        _logger.debug(' \n\n \t CHECKING OVER LIMIT FOR CUSTOMER \n\n\n')
#       self.ensure_one();
        for item in self:
            if item.credit_limit2<item.credit:
                item.my_credit_is_over=True
            else:
                item.my_credit_is_over=False
