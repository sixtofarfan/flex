from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_round,float_repr
from datetime import datetime

class AccountClosure(models.Model):
    _name = 'account.closure'
    _description = 'Account Closure'

    name = fields.Char(string='Name', default='Closing fiscal year ')
    closure_model_id = fields.Many2one('account.closure.model', string='Closure model')
    closing_fiscal_year_id = fields.Many2one('account.fiscal.year', string='Closing fiscal year')
    opening_fiscal_year_id = fields.Many2one('account.fiscal.year', string='Opening fiscal year')
    closing_period_id = fields.Many2one('account.period', string='Closing period')
    opening_period_id = fields.Many2one('account.period', string='Opening period')
    closing_journal_id = fields.Many2one('account.journal', string='Closing journal')
    opening_journal_id = fields.Many2one('account.journal', string='Opening journal')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('checked', 'Checked'),
        ('prepared', 'Prepared'),
        ('done', 'Done'),
    ], string='State', default='draft')
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.company),required=True,string='Company')
    account_move_ids = fields.One2many('account.move', 'account_closure_id', string='Account moves')
    # income_tax_move = fields.Many2one('account.move', string='Income Tax Move')

    @api.onchange('closing_fiscal_year_id')
    def _onchange_closing_fiscal_year_id(self):
        self.name = 'Closing fiscal year %s' %self.closing_fiscal_year_id.name

    def checking_balance(self):
        """
        Primero obtenemos el resultado del balance de comprobación de activos y pasivos
        y lo comparamos con el resultado de de cuentas por función y por naturaleza. Los
        tres deben tener el mismo resultado
        """
        # Función
        sql= """select sum(debit) - sum(credit) as total from account_move_line aml
                left join account_account aa on aa.id = aml.account_id
                left join account_move am on aml.move_id = am.id
                where (aa.clasification_sheet = '3' or aa.clasification_sheet = '2')
                and am.date >= '""" + datetime.strftime(self.closing_fiscal_year_id.date_from,"%Y-%m-%d") + """'
                and am.date <= '""" + datetime.strftime(self.closing_period_id.date_end,"%Y-%m-%d") + """'
                and am.state = 'posted'
                and aa.company_id = """ + str(self.env.company.id)
        self.env.cr.execute(sql)
        for line in self.env.cr.fetchall():
            if line[0]:
                by_function_result = float_repr(abs(line[0]),2)
            else:
                by_function_result = 0

        # Naturaleza
        sql= """select sum(debit) - sum(credit) as total from account_move_line aml
                left join account_account aa on aa.id = aml.account_id
                left join account_move am on aml.move_id = am.id
                where (aa.clasification_sheet = '3' or aa.clasification_sheet = '1')
                and am.date >= '""" + datetime.strftime(self.closing_fiscal_year_id.date_from,"%Y-%m-%d") + """'
                and am.date <= '""" + datetime.strftime(self.closing_period_id.date_end,"%Y-%m-%d") + """'
                and am.state = 'posted'
                and aa.company_id = """ + str(self.env.company.id)
        self.env.cr.execute(sql)
        for line in self.env.cr.fetchall():
            if line[0]:
                by_nature_result = float_repr(abs(line[0]),2)
            else:
                by_nature_result = 0
                
        # Activos y pasivos
        sql= """select sum(debit) - sum(credit) as total from account_move_line aml
                left join account_account aa on aa.id = aml.account_id
                left join account_move am on aml.move_id = am.id
                where aa.clasification_sheet = '0'
                and am.date >= '""" + datetime.strftime(self.closing_fiscal_year_id.date_from,"%Y-%m-%d") + """'
                and am.date <= '""" + datetime.strftime(self.closing_period_id.date_end,"%Y-%m-%d") + """'
                and am.state = 'posted'
                and aa.company_id = """ + str(self.env.company.id)
        self.env.cr.execute(sql)
        for line in self.env.cr.fetchall():
            if line[0]:
                assets_liabilities_result = float_repr(abs(line[0]),2)
            else:
                assets_liabilities_result = 0

        if by_nature_result == by_function_result == assets_liabilities_result:
            self.state = 'checked'
        else:
            #TODO mensaje de error
            raise UserError(_('The results of the three columns are not the same: \n\n%s for assets and liabilities \n%s for function \n%s for nature') % (assets_liabilities_result, by_function_result, by_nature_result))

    def make_pre_closure(self):
        # En base al modelo de cierre elegido pasamos por las diferentes etapas de pre cierre
        for stage in self.closure_model_id.closure_stage_ids.filtered(lambda stage: stage.sync_time == 'pre').sorted(key=lambda stage: stage.sequence):
            # En base a la etapa hacemos el procedimiento que corresponda para
            # crear un asiento por etapa
            lines = []
            if stage.type_stage == 'complex':
                # Procedimiento complejo
                for stage_line in stage.complex_line_ids:
                    # Se obtiene el balance de la cuenta origen y se crean 
                    # las lineas del asiento si el balance no es 0
                    balance = self._get_balance_from_account(stage_line.origin_account_id.code)
                    if balance  and  balance != 0:
                        lines.append(self._prepare_lines_for_move(stage_line.origin_account_id, balance * -1))
                        lines.append(self._prepare_lines_for_move(stage_line.destin_account_id, balance))
                # Se crea el asiento de la etapa si existen lineas
                if lines:
                    self._create_move(lines, stage.description)
            else:
                pass
                # Procedimiento simple
                total_balance = 0
                for account in stage.simple_line_ids:
                    # Se obtiene el balance de la cuenta origen y se crea 
                    # la linea del asiento si el balance no es 0
                    balance = self._get_balance_from_account(account.code)
                    if balance and balance != 0:
                        total_balance += balance
                        lines.append(self._prepare_lines_for_move(account, balance * -1))
                    # Luego se envia todo el saldo a la cuenta simple
                if total_balance != 0:
                    lines.append(self._prepare_lines_for_move(stage.account_simple_id, total_balance))
                # Se crea el asiento de la etapa si existen lineas
                if lines:
                    self._create_move(lines, stage.description)
        # Terminar el pre cierre
        self.state = 'prepared'

    def make_post_closure(self):
        # if not self.income_tax_move:
        #     raise UserError(_('Please select the income tax move created to finish the closure procedure.'))
        # En base al modelo de cierre elegido pasamos por las diferentes etapas de post cierre
        for stage in self.closure_model_id.closure_stage_ids.filtered(lambda stage: stage.sync_time == 'post').sorted(key=lambda stage: stage.sequence):
            # En base a la etapa hacemos el procedimiento que corresponda para
            # crear un asiento por etapa
            lines = []
            if stage.type_stage == 'complex':
                # Procedimiento complejo
                for stage_line in stage.complex_line_ids:
                    # Se obtiene el balance de la cuenta origen y se crean 
                    # las lineas del asiento si el balance no es 0
                    balance = self._get_balance_from_account(stage_line.origin_account_id.code)
                    if balance  and  balance != 0:
                        lines.append(self._prepare_lines_for_move(stage_line.origin_account_id, balance * -1))
                        lines.append(self._prepare_lines_for_move(stage_line.destin_account_id, balance))
                # Se crea el asiento de la etapa si existen lineas
                if lines:
                    self._create_move(lines, stage.description)
            else:
                pass
                # Procedimiento simple
                total_balance = 0
                for account in stage.simple_line_ids:
                    # Se obtiene el balance de la cuenta origen y se crea 
                    # la linea del asiento si el balance no es 0
                    balance = self._get_balance_from_account(account.code)
                    if balance and balance != 0:
                        total_balance += balance
                        lines.append(self._prepare_lines_for_move(account, balance * -1))
                    # Luego se envia todo el saldo a la cuenta simple
                if total_balance != 0:
                    lines.append(self._prepare_lines_for_move(stage.account_simple_id, total_balance))
                # Se crea el asiento de la etapa si existen lineas
                if lines:
                    self._create_move(lines, stage.description)
        # Crear el asiento de cierre
        lines_closure = []
        lines_opening = []
        for account in self.env['account.account'].search([]):
            balance = self._get_balance_from_account(account.code)
            if balance and balance != 0:
                lines_closure.append(self._prepare_lines_for_move(account, balance * -1))
                lines_opening.append(self._prepare_lines_for_move(account, balance))
        self._create_move(lines_closure, _('Closure Move'))
        self._create_move(lines_opening, _('Opening Move'), True)
        # Terminar el cierre
        self.state = 'done'

    def _get_balance_from_account(self, account_code):
        sql= f"""select sum(debit) - sum(credit) as total from account_move_line aml
                left join account_account aa on aa.id = aml.account_id
                left join account_move am on aml.move_id = am.id
                where aa.code = '{account_code}'
                and am.date >= '""" + datetime.strftime(self.closing_fiscal_year_id.date_from,"%Y-%m-%d") + """'
                and am.date <= '""" + datetime.strftime(self.closing_period_id.date_end,"%Y-%m-%d") + """'
                and am.state = 'posted'
                and aa.company_id = """ + str(self.env.company.id)
        self.env.cr.execute(sql)
        for line in self.env.cr.fetchall():
                account_value_results = line[0]
        return account_value_results
    
    def _prepare_lines_for_move(self, account_id, balance, is_opening=False):
        value = {
            'type_document_id': self.env['einvoice.catalog.01'].search([('code','=','00')]).id,
            'nro_comp': _('CLOSURE %s') %self.closing_fiscal_year_id.name if not is_opening else _('OPENING %s') %self.opening_fiscal_year_id.name,
            'account_id': account_id.id,
            'currency_id': account_id.currency_id.id,
            'balance': balance,
            'debit': abs(balance) if balance > 0 else 0,
            'credit':abs(balance) if balance < 0 else 0,
        }
        return value
    
    def _create_move(self, lines, description, is_opening=False):                
        self.env['account.move'].create({
            'name': '/',
            'account_closure_id': self.id,
            'date': self.closing_period_id.date_end if not is_opening else self.opening_period_id.date_start,
            'journal_id': self.closing_journal_id.id if not is_opening else self.opening_journal_id.id,
            'glosa': description,
            'type': 'entry',
            'is_opening_close': True,
            'line_ids': [(0,0, line) for line in lines],
        }).post()

    def cancel(self):
        if self.state == 'checked':
            self.state = 'draft'
        if self.state == 'prepared':
            for move in self.account_move_ids:
                move.button_draft()
                move.with_context(force_delete=True).unlink()
            self.state = 'checked'
        if self.state == 'done':
            self.state = 'prepared'
            for move in self.account_move_ids:
                if self.glosa in (_('Closure Move'),_('Opening Move')):
                    move.button_draft()
                    move.with_context(force_delete=True).unlink()

class AccountClosureLine(models.Model):
    _name = 'account.closure.line'
    _description = 'Account Closure Line'

    stage_id = fields.Many2one('account.closure.stage', string='Stage')
    origin_account_id = fields.Many2one('account.account', 'Origin acccount')
    destin_account_id = fields.Many2one('account.account', 'Destination account')

class AccountClosureStage(models.Model):
    _name = 'account.closure.stage'
    _description = 'Account Closure Stage'

    sequence = fields.Integer(string='Sequence')
    name = fields.Char('Stage name')
    description = fields.Char('Description')
    type_stage = fields.Selection([
        ('simple', 'Simple'),
        ('complex', 'Complex')
    ], string='Type of stage')
    complex_line_ids = fields.One2many('account.closure.line', 'stage_id', string='Complex line ids', copy=False)
    simple_line_ids = fields.Many2many('account.account', string='Simple line ids', copy=False)
    account_simple_id = fields.Many2one('account.account', string='Destination account', copy=False)
    sync_time = fields.Selection([
        ('pre', 'Before Income Tax'),
        ('post', 'After Income Tax'),
    ], string='Synchronization Time')

class AccountClosureModel(models.Model):
    _name = 'account.closure.model'
    _description = 'Account Closure Model'

    name = fields.Char(string='Model name')
    closure_stage_ids = fields.Many2many('account.closure.stage', string='Stage', copy=False)