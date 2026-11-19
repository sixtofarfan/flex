# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64


class WorksheetF2Wizard(models.TransientModel):
    _name = 'worksheet.f2.wizard'

    name = fields.Char()
    company_id = fields.Many2one('res.company', string=u'Compañia', required=True,
                                 default=lambda self: self.env.company, readonly=True)
    fiscal_year_id = fields.Many2one('account.fiscal.year', string='Ejercicio', required=True)
    period = fields.Many2one('account.period', string='Periodo', required=True)
    type_show = fields.Selection([('pantalla', 'Pantalla'), ('excel', 'Excel')], default='pantalla',
                                 string=u'Mostrar en', required=True)
    currency = fields.Selection([('pen', 'PEN'), ('usd', 'USD')], string=u'Moneda', default='pen', required=True)
    show_account_entries = fields.Boolean(string='Mostrar Rubros de Cuenta', default=False)
    level = fields.Selection([('balance', 'Balance'), ('register', 'Registro')], default='balance', string='Nivel',
                             required=True)

    @api.onchange('company_id')
    def get_fiscal_year(self):
        if self.company_id:
            fiscal_year = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)],
                                                            limit=1).fiscal_year
            if fiscal_year:
                self.fiscal_year_id = fiscal_year.id
            else:
                raise UserError(
                    u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

    # URO metodo modificado para lograr reducir el tiempo de respuesta del reporte
    def _get_f2_register_sql(self):
        sql = """	
            DELETE FROM f2_register WHERE company_id = {company} AND res_user_id = {user_id};	
			SELECT 
			    mayor,
				cuenta,
				nomenclatura,
				debe_inicial,
				haber_inicial,
				debe,
				haber,
				saldo_deudor,
				saldo_acreedor,
				activo,
				pasivo,
				perdinat,
				ganannat,
				perdifun,
				gananfun,
				rubro
				FROM get_f2_register('{period}',{company},'{currency}')
		""".format(
            period=self.period.code,
            company=self.company_id.id,
            currency=self.currency,
            user_id=self.env.user.id
        )
        self._cr.execute(sql)
        lines = self.env.cr.fetchall()
        vals = []
        sum_debe_inicial = 0
        sum_haber_inicial = 0
        sum_debe = 0
        sum_haber = 0
        sum_saldo_deudor = 0
        sum_saldo_acreedor = 0
        sum_activo = 0
        sum_pasivo = 0
        sum_perdinat = 0
        sum_ganannat = 0
        sum_perdifun = 0
        sum_gananfun = 0
        for line in lines:
            sum_debe_inicial += line[3]
            sum_haber_inicial += line[4]
            sum_debe += line[5]
            sum_haber += line[6]
            sum_saldo_deudor += line[7]
            sum_saldo_acreedor += line[8]
            sum_activo += line[9]
            sum_pasivo += line[10]
            sum_perdinat += line[11]
            sum_ganannat += line[12]
            sum_perdifun += line[13]
            sum_gananfun += line[14]
            vals.append(
                {
                    "period": self.period.code,
                    "mayor": line[0],
                    "cuenta": line[1],
                    "nomenclatura": line[2],
                    "debe_inicial": line[3],
                    "haber_inicial": line[4],
                    "debe": line[5],
                    "haber": line[6],
                    "saldo_deudor": line[7],
                    "saldo_acreedor": line[8],
                    "activo": line[9],
                    "pasivo": line[10],
                    "perdinat": line[11],
                    "ganannat": line[12],
                    "perdifun": line[13],
                    "gananfun": line[14],
                    "rubro": line[15],
                    "company_id": self.env.company.id,
                    "res_user_id": self.env.user.id
                })
        dict_sumas = {
            "period": self.period.code,
            "mayor": None,
            "cuenta": None,
            "nomenclatura": 'SUMAS',
            "debe_inicial": sum_debe_inicial,
            "haber_inicial": sum_haber_inicial,
            "debe": sum_debe,
            "haber": sum_haber,
            "saldo_deudor": sum_saldo_deudor,
            "saldo_acreedor": sum_saldo_acreedor,
            "activo": sum_activo,
            "pasivo": sum_pasivo,
            "perdinat": sum_perdinat,
            "ganannat": sum_ganannat,
            "perdifun": sum_perdifun,
            "gananfun": sum_gananfun,
            "rubro": None,
            "company_id": self.env.company.id,
            "res_user_id": self.env.user.id
        }
        gp_debe_inicial = 0
        gp_haber_inicial = 0
        gp_debe = 0
        gp_haber = 0
        gp_saldo_deudor = 0
        gp_saldo_acreedor = 0
        gp_activo = 0
        gp_pasivo = 0
        gp_perdinat = 0
        gp_ganannat = 0
        gp_perdifun = 0
        gp_gananfun = 0
        if sum_debe_inicial < sum_haber_inicial:
            gp_debe_inicial = sum_haber_inicial - sum_debe_inicial
        if sum_debe_inicial > sum_haber_inicial:
            gp_haber_inicial = sum_debe_inicial - sum_haber_inicial
        if sum_debe < sum_haber:
            gp_debe = sum_haber - sum_debe
        if sum_debe > sum_haber:
            gp_haber = sum_debe - sum_haber
        if sum_saldo_deudor < sum_saldo_acreedor:
            gp_saldo_deudor = sum_saldo_acreedor - sum_saldo_deudor
        if sum_saldo_deudor > sum_saldo_acreedor:
            gp_saldo_acreedor = sum_saldo_deudor - sum_saldo_acreedor
        if sum_activo < sum_pasivo:
            gp_activo = sum_pasivo - sum_activo
        if sum_activo > sum_pasivo:
            gp_pasivo = sum_activo - sum_pasivo
        if sum_perdinat < sum_ganannat:
            gp_perdinat = sum_ganannat - sum_perdinat
        if sum_perdinat > sum_ganannat:
            gp_ganannat = sum_perdinat - sum_ganannat
        if sum_perdifun < sum_gananfun:
            gp_perdifun = sum_gananfun - sum_perdifun
        if sum_perdifun > sum_gananfun:
            gp_gananfun = sum_perdifun - sum_gananfun
        dict_perdi_ganan = {
            "period": self.period.code,
            "mayor": None,
            "cuenta": None,
            "nomenclatura": 'UTILIDAD O PERDIDA',
            "debe_inicial": gp_debe_inicial,
            "haber_inicial": gp_haber_inicial,
            "debe": gp_debe,
            "haber": gp_haber,
            "saldo_deudor": gp_saldo_deudor,
            "saldo_acreedor": gp_saldo_acreedor,
            "activo": gp_activo,
            "pasivo": gp_pasivo,
            "perdinat": gp_perdinat,
            "ganannat": gp_ganannat,
            "perdifun": gp_perdifun,
            "gananfun": gp_gananfun,
            "rubro": None,
            "company_id": self.env.company.id,
            "res_user_id": self.env.user.id
        }
        vals.append(dict_sumas)
        vals.append(dict_perdi_ganan)
        self.env["f2.register"].create(vals)

    # URO comentado
    # def _get_f2_register_sql(self):
    #         sql = """
    # 		--DROP VIEW IF EXISTS f2_register;
    # 		--CREATE OR REPLACE VIEW f2_register AS
    # 		--(
    # 			DELETE FROM f2_register WHERE company_id = {company} AND res_user_id = {user_id};
    # 			SELECT row_number() OVER () AS id,
    # 			'{period}' as period,
    # 			* FROM (
    # 			SELECT *
    # 			FROM get_f2_register('{period}',{company},'{currency}')
    # 			UNION ALL
    # 			SELECT
    # 			null::text as mayor,
    # 			null::character varying as cuenta,
    # 			'SUMAS'::text as nomenclatura,
    # 			sum(debe_inicial) as debe_inicial,
    # 			sum(haber_inicial) as haber_inicial,
    # 			sum(debe) as debe,
    # 			sum(haber) as haber,
    # 			sum(saldo_deudor) as saldo_deudor,
    # 			sum(saldo_acreedor) as saldo_acreedor,
    # 			sum(activo) as activo,
    # 			sum(pasivo) as pasivo,
    # 			sum(perdinat) as perdinat,
    # 			sum(ganannat) as ganannat,
    # 			sum(perdifun) as perdifun,
    # 			sum(gananfun) as gananfun,
    # 			null::text as rubro
    # 			FROM get_f2_register('{period}',{company},'{currency}')
    # 			UNION ALL
    # 			SELECT
    # 			null::text as mayor,
    # 			null::character varying as cuenta,
    # 			'UTILIDAD O PERDIDA'::text as nomenclatura,
    # 			case
    # 				when sum(debe_inicial) < sum(haber_inicial)
    # 				then sum(haber_inicial) - sum(debe_inicial)
    # 				else 0
    # 			end as debe_inicial,
    # 			case
    # 				when sum(debe_inicial) > sum(haber_inicial)
    # 				then sum(debe_inicial) - sum(haber_inicial)
    # 				else 0
    # 			end as haber_inicial,
    # 			case
    # 				when sum(debe) < sum(haber)
    # 				then sum(haber) - sum(debe)
    # 				else 0
    # 			end as debe,
    # 			case
    # 				when sum(debe) > sum(haber)
    # 				then sum(debe) - sum(haber)
    # 				else 0
    # 			end as haber,
    # 			case
    # 				when sum(saldo_deudor) < sum(saldo_acreedor)
    # 				then sum(saldo_acreedor) - sum(saldo_deudor)
    # 				else 0
    # 			end as saldo_deudor,
    # 			case
    # 				when sum(saldo_deudor) > sum(saldo_acreedor)
    # 				then sum(saldo_deudor) - sum(saldo_acreedor)
    # 				else 0
    # 			end as saldo_acreedor,
    # 			case
    # 				when sum(activo) < sum(pasivo)
    # 				then sum(pasivo) - sum(activo)
    # 				else 0
    # 			end as activo,
    # 			case
    # 				when sum(activo) > sum(pasivo)
    # 				then sum(activo) - sum(pasivo)
    # 				else 0
    # 			end as pasivo,
    # 			case
    # 				when sum(perdinat) < sum(ganannat)
    # 				then sum(ganannat) - sum(perdinat)
    # 				else 0
    # 			end as perdinat,
    # 			case
    # 				when sum(perdinat) > sum(ganannat)
    # 				then sum(perdinat) - sum(ganannat)
    # 				else 0
    # 			end as ganannat,
    # 			case
    # 				when sum(perdifun) < sum(gananfun)
    # 				then sum(gananfun) - sum(perdifun)
    # 				else 0
    # 			end as perdifun,
    # 			case
    # 				when sum(perdifun) > sum(gananfun)
    # 				then sum(perdifun) - sum(gananfun)
    # 				else 0
    # 			end as gananfun,
    # 			null::text as rubro
    # 			FROM get_f2_register('{period}',{company},'{currency}')
    # 				)T
    # 		--)
    # 		""".format(
    #             period=self.period.code,
    #             company=self.company_id.id,
    #             currency=self.currency,
    #             user_id=self.env.user.id
    #         )
    #         # print(sql)
    #         # return sql
    #         self._cr.execute(sql)
    #         lines = self.env.cr.fetchall()
    #         vals = []
    #         for line in lines:
    #             vals.append(
    #                 {
    #                     "period": line[1],
    #                     "mayor": line[2],
    #                     "cuenta": line[3],
    #                     "nomenclatura": line[4],
    #                     "debe_inicial": line[5],
    #                     "haber_inicial": line[6],
    #                     "debe": line[7],
    #                     "haber": line[8],
    #                     "saldo_deudor": line[9],
    #                     "saldo_acreedor": line[10],
    #                     "activo": line[11],
    #                     "pasivo": line[12],
    #                     "perdinat": line[13],
    #                     "ganannat": line[14],
    #                     "perdifun": line[15],
    #                     "gananfun": line[16],
    #                     "rubro": line[17],
    #                     "company_id": self.env.company.id,
    #                     "res_user_id": self.env.user.id
    #                 })
    #         self.env["f2.register"].create(vals)

    # URO metodo modificado para lograr reducir el tiempo de respuesta del reporte
    def _get_f2_balance_sql(self):
        sql = """ DELETE FROM f2_balance WHERE company_id = {company} AND res_user_id = {user_id};	
        		    SELECT 
                    mayor,                    
                    nomenclatura,
                    debe_inicial,
                    haber_inicial,
                    debe,
                    haber,
                    saldo_deudor,
                    saldo_acreedor,
                    activo,
                    pasivo,
                    perdinat,
                    ganannat,
                    perdifun,
                    gananfun                    
        			FROM get_f2_balance('{period}',{company},'{currency}')
        		""".format(
            period=self.period.code,
            company=self.company_id.id,
            currency=self.currency,
            user_id=self.env.user.id
        )
        self._cr.execute(sql)
        lines = self.env.cr.fetchall()
        vals = []
        sum_debe_inicial = 0
        sum_haber_inicial = 0
        sum_debe = 0
        sum_haber = 0
        sum_saldo_deudor = 0
        sum_saldo_acreedor = 0
        sum_activo = 0
        sum_pasivo = 0
        sum_perdinat = 0
        sum_ganannat = 0
        sum_perdifun = 0
        sum_gananfun = 0
        for line in lines:
            sum_debe_inicial += line[2]
            sum_haber_inicial += line[3]
            sum_debe += line[4]
            sum_haber += line[5]
            sum_saldo_deudor += line[6]
            sum_saldo_acreedor += line[7]
            sum_activo += line[8]
            sum_pasivo += line[9]
            sum_perdinat += line[10]
            sum_ganannat += line[11]
            sum_perdifun += line[12]
            sum_gananfun += line[13]
            vals.append(
                {
                    "period": self.period.code,
                    "mayor": line[0],
                    "nomenclatura": line[1],
                    "debe_inicial": line[2],
                    "haber_inicial": line[3],
                    "debe": line[4],
                    "haber": line[5],
                    "saldo_deudor": line[6],
                    "saldo_acreedor": line[7],
                    "activo": line[8],
                    "pasivo": line[9],
                    "perdinat": line[10],
                    "ganannat": line[11],
                    "perdifun": line[12],
                    "gananfun": line[13],
                    "company_id": self.env.company.id,
                    "res_user_id": self.env.user.id
                })
        dict_sumas = {
            "period": self.period.code,
            "mayor": None,
            "nomenclatura": 'SUMAS',
            "debe_inicial": sum_debe_inicial,
            "haber_inicial": sum_haber_inicial,
            "debe": sum_debe,
            "haber": sum_haber,
            "saldo_deudor": sum_saldo_deudor,
            "saldo_acreedor": sum_saldo_acreedor,
            "activo": sum_activo,
            "pasivo": sum_pasivo,
            "perdinat": sum_perdinat,
            "ganannat": sum_ganannat,
            "perdifun": sum_perdifun,
            "gananfun": sum_gananfun,
            "company_id": self.env.company.id,
            "res_user_id": self.env.user.id
        }
        gp_debe_inicial = 0
        gp_haber_inicial = 0
        gp_debe = 0
        gp_haber = 0
        gp_saldo_deudor = 0
        gp_saldo_acreedor = 0
        gp_activo = 0
        gp_pasivo = 0
        gp_perdinat = 0
        gp_ganannat = 0
        gp_perdifun = 0
        gp_gananfun = 0
        if sum_debe_inicial < sum_haber_inicial:
            gp_debe_inicial = sum_haber_inicial - sum_debe_inicial
        if sum_debe_inicial > sum_haber_inicial:
            gp_haber_inicial = sum_debe_inicial - sum_haber_inicial
        if sum_debe < sum_haber:
            gp_debe = sum_haber - sum_debe
        if sum_debe > sum_haber:
            gp_haber = sum_debe - sum_haber
        if sum_saldo_deudor < sum_saldo_acreedor:
            gp_saldo_deudor = sum_saldo_acreedor - sum_saldo_deudor
        if sum_saldo_deudor > sum_saldo_acreedor:
            gp_saldo_acreedor = sum_saldo_deudor - sum_saldo_acreedor
        if sum_activo < sum_pasivo:
            gp_activo = sum_pasivo - sum_activo
        if sum_activo > sum_pasivo:
            gp_pasivo = sum_activo - sum_pasivo
        if sum_perdinat < sum_ganannat:
            gp_perdinat = sum_ganannat - sum_perdinat
        if sum_perdinat > sum_ganannat:
            gp_ganannat = sum_perdinat - sum_ganannat
        if sum_perdifun < sum_gananfun:
            gp_perdifun = sum_gananfun - sum_perdifun
        if sum_perdifun > sum_gananfun:
            gp_gananfun = sum_perdifun - sum_gananfun
        dict_perdi_ganan = {
            "period": self.period.code,
            "mayor": None,
            "nomenclatura": 'UTILIDAD O PERDIDA',
            "debe_inicial": gp_debe_inicial,
            "haber_inicial": gp_haber_inicial,
            "debe": gp_debe,
            "haber": gp_haber,
            "saldo_deudor": gp_saldo_deudor,
            "saldo_acreedor": gp_saldo_acreedor,
            "activo": gp_activo,
            "pasivo": gp_pasivo,
            "perdinat": gp_perdinat,
            "ganannat": gp_ganannat,
            "perdifun": gp_perdifun,
            "gananfun": gp_gananfun,
            "company_id": self.env.company.id,
            "res_user_id": self.env.user.id
        }
        vals.append(dict_sumas)
        vals.append(dict_perdi_ganan)
        self.env["f2.balance"].create(vals)

    # URO comentado
    # def _get_f2_balance_sql(self):
    #         sql = """
    # 		--DROP VIEW IF EXISTS f2_balance;
    # 		--CREATE OR REPLACE VIEW f2_balance AS
    # 		--(
    # 			DELETE FROM f2_balance WHERE company_id = {company} AND res_user_id = {user_id};
    # 			SELECT row_number() OVER () AS id,
    # 			'{period}' as period,
    # 			* FROM (
    # 			SELECT *
    # 			FROM get_f2_balance('{period}',{company},'{currency}')
    # 			UNION ALL
    # 			SELECT
    # 			null::text as mayor,
    # 			'SUMAS'::text as nomenclatura,
    # 			sum(debe_inicial) as debe_inicial,
    # 			sum(haber_inicial) as haber_inicial,
    # 			sum(debe) as debe,
    # 			sum(haber) as haber,
    # 			sum(saldo_deudor) as saldo_deudor,
    # 			sum(saldo_acreedor) as saldo_acreedor,
    # 			sum(activo) as activo,
    # 			sum(pasivo) as pasivo,
    # 			sum(perdinat) as perdinat,
    # 			sum(ganannat) as ganannat,
    # 			sum(perdifun) as perdifun,
    # 			sum(gananfun) as gananfun
    # 			FROM get_f2_balance('{period}',{company},'{currency}')
    # 			UNION ALL
    # 			SELECT
    # 			null::text as mayor,
    # 			'UTILIDAD O PERDIDA'::text as nomenclatura,
    # 			case
    # 				when sum(debe_inicial) < sum(haber_inicial)
    # 				then sum(haber_inicial) - sum(debe_inicial)
    # 				else 0
    # 			end as debe_inicial,
    # 			case
    # 				when sum(debe_inicial) > sum(haber_inicial)
    # 				then sum(debe_inicial) - sum(haber_inicial)
    # 				else 0
    # 			end as haber_inicial,
    # 			case
    # 				when sum(debe) < sum(haber)
    # 				then sum(haber) - sum(debe)
    # 				else 0
    # 			end as debe,
    # 			case
    # 				when sum(debe) > sum(haber)
    # 				then sum(debe) - sum(haber)
    # 				else 0
    # 			end as haber,
    # 			case
    # 				when sum(saldo_deudor) < sum(saldo_acreedor)
    # 				then sum(saldo_acreedor) - sum(saldo_deudor)
    # 				else 0
    # 			end as saldo_deudor,
    # 			case
    # 				when sum(saldo_deudor) > sum(saldo_acreedor)
    # 				then sum(saldo_deudor) - sum(saldo_acreedor)
    # 				else 0
    # 			end as saldo_acreedor,
    # 			case
    # 				when sum(activo) < sum(pasivo)
    # 				then sum(pasivo) - sum(activo)
    # 				else 0
    # 			end as activo,
    # 			case
    # 				when sum(activo) > sum(pasivo)
    # 				then sum(activo) - sum(pasivo)
    # 				else 0
    # 			end as pasivo,
    # 			case
    # 				when sum(perdinat) < sum(ganannat)
    # 				then sum(ganannat) - sum(perdinat)
    # 				else 0
    # 			end as perdinat,
    # 			case
    # 				when sum(perdinat) > sum(ganannat)
    # 				then sum(perdinat) - sum(ganannat)
    # 				else 0
    # 			end as ganannat,
    # 			case
    # 				when sum(perdifun) < sum(gananfun)
    # 				then sum(gananfun) - sum(perdifun)
    # 				else 0
    # 			end as perdifun,
    # 			case
    # 				when sum(perdifun) > sum(gananfun)
    # 				then sum(perdifun) - sum(gananfun)
    # 				else 0
    # 			end as gananfun
    # 			FROM get_f2_balance('{period}',{company},'{currency}')
    # 				)T
    # 		--)
    # 		""".format(
    #             period=self.period.code,
    #             company=self.company_id.id,
    #             currency=self.currency,
    #             user_id=self.env.user.id
    #         )
    #         # print(sql)
    #         # return sql
    #         self._cr.execute(sql)
    #         lines = self.env.cr.fetchall()
    #         vals = []
    #         for line in lines:
    #             vals.append(
    #                 {
    #                     "period": line[1],
    #                     "mayor": line[2],
    #                     "nomenclatura": line[3],
    #                     "debe_inicial": line[4],
    #                     "haber_inicial": line[5],
    #                     "debe": line[6],
    #                     "haber": line[7],
    #                     "saldo_deudor": line[8],
    #                     "saldo_acreedor": line[9],
    #                     "activo": line[10],
    #                     "pasivo": line[11],
    #                     "perdinat": line[12],
    #                     "ganannat": line[13],
    #                     "perdifun": line[14],
    #                     "gananfun": line[15],
    #                     "company_id": self.env.company.id,
    #                     "res_user_id": self.env.user.id
    #                 })
    #         self.env["f2.balance"].create(vals)

    def get_report(self):
        if self.level == 'register':
            # self._cr.execute(self._get_f2_register_sql())
            self._get_f2_register_sql()
        elif self.level == 'balance':
            # self._cr.execute(self._get_f2_balance_sql())
            self._get_f2_balance_sql()
        if self.type_show == 'pantalla':
            if self.level == 'register':
                return self.get_window_f2_register()
            else:
                return self.get_window_f2_balance()
        else:
            if self.level == 'register':
                return self.get_excel_f2_register()
            else:
                return self.get_excel_f2_balance()

    def get_window_f2_register(self):
        if self.show_account_entries:
            view = self.env.ref('account_htf2_report.view_f2_register_tree_true').id
        else:
            view = self.env.ref('account_htf2_report.view_f2_register_tree').id
        return {
            'name': 'Hoja de Trabajo F2 - Registro',
            'type': 'ir.actions.act_window',
            'res_model': 'f2.register',
            'view_mode': 'tree',
            'domain': [('company_id', '=', self.env.company.id),('res_user_id','=',self.env.user.id)],
            'views': [(view, 'tree')],
        }

    def get_window_f2_balance(self):
        view = self.env.ref('account_htf2_report.view_f2_balance_tree').id
        return {
            'name': 'Hoja de Trabajo F2 - Balance',
            'type': 'ir.actions.act_window',
            'res_model': 'f2.balance',
            'view_mode': 'tree',
            'domain': [('company_id', '=', self.env.company.id),('res_user_id','=',self.env.user.id)],
            'views': [(view, 'tree')],
        }

    def get_excel_f2_register(self):
        import io
        from xlsxwriter.workbook import Workbook
        ReportBase = self.env['report.base']
        direccion = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)],
                                                      limit=1).dir_create_file

        if not direccion:
            raise UserError(
                u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

        workbook = Workbook(direccion + 'Hoja_Trabajo_F2.xlsx')
        workbook, formats = ReportBase.get_formats(workbook)

        import importlib
        import sys
        importlib.reload(sys)

        worksheet = workbook.add_worksheet("Hoja de Trabajo F2")
        worksheet.set_tab_color('blue')

        HEADERS = ['MAYOR', 'CUENTA', 'NOMENCLATURA', 'DEBE INICIAL', 'HABER INICIAL', 'DEBE', 'HABER', 'SALDO DEUDOR',
                   'SALDO ACREEDOR',
                   'ACTIVO', 'PASIVO', 'PERDINAT', 'GANANNAT', 'PERDIFUN', 'GANANFUN']
        if self.show_account_entries:
            HEADERS.append('RUBRO ESTADO FINANCIERO')
        worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
        x = 1
        lines = self.env['f2.register'].search(
            [('company_id', '=', self.company_id.id), ('res_user_id', '=', self.env.user.id)])
        total = len(lines) - 2
        for c, line in enumerate(lines, 1):
            worksheet.write(x, 0, line.mayor if line.mayor else '', formats['especial1'])
            worksheet.write(x, 1, line.cuenta if line.cuenta else '', formats['especial1'])
            worksheet.write(x, 2, line.nomenclatura if line.nomenclatura else '',
                            formats['especial1'] if c <= total else formats['boldbord'])
            worksheet.write(x, 3, line.debe_inicial if line.debe_inicial else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 4, line.haber_inicial if line.haber_inicial else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 5, line.debe if line.debe else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 6, line.haber if line.haber else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 7, line.saldo_deudor if line.saldo_deudor else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 8, line.saldo_acreedor if line.saldo_acreedor else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 9, line.activo if line.activo else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 10, line.pasivo if line.pasivo else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 11, line.perdinat if line.perdinat else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 12, line.ganannat if line.ganannat else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 13, line.perdifun if line.perdifun else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 14, line.gananfun if line.gananfun else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            if self.show_account_entries:
                worksheet.write(x, 15, line.rubro if line.rubro else '', formats['especial1'])
            x += 1

        widths = [7, 9, 40, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 40]
        worksheet = ReportBase.resize_cells(worksheet, widths)
        workbook.close()
        f = open(direccion + 'Hoja_Trabajo_F2.xlsx', 'rb')
        return self.env['popup.it'].get_file('Hoja_Trabajo_F2_Nivel_Registro.xlsx',
                                             base64.encodestring(b''.join(f.readlines())))

    def get_excel_f2_balance(self):
        import io
        from xlsxwriter.workbook import Workbook
        ReportBase = self.env['report.base']
        direccion = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)],
                                                      limit=1).dir_create_file

        if not direccion:
            raise UserError(
                u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

        workbook = Workbook(direccion + 'Hoja_Trabajo_F2.xlsx')
        workbook, formats = ReportBase.get_formats(workbook)

        import importlib
        import sys
        importlib.reload(sys)

        worksheet = workbook.add_worksheet("Hoja de Trabajo F2")
        worksheet.set_tab_color('blue')

        HEADERS = ['MAYOR', 'NOMENCLATURA', 'DEBE INICIAL', 'HABER INICIAL', 'DEBE', 'HABER', 'SALDO DEUDOR',
                   'SALDO ACREEDOR',
                   'ACTIVO', 'PASIVO', 'PERDINAT', 'GANANNAT', 'PERDIFUN', 'GANANFUN']
        worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
        x = 1
        total = len(self.env['f2.balance'].search([])) - 2
        for c, line in enumerate(self.env['f2.balance'].search([]), 1):
            worksheet.write(x, 0, line.mayor if line.mayor else '', formats['especial1'])
            worksheet.write(x, 1, line.nomenclatura if line.nomenclatura else '',
                            formats['especial1'] if c <= total else formats['boldbord'])
            worksheet.write(x, 2, line.debe_inicial if line.debe_inicial else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 3, line.haber_inicial if line.haber_inicial else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 4, line.debe if line.debe else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 5, line.haber if line.haber else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 6, line.saldo_deudor if line.saldo_deudor else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 7, line.saldo_acreedor if line.saldo_acreedor else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 8, line.activo if line.activo else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 9, line.pasivo if line.pasivo else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 10, line.perdinat if line.perdinat else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 11, line.ganannat if line.ganannat else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 12, line.perdifun if line.perdifun else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            worksheet.write(x, 13, line.gananfun if line.gananfun else 0,
                            formats['numberdos'] if c <= total else formats['numbertotal'])
            x += 1

        widths = [7, 40, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 40]
        worksheet = ReportBase.resize_cells(worksheet, widths)
        workbook.close()
        f = open(direccion + 'Hoja_Trabajo_F2.xlsx', 'rb')
        return self.env['popup.it'].get_file('Hoja_Trabajo_F2_Nivel_Balance.xlsx',
                                             base64.encodestring(b''.join(f.readlines())))
