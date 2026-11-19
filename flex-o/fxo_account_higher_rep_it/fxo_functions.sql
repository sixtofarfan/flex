
----------------------------------------------------------------------------------------------------------------
----------Esta vista obtiene el libro mayor, reporte con todas las cuentas

DROP VIEW IF EXISTS public.vst_mayor CASCADE;

CREATE OR REPLACE VIEW public.vst_mayor AS 
 SELECT tt.periodo,
    tt.fecha,
    tt.libro,
    tt.voucher,
    tt.cuenta,
    tt.debe,
    tt.debe_me,
    tt.haber,
    tt.haber_me,
    tt.balance,
    tt.balance_me,
    tt.moneda,
    tt.tc,
    tt.importe_me,
    tt.code_cta_analitica,
    tt.glosa,
    tt.td_partner,
    tt.doc_partner,
    tt.partner,
    tt.td_sunat,
    tt.nro_comprobante,
    tt.fecha_doc,
    tt.fecha_ven,
    tt.company_id,
    tt.account_id,
    tt.move_line_id
   FROM ( SELECT vst_diariog.periodo,
            to_date(vst_diariog.fecha, 'yyyy/mm/dd'::text) AS fecha,
            vst_diariog.libro,
            vst_diariog.voucher,
            vst_diariog.cuenta,
            vst_diariog.debe,
            vst_diariog_me.debe_me,
            vst_diariog.haber,
            vst_diariog_me.haber_me,
            vst_diariog.balance,
            (coalesce(vst_diariog_me.debe_me,0) - coalesce(vst_diariog_me.haber_me,0)) as balance_me,
            vst_diariog.moneda,
            vst_diariog.tc,
            vst_diariog.importe_me,
            vst_diariog.code_cta_analitica,
            vst_diariog.glosa,
            vst_diariog.td_partner,
            vst_diariog.doc_partner,
            vst_diariog.partner,
            vst_diariog.td_sunat,
            vst_diariog.nro_comprobante,
            vst_diariog.fecha_doc,
            vst_diariog.fecha_ven,
            vst_diariog.company_id,
            vst_diariog.account_id,
            vst_diariog.move_line_id
           FROM vst_diariog
           LEFT JOIN vst_diariog_me on vst_diariog_me.move_id = vst_diariog.move_id and vst_diariog_me.move_line_id = vst_diariog.move_line_id
          ORDER BY vst_diariog.cuenta, vst_diariog.periodo, vst_diariog.fecha) tt;


DROP FUNCTION IF EXISTS public.fxo_get_mayor_detalle(date,date,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.fxo_get_mayor_detalle(
    IN fec_ini date,
    IN fec_fin date,
    IN id_compannia integer)
  RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying, cuenta character varying, debe numeric, debe_me numeric, haber numeric, haber_me numeric, balance numeric, balance_me numeric, moneda character varying, tc numeric, importe_me numeric, code_cta_analitica character varying, glosa character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, company_id integer, account_id integer, saldo numeric, saldo_me numeric, move_line_id integer) AS
$BODY$
DECLARE 
    var_r record;
    quiebre TEXT;
    contador INT;
BEGIN
   contador = 0 ;
   saldo = 0;
   saldo_me = 0;
   FOR var_r IN(
        select * from (
           SELECT * FROM VST_MAYOR WHERE VST_MAYOR.fecha>= fec_ini 
                    AND  VST_MAYOR.fecha <= fec_fin AND VST_MAYOR.company_id = id_compannia
            union all
            SELECT "left"(to_char((fec_ini-1)::timestamp with time zone, 'yyyymmdd'::text), 6) AS periodo, fec_ini - 1, '' as libro, '' as voucher, VST_MAYOR.cuenta,
            CASE
                WHEN SUM (VST_MAYOR.balance) > 0 THEN SUM(VST_MAYOR.balance) ELSE 0
            END as debe,
            CASE
                WHEN SUM (coalesce(VST_MAYOR.balance_me,0)) > 0 THEN SUM (coalesce(VST_MAYOR.balance_me,0)) ELSE 0
            END as debe_me,
            CASE
                WHEN SUM (VST_MAYOR.balance) < 0 THEN ABS(SUM (VST_MAYOR.balance)) ELSE 0
            END as haber,
            CASE
                WHEN SUM (coalesce(VST_MAYOR.balance_me,0)) < 0 THEN ABS(SUM (coalesce(VST_MAYOR.balance_me,0))) ELSE 0
            END as haber_me,
            SUM (VST_MAYOR.balance) AS balance,
            SUM (coalesce(VST_MAYOR.balance_me,0)) AS balance_me, '' AS moneda, 0 AS tc, SUM (VST_MAYOR.importe_me) AS importe_me, '' as code_cta_analitica, 'SALDO INICIAL' as glosa,
            '' AS td_partner, '' AS doc_partner, '' AS partner, '' AS td_sunat, '' AS nro_comprobante, null::date AS fecha_doc, null::date AS fecha_ven, VST_MAYOR.company_id as company_id, 
            VST_MAYOR.account_id AS account_id,
            min(VST_MAYOR.move_line_id) as move_line_id
            FROM VST_MAYOR WHERE VST_MAYOR.fecha < fec_ini AND VST_MAYOR.company_id = id_compannia
                            AND  EXTRACT (YEAR FROM VST_MAYOR.fecha) = EXTRACT (YEAR FROM fec_ini)
            group by VST_MAYOR.cuenta,VST_MAYOR.account_id,VST_MAYOR.company_id
         )T
                ORDER BY cuenta, periodo, fecha
               
               )
   LOOP
        -- Obtiene por unica vez el valor del primer registro
        IF contador = 0 THEN 
            quiebre := var_r.cuenta ;
            contador = contador + 1;
        END IF;
        
        -- Si los registros son de la misma cuenta
        IF quiebre =  var_r.cuenta THEN
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.balance_me;
        -- Si la cuenta cambia, reinicio el saldo y actualizo el quiebre
        ELSE
            saldo = 0;
            saldo_me = 0;
            quiebre := var_r.cuenta ;
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.balance_me;
        END IF;
        
        periodo = var_r.periodo ;
        fecha = var_r.fecha ;
        libro = var_r.libro ;
        voucher = var_r.voucher ;
        cuenta  = var_r.cuenta ;
        debe = var_r.debe ;
        debe_me = var_r.debe_me ;
        haber = var_r.haber;
        haber_me = var_r.haber_me;
        balance = var_r.balance ;
        balance_me = var_r.balance_me ;
        moneda = var_r.moneda ;
        tc  = var_r.tc ;
        importe_me  = var_r.importe_me ;
        code_cta_analitica = var_r.code_cta_analitica ;
        glosa = var_r.glosa ;
        td_partner = var_r.td_partner ;
        doc_partner = var_r.doc_partner;
        partner = var_r.partner;
        td_sunat = var_r.td_sunat ;
        nro_comprobante  = var_r.nro_comprobante ;
        fecha_doc = var_r.fecha_doc ;
        fecha_ven  = var_r.fecha_ven ;
        company_id = var_r.company_id ;
        account_id  = var_r.account_id ;
        move_line_id = var_r.move_line_id;
        
   RETURN NEXT;
   END LOOP;
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


-- FUNCTION: public.get_mayor_detalle(date, date, integer)

DROP FUNCTION public.get_mayor_detalle(date, date, integer);

CREATE OR REPLACE FUNCTION public.get_mayor_detalle(
	fec_ini date,
	fec_fin date,
	id_compannia integer)
    RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying, cuenta character varying, debe numeric, debe_me numeric, haber numeric, haber_me numeric, balance numeric, balance_me numeric, moneda character varying, tc numeric, importe_me numeric, code_cta_analitica character varying, glosa character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, company_id integer, account_id integer, saldo numeric, saldo_me numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
DECLARE 
    var_r record;
    quiebre TEXT;
    contador INT;
BEGIN
   contador = 0 ;
   saldo = 0;
   saldo_me = 0;
   FOR var_r IN(
        select * from (
           SELECT * FROM VST_MAYOR WHERE VST_MAYOR.fecha>= fec_ini 
                    AND  VST_MAYOR.fecha <= fec_fin AND VST_MAYOR.company_id = id_compannia
            union all
            SELECT "left"(to_char((fec_ini-1)::timestamp with time zone, 'yyyymmdd'::text), 6) AS periodo, fec_ini - 1, '' as libro, '' as voucher, VST_MAYOR.cuenta,
            CASE
				WHEN SUM (VST_MAYOR.balance) > 0 THEN SUM(VST_MAYOR.balance) ELSE 0
			END as debe,
            CASE
				WHEN SUM (coalesce(VST_MAYOR.balance_me,0)) > 0 THEN SUM (coalesce(VST_MAYOR.balance_me,0)) ELSE 0
			END as debe_me,
			CASE
				WHEN SUM (VST_MAYOR.balance) < 0 THEN ABS(SUM (VST_MAYOR.balance)) ELSE 0
			END as haber,
            CASE
				WHEN SUM (coalesce(VST_MAYOR.balance_me,0)) < 0 THEN ABS(SUM (coalesce(VST_MAYOR.balance_me,0))) ELSE 0
			END as haber_me,
            SUM (VST_MAYOR.balance) AS balance,
            SUM (coalesce(VST_MAYOR.balance_me,0)) AS balance_me, '' AS moneda, 0 AS tc, SUM (VST_MAYOR.importe_me) AS importe_me, '' as code_cta_analitica, 'SALDO INICIAL' as glosa,
            '' AS td_partner, '' AS doc_partner, '' AS partner, '' AS td_sunat, '' AS nro_comprobante, null::date AS fecha_doc, null::date AS fecha_ven, VST_MAYOR.company_id as company_id, 
            VST_MAYOR.account_id AS account_id,
			0 as move_line_id
            FROM VST_MAYOR WHERE VST_MAYOR.fecha < fec_ini AND VST_MAYOR.company_id = id_compannia
                            AND  EXTRACT (YEAR FROM VST_MAYOR.fecha) = EXTRACT (YEAR FROM fec_ini)
            group by VST_MAYOR.cuenta,VST_MAYOR.account_id,VST_MAYOR.company_id
         )T
                ORDER BY cuenta, periodo, fecha
               
               )
   LOOP
        -- Obtiene por unica vez el valor del primer registro
        IF contador = 0 THEN 
            quiebre := var_r.cuenta ;
            contador = contador + 1;
        END IF;
        
        -- Si los registros son de la misma cuenta
        IF quiebre =  var_r.cuenta THEN
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.balance_me;
        -- Si la cuenta cambia, reinicio el saldo y actualizo el quiebre
        ELSE
            saldo = 0;
            saldo_me = 0;
            quiebre := var_r.cuenta ;
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.balance_me;
        END IF;
        
        periodo = var_r.periodo ;
        fecha = var_r.fecha ;
        libro = var_r.libro ;
        voucher = var_r.voucher ;
        cuenta  = var_r.cuenta ;
        debe = var_r.debe ;
        debe_me = var_r.debe_me ;
        haber = var_r.haber;
        haber_me = var_r.haber_me;
        balance = var_r.balance ;
        balance_me = var_r.balance_me ;
        moneda = var_r.moneda ;
        tc  = var_r.tc ;
        importe_me  = var_r.importe_me ;
        code_cta_analitica = var_r.code_cta_analitica ;
        glosa = var_r.glosa ;
        td_partner = var_r.td_partner ;
        doc_partner = var_r.doc_partner;
        partner = var_r.partner;
        td_sunat = var_r.td_sunat ;
        nro_comprobante  = var_r.nro_comprobante ;
        fecha_doc = var_r.fecha_doc ;
        fecha_ven  = var_r.fecha_ven ;
        company_id = var_r.company_id ;
        account_id  = var_r.account_id ;
        
   RETURN NEXT;
   END LOOP;
END; $BODY$;