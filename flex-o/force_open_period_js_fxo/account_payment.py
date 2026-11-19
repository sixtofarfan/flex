from odoo import models, fields, api




class AccountPayment(models.Model):
    _inherit = "account.payment"
    #funcion Validar para registrar pago
    #lo que se hace es ver si elapgo a realizarse es de una factura
    #donde el periodo esta cerrado , lo vuelce a abrir el periodo
    #hace el pago y lo veulve a cerrar
    #aqui no paso nada :'vvvv
    def post(self):
        #abrir el periodo si es el rango de fecha es
        #diferente a la fecha actual

        array_periodos_done = []

        for rec in self:
            if rec.invoice_ids:
                for move in rec.invoice_ids:
                    #periodo actual
                    period_move = self.env['account.journal.period'].search(
                        [('company_id', '=', move.company_id.id), ('date_start', '<=', move.date),
                         ('date_end', '>=', move.date)], limit=1)
                    periodo_wizard = self.env['account.journal.period'].search(
                        [('company_id', '=', move.company_id.id), ('date_start', '<=', self.payment_date),
                         ('date_end', '>=', self.payment_date)], limit=1)

                    if periodo_wizard !=  period_move and period_move.state == 'done':
                        period_move.state = 'draft'
                        array_periodos_done.append(period_move)

        res = super(AccountPayment, self).post()


        if array_periodos_done:
            for p in array_periodos_done:
                p.state = 'done'


        return res
