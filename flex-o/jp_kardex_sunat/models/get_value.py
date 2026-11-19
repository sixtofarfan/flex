from datetime import datetime, timedelta
# import pandas as pd
# import numpy as np
from pytz import timezone
# from .exceptions import InvalidCurrency, InvalidSource, InvalidYearException, NoDataFoundException
from odoo.exceptions import UserError, Warning
from odoo import _
from odoo.tools import float_round
from dateutil.relativedelta import relativedelta


class ComputeKardex():

    def convert_TZ_UTC(self, TZ_datetime, env):
        fmt = "%Y-%m-%d %H:%M:%S"
        # Current time in UTC
        now_utc = datetime.now(timezone('UTC'))
        # Convert to current user time zone
        now_timezone = now_utc.astimezone(timezone(env.user.tz))
        UTC_OFFSET_TIMEDELTA = datetime.strptime(now_utc.strftime(fmt), fmt) - datetime.strptime(
            now_timezone.strftime(fmt), fmt)
        local_datetime = datetime.strptime(TZ_datetime, fmt)
        result_utc_datetime = local_datetime + UTC_OFFSET_TIMEDELTA
        return result_utc_datetime

    def convert_TZ_to_USER(self, TZ_datetime, env):
        fmt = "%Y-%m-%d %H:%M:%S"
        # Current time in UTC
        now_utc = datetime.now(timezone('UTC'))
        # Convert to current user time zone
        now_timezone = now_utc.astimezone(timezone(env.user.tz))
        UTC_OFFSET_TIMEDELTA = datetime.strptime(now_timezone.strftime(fmt), fmt) - datetime.strptime(
            now_utc.strftime(fmt), fmt)
        local_datetime = datetime.strptime(TZ_datetime, fmt)
        result_user_datetime = local_datetime + UTC_OFFSET_TIMEDELTA
        return result_user_datetime

    def get_kardex_cost(self, product_id, locked_period, location_id, line_datetime, env):

        """ Función para obtener el costo del kardex de un producto, en un almacen,
            en una fecha específica, desde el ultimo periodo de cierre."""

        period = env['closing.period'].search([('locked_period', '<', locked_period), ('state', '=', 'done'),
                                               ('location_ids', 'in', location_id)]).sorted(lambda x: x.locked_period,
                                                                                            reverse=True)
        if not period:
            locked_period = line_datetime[:4] + '-01'
            total_quantity = total_balance = last_price = 0
        else:
            # URO comente esto de JP
            # period = period[0]
            # if int(period.locked_period[5:7]) + 1 == 13:
            #     locked_period = str(int(period.locked_period[:4]) + 1) + '-01'
            # else:
            #     locked_period = period.locked_period[:4] + '-' + str(int(period.locked_period[5:7]) + 1).zfill(2)
            # line = period.period_lines.filtered(lambda
            #                                         l: l.product_id.id == product_id and l.location_id.id == location_id) + period.period_lines_errors.filtered(
            #     lambda l: l.product_id.id == product_id and l.location_id.id == location_id)
            # total_quantity = line.quantity
            # total_balance = line.quantity * line.unit_cost
            # last_price = line.unit_cost

            # URO agregue este funcionalidad
            for p in period:
                period = p
                if int(period.locked_period[5:7]) + 1 == 13:
                    locked_period = str(int(period.locked_period[:4]) + 1) + '-01'
                else:
                    locked_period = period.locked_period[:4] + '-' + str(int(period.locked_period[5:7]) + 1).zfill(2)
                line = period.period_lines.filtered(lambda
                                                        l: l.product_id.id == product_id and l.location_id.id == location_id) + period.period_lines_errors.filtered(
                    lambda l: l.product_id.id == product_id and l.location_id.id == location_id)
                if line:
                    total_quantity = line.quantity
                    total_balance = line.quantity * line.unit_cost
                    last_price = line.unit_cost
                    break
                else:
                    total_quantity = total_balance = last_price = 0
        line_datetime = self.convert_TZ_UTC(line_datetime, env)
        sql = """select
                    case
                        when not sp.kardex_date IS NULL then
                            sp.kardex_date
                        else
                            case
                                when not si.accounting_date IS NULL then
                                    si.accounting_date
                                else
                                    si.date
                            end
                    end as kardex_date,
                    sum(qty_done),
                    spt.code,
                    sml.location_id,
                    sml.location_dest_id,
                    sm.origin_returned_move_id,
                    sm.id
                    from stock_move_line sml
                    left join stock_move sm ON sm.id = sml.move_id
                    left join stock_picking sp ON sp.id = sm.picking_id
                    left join stock_inventory si ON si.id = sm.inventory_id
    				left join stock_picking_type spt ON spt.id = sm.picking_type_id
                    where sml.product_id = """ + str(product_id) + """
                    and
                        case
                            when not sp.kardex_date::timestamp with time zone IS NULL then
                                sp.kardex_date::timestamp with time zone
                            else
                                case
                                    when not si.accounting_date::timestamp with time zone IS NULL then
                                        si.accounting_date::timestamp with time zone
                                    else
                                        si.date::timestamp with time zone
                                end
                            end::date >= '""" + locked_period + """-01'
                    and
                        case
                            when not sp.kardex_date::timestamp with time zone IS NULL then
                                sp.kardex_date::timestamp with time zone
                            else
                                case
                                    when not si.accounting_date::timestamp with time zone IS NULL then
                                        si.accounting_date::timestamp with time zone
                                    else
                                        si.date::timestamp with time zone
                                end
                            end <= '""" + line_datetime.strftime("%Y-%m-%d %H:%M:%S") + """'
                    and (sml.location_id in (""" + str(location_id) + """) or sml.location_dest_id in (""" + str(
            location_id) + """))
                    and sml.state = 'done'
                    and sm.company_id = """ + str(env.company.id) + """
                    group by sp.kardex_date, sml.reference, sm.id, sp.numberg, sp.type_operation_sunat_id, si.type_operation_sunat_id, si.accounting_date, si.date, spt.code , sml.location_id, sml.location_dest_id, sm.origin_returned_move_id
                    order by kardex_date, spt.code"""

        env.cr.execute(sql)
        # Obtenemos el recordset del sql
        movs = env.cr.fetchall()
        # Convertimos los movimientos de tuplas a listas
        movs = [list(element) for element in movs]
        # Cambiamos la fecha a fecha del usuario
        for mov in movs:
            mov[0] = self.convert_TZ_to_USER(mov[0].strftime("%Y-%m-%d %H:%M:%S"), env).date()
        # Ordenamos por fecha y luego por tipo de movimiento y luego por documento
        movs = sorted(movs, key=lambda mov: (mov[0], mov[3]))
        # Ordenamos nuevamente para que las devoluciones esten despues de las salidas
        movs_returned = [mov for mov in movs if mov[5] != None]
        for movr in movs_returned:
            # Hacemos un try por si la devolucion es despues del cierre
            # y no se encuentra la salida origen
            try:
                index = movs.index(next(m for m in movs if movr[5] == m[6]))
                if movr[0] == movs[index][0]:
                    movs.remove(movr)
                    movs.insert(index, movr)
            except:
                pass
        for line in movs:
            if line[2] == 'internal' or line[5] != None:
                if line[3] == location_id:
                    total_balance -= line[1] * last_price
                    total_quantity -= line[1]
                else:
                    if env['stock.location'].search([('id', '=', line[3])]).usage == 'customer':
                        sm = env['stock.move'].search([('id', '=', line[5])])
                        if sm:
                            kardex_date = sm.picking_id.kardex_date or sm.picking_id.date_done
                            if line[4] == location_id:
                                # URO comente esto de JP
                                # if last_price == 0:
                                #     sm = env['stock.move'].search([('id', '=', line[5])])
                                #     kardex_date = sm.picking_id.kardex_date or sm.picking_id.date_done
                                #     transfer_cost = self.get_kardex_cost(product_id, str(kardex_date.year) + '-' + str(
                                #         kardex_date.month).zfill(2), line[4], kardex_date.strftime("%Y-%m-%d %H:%M:%S"),
                                #                                          env)
                                # else:
                                transfer_cost = {}
                                transfer_cost['unit_cost'] = last_price
                            else:
                                transfer_cost = self.get_kardex_cost(product_id, str(kardex_date.year) + '-' + str(
                                    kardex_date.month).zfill(2), line[4], kardex_date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                     env)
                            # line[2] = transfer_cost['unit_cost']
                        else:
                            sm = env['stock.move'].search([('id', '=', line[6])])
                            svl = env['stock.valuation.layer'].search(
                                [('stock_move_id', '=', sm.id), ('stock_landed_cost_id', '=', False),
                                 ('quantity', '>', 0)]).sorted(lambda l: l.create_date, reverse=True)
                            unit_cost = (svl[0][0].unit_cost if svl or svl[0][
                                0].unit_cost != 0 else sm.price_unit_it) + sm.kardex_price_unit
                            transfer_cost = {}
                            transfer_cost['unit_cost'] = unit_cost
                            # line[2] = 0
                    else:
                        transfer_cost = self.get_kardex_cost(product_id, locked_period, line[3],
                                                             line[0].strftime("%Y-%m-%d %H:%M:%S"), env)
                    total_balance += line[1] * transfer_cost['unit_cost']
                    total_quantity += line[1]
            else:
                if line[2] == 'incoming' or line[2] == None or line[2] == 'mrp_operation':
                    if env['stock.location'].search([('id', '=', line[3])]).usage == 'customer':
                        sm = env['stock.move'].search([('picking_id', '=', line[5])])
                        kardex_date = sm.picking_id.kardex_date or sm.picking_id.date_done
                        transfer_cost = self.get_kardex_cost(product_id,
                                                             str(kardex_date.year) + '-' + str(kardex_date.month).zfill(
                                                                 2), line[5], kardex_date.strftime("%Y-%m-%d %H:%M:%S"),
                                                             env)
                        unit_cost = transfer_cost['unit_cost']
                    sm = env['stock.move'].search([('id', '=', line[6])])
                    svl = env['stock.valuation.layer'].search(
                        [('stock_move_id', '=', sm.id), ('stock_landed_cost_id', '=', False),
                         ('quantity', '>', 0)]).sorted(lambda l: l.create_date, reverse=True)
                    if svl:
                        if svl[0][0].unit_cost != 0:
                            unit_cost = svl[0][0].unit_cost + sm.kardex_price_unit
                        else:
                            unit_cost = sm.price_unit_it + sm.kardex_price_unit
                    else:
                        unit_cost = sm.price_unit_it + sm.kardex_price_unit
                    total_quantity += line[1]
                    total_balance += unit_cost * line[1]
                else:
                    total_quantity -= line[1]
                    total_balance -= line[1] * last_price
            if float_round(total_balance, 2) == 0 and float_round(total_quantity, 2) == 0:
                pass
            else:
                last_price = total_balance / total_quantity if total_quantity != 0 else 1
        return {'total_q': total_quantity, 'unit_cost': float_round(last_price, 8)}

    def create_kardex_dict(self, product_id, locked_period, location_id, line_datetime, env):

        """ Función para obtener un diccionario del kardex valorizado de un producto,
            en un almacen, en una fecha específica, desde el ultimo periodo de cierre.
            Si no existe un periodo de cierre comienza desde el inicio del año en curso."""

        vals = []

        period = env['closing.period'].search([('locked_period', '<', locked_period), ('state', '=', 'done'),
                                               ('location_ids', 'in', location_id)]).sorted(lambda x: x.locked_period,
                                                                                            reverse=True)
        if not period:
            locked_period = line_datetime[:4] + '-01'
            total_quantity = total_balance = last_price = 0
        else:
            period = period[0]
            if int(period[0].locked_period[5:7]) + 1 == 13:
                locked_period = str(int(period[0].locked_period[:4]) + 1) + '-01'
            else:
                locked_period = period[0].locked_period[:4] + '-' + str(int(period[0].locked_period[5:7]) + 1)
            line = period.period_lines.filtered(lambda
                                                    l: l.product_id.id == product_id and l.location_id.id == location_id) + period.period_lines_errors.filtered(
                lambda l: l.product_id.id == product_id and l.location_id.id == location_id)
            total_quantity = line.quantity
            total_balance = line.quantity * line.unit_cost
            last_price = line.unit_cost
            # Apertura por el cierre
            if line.quantity != 0 and line.unit_cost != 0:
                vals.append({
                    'date': period.end_date.strftime("%d/%m/%Y"),
                    'type_document': '00',
                    'serie': '',
                    'number': _('Initial Balance') + ' ' + period.locked_period,
                    'type_operation': '16',
                    'in_qty': line.quantity,
                    'in_cost': line.unit_cost,
                    'out_qty': 0,
                    'out_cost': 0,
                })

        line_datetime = self.convert_TZ_UTC(line_datetime, env)

        sql = """select 
                    case 
                        when not sp.kardex_date IS NULL then 
                            sp.kardex_date
                        else
                            case
                                when not si.accounting_date IS NULL then
                                    si.accounting_date
                                else
                                    si.date
                            end
                    end as kardex_date,
                    case 
                        when not sp.numberg IS NULL then
                            sp.numberg
                        else
                            ''                               
                    end as doc,
                    case
                        when not sp.type_operation_sunat_id IS NULL then
                            --sp.type_operation_sunat_id
                            tok.code
                        else
                            --si.type_operation_sunat_id
                            tok2.code
                    end,
                    sum(qty_done),
                    spt.code,
                    sml.location_id,
                    sml.location_dest_id,
                    sm.origin_returned_move_id,
                    sm.id,
                    am.ref as invoice
                    from stock_move_line sml
                    left join stock_move sm ON sm.id = sml.move_id
                    left join stock_picking sp ON sp.id = sm.picking_id
                    left join type_operation_kardex tok ON tok.id = sp.type_operation_sunat_id
                    left join stock_inventory si ON si.id = sm.inventory_id
                    left join type_operation_kardex tok2 ON tok2.id = si.type_operation_sunat_id
					left join stock_picking_type spt ON spt.id = sm.picking_type_id
					left join account_move am ON am.id = sp.invoice_id
                    where sml.product_id = """ + str(product_id) + """
                    and 
                        case 
                            when not sp.kardex_date IS NULL then 
                                sp.kardex_date
                            else
                                case
                                    when not si.accounting_date IS NULL then
                                        si.accounting_date
                                    else
                                        si.date
                                end
                        end::date >= '""" + locked_period + """-01'
                    and 
                        case 
                            when not sp.kardex_date IS NULL then 
                                sp.kardex_date
                            else
                                case
                                    when not si.accounting_date IS NULL then
                                        si.accounting_date
                                    else
                                        si.date
                                end
                        end <= '""" + line_datetime.strftime("%Y-%m-%d %H:%M:%S") + """'
                    and (sml.location_id in (""" + str(location_id) + """) or sml.location_dest_id in (""" + str(
            location_id) + """))
                    and sml.state = 'done'
                    and sm.company_id = """ + str(env.company.id) + """
                    group by sp.kardex_date, sml.reference, sm.id, sp.numberg, am.ref, sp.type_operation_sunat_id, si.type_operation_sunat_id, tok.code, tok2.code, si.accounting_date, si.date, spt.code , sml.location_id, sml.location_dest_id, sm.origin_returned_move_id
                    order by kardex_date, spt.code, doc"""

        # if product_id == 1650:
        #     print(sql)

        env.cr.execute(sql)
        # Obtenemos el recordset del sql
        movs = env.cr.fetchall()
        # Convertimos los movimientos de tuplas a listas
        movs = [list(element) for element in movs]
        # Cambiamos la fecha a fecha del usuario
        for mov in movs:
            mov[0] = self.convert_TZ_to_USER(mov[0].strftime("%Y-%m-%d %H:%M:%S"), env).date()
        # Ordenamos por fecha y luego por tipo de movimiento y luego por documento
        movs = sorted(movs, key=lambda mov: (mov[0], mov[4], mov[1]))
        # Ordenamos nuevamente para que las devoluciones esten despues de las salidas
        movs_returned = [mov for mov in movs if mov[7] != None]
        for movr in movs_returned:
            # Hacemos un try por si la devolucion es despues del cierre
            # y no se encuentra la salida origen
            try:
                index = movs.index(next(m for m in movs if movr[7] == m[8]))
                if movr[0] == movs[index][0]:
                    movs.remove(movr)
                    movs.insert(index, movr)
            except:
                pass
        for line in movs:
            transfer_cost = {'unit_cost': 0}
            if line[4] == 'internal' or line[7] != None:
                if line[5] == location_id:
                    total_balance -= line[3] * last_price
                    total_quantity -= line[3]
                    in_out = False
                else:
                    if env['stock.location'].search([('id', '=', line[5])]).usage == 'customer':
                        sm = env['stock.move'].search([('id', '=', line[7])])
                        if sm:
                            kardex_date = sm.picking_id.kardex_date or sm.picking_id.date_done
                            transfer_cost = self.get_kardex_cost(product_id, str(kardex_date.year) + '-' + str(
                                kardex_date.month).zfill(2), line[6], kardex_date.strftime("%Y-%m-%d %H:%M:%S"), env)
                            # line[4] = transfer_cost['unit_cost']
                            unit_cost = transfer_cost['unit_cost']
                        else:
                            sm = env['stock.move'].search([('id', '=', line[8])])
                            svl = env['stock.valuation.layer'].search(
                                [('stock_move_id', '=', sm.id), ('stock_landed_cost_id', '=', False),
                                 ('quantity', '>', 0)]).sorted(lambda l: l.create_date, reverse=True)
                            unit_cost = (svl[0][0].unit_cost if svl or svl[0][
                                0].unit_cost != 0 else sm.price_unit_it) + sm.kardex_price_unit
                            # transfer_cost['unit_cost'] = 0
                            # line[4] = 0
                            # unit_cost = transfer_cost['unit_cost']
                    else:
                        transfer_cost = self.get_kardex_cost(product_id, locked_period, line[5],
                                                             line[0].strftime("%Y-%m-%d %H:%M:%S"), env)
                    total_balance += line[3] * transfer_cost['unit_cost']
                    total_quantity += line[3]
                    in_out = True
            else:
                if line[4] == 'incoming' or line[4] == None or line[4] == 'mrp_operation':
                    if env['stock.location'].search([('id', '=', line[5])]).usage == 'customer':
                        sm = env['stock.move'].search([('picking_id', '=', line[7])])
                        kardex_date = sm.picking_id.kardex_date or sm.picking_id.date_done
                        transfer_cost = self.get_kardex_cost(product_id,
                                                             str(kardex_date.year) + '-' + str(kardex_date.month).zfill(
                                                                 2), line[6], kardex_date.strftime("%Y-%m-%d %H:%M:%S"),
                                                             env)
                        line[4] = transfer_cost['unit_cost']
                    sm = env['stock.move'].search([('id', '=', line[8])])
                    svl = env['stock.valuation.layer'].search(
                        [('stock_move_id', '=', sm.id), ('stock_landed_cost_id', '=', False),
                         ('quantity', '>', 0)]).sorted(lambda l: l.create_date, reverse=True)
                    # URO se desgloso el if ternario porque daba error de index en tupla
                    if svl:
                        if svl[0][0].unit_cost != 0:
                            unit_cost = svl[0][0].unit_cost + sm.kardex_price_unit
                        else:
                            unit_cost = sm.price_unit_it + sm.kardex_price_unit
                    else:
                        unit_cost = sm.price_unit_it + sm.kardex_price_unit
                    # unit_cost = (svl[0][0].unit_cost if svl or svl[0][
                    #     0].unit_cost != 0 else sm.price_unit_it) + sm.kardex_price_unit
                    total_quantity += line[3]
                    total_balance += unit_cost * line[3]
                    in_out = True
                else:
                    total_quantity -= line[3]
                    total_balance -= line[3] * last_price
                    in_out = False
            if float_round(total_balance, 2) == 0 and float_round(total_quantity, 2) == 0:
                last_price = last_price
            else:
                last_price = total_balance / total_quantity if total_quantity != 0 else 1
            if line[1]:
                parts = line[1].split('-')
            else:
                if line[9]:
                    parts = line[9].split('-')
                else:
                    parts = ['S/N']
            if len(parts) > 1:
                serie = parts[0]
                number = parts[1]
            else:
                serie = ''
                number = parts[0]
            vals.append({
                'date': line[0].strftime("%d/%m/%Y"),
                'type_document': '09' if line[1] else ('01' if line[9] else ''),
                'serie': serie,
                'number': number,
                'type_operation': str(line[2]).zfill(2) if line[2] else '18',
                'in_qty': line[3] if in_out else 0,
                'in_cost': (
                    unit_cost if transfer_cost['unit_cost'] == 0 else transfer_cost['unit_cost']) if in_out else 0,
                'out_qty': line[3] if not in_out else 0,
                'out_cost': (
                    last_price if transfer_cost['unit_cost'] == 0 else transfer_cost['unit_cost']) if not in_out else 0,
            })
        return vals

    def create_kardex_dict_uro(self, product_id, locked_period, location_id, line_datetime, env):
        period = env['closing.period'].search([('locked_period', '<', locked_period), ('state', '=', 'done'),
                                               ('location_ids', 'in', location_id)]).sorted(lambda x: x.locked_period,
                                                                                            reverse=True)
        vals = []
        if not period:
            locked_period = line_datetime[:4] + '-01'
            total_quantity = total_balance = last_price = 0
            sql = """select 
                                            case 
                                                when not sp.kardex_date IS NULL then 
                                                    sp.kardex_date
                                                else
                                                    case
                                                        when not si.accounting_date IS NULL then
                                                            si.accounting_date
                                                        else
                                                            si.date
                                                    end
                                            end as kardex_date,
                                            case 
                                                when not sp.numberg IS NULL then
                                                    sp.numberg
                                                else
                                                    ''                               
                                            end as doc,
                                            case
                                                when not sp.type_operation_sunat_id IS NULL then
                                                    --sp.type_operation_sunat_id
                                                    tok.code
                                                else
                                                    --si.type_operation_sunat_id
                                                    tok2.code
                                            end,
                                            sum(qty_done),
                                            spt.code,
                                            sml.location_id,
                                            sml.location_dest_id,
                                            sm.origin_returned_move_id,
                                            sm.id,
                                            am.ref as invoice,
                                            sp.name
                                            from stock_move_line sml
                                            left join stock_move sm ON sm.id = sml.move_id
                                            left join stock_picking sp ON sp.id = sm.picking_id
                                            left join type_operation_kardex tok ON tok.id = sp.type_operation_sunat_id
                                            left join stock_inventory si ON si.id = sm.inventory_id
                                            left join type_operation_kardex tok2 ON tok2.id = si.type_operation_sunat_id
                                            left join stock_picking_type spt ON spt.id = sm.picking_type_id
                                            left join account_move am ON am.id = sp.invoice_id
                                            where sml.product_id = """ + str(product_id) + """
                                            and 
                                                case 
                                                    when not sp.kardex_date IS NULL then 
                                                        sp.kardex_date
                                                    else
                                                        case
                                                            when not si.accounting_date IS NULL then
                                                                si.accounting_date
                                                            else
                                                                si.date
                                                        end
                                                end::date >= '""" + locked_period + """-01'
                                            and 
                                                case 
                                                    when not sp.kardex_date IS NULL then 
                                                        sp.kardex_date
                                                    else
                                                        case
                                                            when not si.accounting_date IS NULL then
                                                                si.accounting_date
                                                            else
                                                                si.date
                                                        end
                                                end <= '""" + line_datetime + """'
                                            and (sml.location_id in (""" + str(
                location_id) + """) or sml.location_dest_id in (""" + str(
                location_id) + """))
                                            and sml.state = 'done'
                                            and sm.company_id = """ + str(env.company.id) + """
                                            group by sp.kardex_date, sml.reference, sm.id, sp.numberg, am.ref, sp.type_operation_sunat_id, si.type_operation_sunat_id, tok.code, tok2.code, si.accounting_date, si.date, spt.code , sml.location_id, sml.location_dest_id, sm.origin_returned_move_id, sp.name
                                            order by kardex_date, spt.code, doc"""

            env.cr.execute(sql)
            movs = env.cr.fetchall()
            movs = [list(element) for element in movs]
            for mov in movs:
                mov[0] = self.convert_TZ_to_USER(mov[0].strftime("%Y-%m-%d %H:%M:%S"), env).date()
            for line in movs:
                transfer_cost = {'unit_cost': 0}
                if line[4] == 'internal' or line[7] != None:
                    if line[5] == location_id:
                        total_balance -= line[3] * last_price
                        total_quantity -= line[3]
                        in_out = False
                    else:
                        if env['stock.location'].search([('id', '=', line[5])]).usage == 'customer':
                            sm = env['stock.move'].search([('id', '=', line[7])])
                            if sm:
                                kardex_date = sm.picking_id.kardex_date or sm.picking_id.date_done
                                transfer_cost = self.get_kardex_cost(product_id, str(kardex_date.year) + '-' + str(
                                    kardex_date.month).zfill(2), line[6], kardex_date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                     env)
                                unit_cost = transfer_cost['unit_cost']
                            else:
                                sm = env['stock.move'].search([('id', '=', line[8])])
                                svl = env['stock.valuation.layer'].search(
                                    [('stock_move_id', '=', sm.id), ('stock_landed_cost_id', '=', False),
                                     ('quantity', '>', 0)]).sorted(lambda l: l.create_date, reverse=True)
                                if svl:
                                    if svl[0][0].unit_cost != 0:
                                        unit_cost = svl[0][0].unit_cost + sm.kardex_price_unit
                                    else:
                                        unit_cost = sm.price_unit_it + sm.kardex_price_unit
                                else:
                                    unit_cost = sm.price_unit_it + sm.kardex_price_unit
                        else:
                            transfer_cost = self.get_kardex_cost(product_id, locked_period, line[5],
                                                                 line[0].strftime("%Y-%m-%d %H:%M:%S"), env)
                        total_balance += line[3] * transfer_cost['unit_cost']
                        total_quantity += line[3]
                        in_out = True
                else:
                    if line[4] == 'incoming' or line[4] == None or line[4] == 'mrp_operation':
                        if env['stock.location'].search([('id', '=', line[5])]).usage == 'customer':
                            sm = env['stock.move'].search([('picking_id', '=', line[7])])
                            kardex_date = sm.picking_id.kardex_date or sm.picking_id.date_done
                            transfer_cost = self.get_kardex_cost(product_id,
                                                                 str(kardex_date.year) + '-' + str(
                                                                     kardex_date.month).zfill(
                                                                     2), line[6],
                                                                 kardex_date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                 env)
                            line[4] = transfer_cost['unit_cost']
                        sm = env['stock.move'].search([('id', '=', line[8])])
                        svl = env['stock.valuation.layer'].search(
                            [('stock_move_id', '=', sm.id), ('stock_landed_cost_id', '=', False),
                             ('quantity', '>', 0)]).sorted(lambda l: l.create_date, reverse=True)
                        if svl:
                            if svl[0][0].unit_cost != 0:
                                unit_cost = svl[0][0].unit_cost + sm.kardex_price_unit
                            else:
                                unit_cost = sm.price_unit_it + sm.kardex_price_unit
                        else:
                            unit_cost = sm.price_unit_it + sm.kardex_price_unit
                        total_quantity += line[3]
                        total_balance += unit_cost * line[3]
                        in_out = True
                    else:
                        total_quantity -= line[3]
                        total_balance -= line[3] * last_price
                        in_out = False
                if float_round(total_balance, 2) == 0 and float_round(total_quantity, 2) == 0:
                    last_price = last_price
                else:
                    last_price = total_balance / total_quantity if total_quantity != 0 else 1
                if line[1]:
                    parts = line[1].split('-')
                else:
                    if line[9]:
                        parts = line[9].split('-')
                    else:
                        parts = ['S/N']
                if len(parts) > 1:
                    serie = parts[0]
                    number = parts[1]
                else:
                    serie = ''
                    number = parts[0]
                vals.append({
                    'date': line[0].strftime("%d/%m/%Y"),
                    'type_document': '09' if line[1] else ('01' if line[9] else ''),
                    'serie': serie,
                    'number': number,
                    'type_operation': str(line[2]).zfill(2) if line[2] else '18',
                    'in_qty': line[3] if in_out else 0,
                    'in_cost': (
                        unit_cost if transfer_cost['unit_cost'] == 0 else transfer_cost[
                            'unit_cost']) if in_out else 0,
                    'out_qty': line[3] if not in_out else 0,
                    'out_cost': (
                        last_price if transfer_cost['unit_cost'] == 0 else transfer_cost[
                            'unit_cost']) if not in_out else 0,
                    'picking': line[10]
                })
        else:
            period = period[0]
            if int(period[0].locked_period[5:7]) + 1 == 13:
                locked_period = str(int(period[0].locked_period[:4]) + 1) + '-01'
            else:
                locked_period = period[0].locked_period[:4] + '-' + str(int(period[0].locked_period[5:7]) + 1)
            line = period.period_lines.filtered(lambda
                                                    l: l.product_id.id == product_id and l.location_id.id == location_id) + period.period_lines_errors.filtered(
                lambda l: l.product_id.id == product_id and l.location_id.id == location_id)
            total_quantity = line.quantity
            total_balance = line.quantity * line.unit_cost
            last_price = line.unit_cost
            if line:
                if line.quantity != 0 and line.unit_cost != 0:
                    vals.append({
                        'date': period.end_date.strftime("%d/%m/%Y"),
                        'type_document': '00',
                        'serie': '',
                        'number': _('Initial Balance') + ' ' + period.locked_period,
                        'type_operation': '16',
                        'in_qty': line.quantity,
                        'in_cost': line.unit_cost,
                        'out_qty': 0,
                        'out_cost': 0,
                        'picking': '-'
                    })

            sql = """select 
                                case 
                                    when not sp.kardex_date IS NULL then 
                                        sp.kardex_date
                                    else
                                        case
                                            when not si.accounting_date IS NULL then
                                                si.accounting_date
                                            else
                                                si.date
                                        end
                                end as kardex_date,
                                case 
                                    when not sp.numberg IS NULL then
                                        sp.numberg
                                    else
                                        ''                               
                                end as doc,
                                case
                                    when not sp.type_operation_sunat_id IS NULL then
                                        --sp.type_operation_sunat_id
                                        tok.code
                                    else
                                        --si.type_operation_sunat_id
                                        tok2.code
                                end,
                                sum(qty_done),
                                spt.code,
                                sml.location_id,
                                sml.location_dest_id,
                                sm.origin_returned_move_id,
                                sm.id,
                                am.ref as invoice,
                                sp.name
                                from stock_move_line sml
                                left join stock_move sm ON sm.id = sml.move_id
                                left join stock_picking sp ON sp.id = sm.picking_id
                                left join type_operation_kardex tok ON tok.id = sp.type_operation_sunat_id
                                left join stock_inventory si ON si.id = sm.inventory_id
                                left join type_operation_kardex tok2 ON tok2.id = si.type_operation_sunat_id
                                left join stock_picking_type spt ON spt.id = sm.picking_type_id
                                left join account_move am ON am.id = sp.invoice_id
                                where sml.product_id = """ + str(product_id) + """
                                and 
                                    case 
                                        when not sp.kardex_date IS NULL then 
                                            sp.kardex_date
                                        else
                                            case
                                                when not si.accounting_date IS NULL then
                                                    si.accounting_date
                                                else
                                                    si.date
                                            end
                                    end::date >= '""" + locked_period + """-01'
                                and 
                                    case 
                                        when not sp.kardex_date IS NULL then 
                                            sp.kardex_date
                                        else
                                            case
                                                when not si.accounting_date IS NULL then
                                                    si.accounting_date
                                                else
                                                    si.date
                                            end
                                    end <= '""" + line_datetime + """'
                                and (sml.location_id in (""" + str(
                location_id) + """) or sml.location_dest_id in (""" + str(
                location_id) + """))
                                and sml.state = 'done'
                                and sm.company_id = """ + str(env.company.id) + """
                                group by sp.kardex_date, sml.reference, sm.id, sp.numberg, am.ref, sp.type_operation_sunat_id, si.type_operation_sunat_id, tok.code, tok2.code, si.accounting_date, si.date, spt.code , sml.location_id, sml.location_dest_id, sm.origin_returned_move_id,sp.name
                                order by kardex_date, spt.code, doc"""

            env.cr.execute(sql)
            movs = env.cr.fetchall()
            movs = [list(element) for element in movs]
            for mov in movs:
                mov[0] = self.convert_TZ_to_USER(mov[0].strftime("%Y-%m-%d %H:%M:%S"), env).date()
            for line in movs:
                transfer_cost = {'unit_cost': 0}
                if line[4] == 'internal' or line[7] != None:
                    if line[5] == location_id:
                        total_balance -= line[3] * last_price
                        total_quantity -= line[3]
                        in_out = False
                    else:
                        if env['stock.location'].search([('id', '=', line[5])]).usage == 'customer':
                            sm = env['stock.move'].search([('id', '=', line[7])])
                            if sm:
                                kardex_date = sm.picking_id.kardex_date or sm.picking_id.date_done
                                transfer_cost = self.get_kardex_cost(product_id, str(kardex_date.year) + '-' + str(
                                    kardex_date.month).zfill(2), line[6], kardex_date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                     env)
                                unit_cost = transfer_cost['unit_cost']
                            else:
                                sm = env['stock.move'].search([('id', '=', line[8])])
                                svl = env['stock.valuation.layer'].search(
                                    [('stock_move_id', '=', sm.id), ('stock_landed_cost_id', '=', False),
                                     ('quantity', '>', 0)]).sorted(lambda l: l.create_date, reverse=True)
                                if svl:
                                    if svl[0][0].unit_cost != 0:
                                        unit_cost = svl[0][0].unit_cost + sm.kardex_price_unit
                                    else:
                                        unit_cost = sm.price_unit_it + sm.kardex_price_unit
                                else:
                                    unit_cost = sm.price_unit_it + sm.kardex_price_unit
                        else:
                            transfer_cost = self.get_kardex_cost(product_id, locked_period, line[5],
                                                                 line[0].strftime("%Y-%m-%d %H:%M:%S"), env)
                        total_balance += line[3] * transfer_cost['unit_cost']
                        total_quantity += line[3]
                        in_out = True
                else:
                    if line[4] == 'incoming' or line[4] == None or line[4] == 'mrp_operation':
                        if env['stock.location'].search([('id', '=', line[5])]).usage == 'customer':
                            sm = env['stock.move'].search([('picking_id', '=', line[7])])
                            kardex_date = sm.picking_id.kardex_date or sm.picking_id.date_done
                            transfer_cost = self.get_kardex_cost(product_id,
                                                                 str(kardex_date.year) + '-' + str(
                                                                     kardex_date.month).zfill(
                                                                     2), line[6],
                                                                 kardex_date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                 env)
                            line[4] = transfer_cost['unit_cost']
                        sm = env['stock.move'].search([('id', '=', line[8])])
                        svl = env['stock.valuation.layer'].search(
                            [('stock_move_id', '=', sm.id), ('stock_landed_cost_id', '=', False),
                             ('quantity', '>', 0)]).sorted(lambda l: l.create_date, reverse=True)
                        if svl:
                            if svl[0][0].unit_cost != 0:
                                unit_cost = svl[0][0].unit_cost + sm.kardex_price_unit
                            else:
                                unit_cost = sm.price_unit_it + sm.kardex_price_unit
                        else:
                            unit_cost = sm.price_unit_it + sm.kardex_price_unit
                        total_quantity += line[3]
                        total_balance += unit_cost * line[3]
                        in_out = True
                    else:
                        total_quantity -= line[3]
                        total_balance -= line[3] * last_price
                        in_out = False
                if float_round(total_balance, 2) == 0 and float_round(total_quantity, 2) == 0:
                    last_price = last_price
                else:
                    last_price = total_balance / total_quantity if total_quantity != 0 else 1
                if line[1]:
                    parts = line[1].split('-')
                else:
                    if line[9]:
                        parts = line[9].split('-')
                    else:
                        parts = ['S/N']
                if len(parts) > 1:
                    serie = parts[0]
                    number = parts[1]
                else:
                    serie = ''
                    number = parts[0]
                vals.append({
                    'date': line[0].strftime("%d/%m/%Y"),
                    'type_document': '09' if line[1] else ('01' if line[9] else ''),
                    'serie': serie,
                    'number': number,
                    'type_operation': str(line[2]).zfill(2) if line[2] else '18',
                    'in_qty': line[3] if in_out else 0,
                    'in_cost': (
                        unit_cost if transfer_cost['unit_cost'] == 0 else transfer_cost[
                            'unit_cost']) if in_out else 0,
                    'out_qty': line[3] if not in_out else 0,
                    'out_cost': (
                        last_price if transfer_cost['unit_cost'] == 0 else transfer_cost[
                            'unit_cost']) if not in_out else 0,
                    'picking': line[10]
                })
        return vals

    def get_kardex_close_period(self, product_id, locked_period, location_id, line_datetime, env):
        list_data = self.create_kardex_dict_uro(product_id, locked_period, location_id, line_datetime, env)
        quantity = 0
        unit_cost = 0
        total_cost = 0
        transfer_cost = {}
        for item in list_data:
            quantity = item['in_qty'] - item['out_qty'] + quantity
            cost_total_in = item['in_qty'] * item['in_cost']
            cost_total_out = item['out_qty'] * item['out_cost']
            total_cost = cost_total_in - cost_total_out + total_cost
            if quantity != 0:
                unit_cost = total_cost / quantity
            else:
                unit_cost = 0
        transfer_cost['total_q'] = quantity
        transfer_cost['unit_cost'] = unit_cost
        return transfer_cost
