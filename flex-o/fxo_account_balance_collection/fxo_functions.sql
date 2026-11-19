------------------------------------------maturity_analysis_rep_it------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_fxo_maturity_analysis(
	first_date date,
	end_date date,
	company_id integer,
	type character varying) CASCADE;
CREATE OR REPLACE FUNCTION public.get_fxo_maturity_analysis(
	first_date date,
	end_date date,
	company_id integer,
	type character varying)
    RETURNS TABLE(fecha_emi date, fecha_ven date, cuenta character varying, divisa character varying, tdp character varying,
    	doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, 
    	saldo_mn numeric, saldo_me numeric, cero_treinta numeric, treinta1_sesenta numeric, sesenta1_noventa numeric, 
    	noventa1_ciento20 numeric, ciento21_ciento50 numeric, ciento51_ciento80 numeric, ciento81_mas numeric, collection character varying,
    	invoice_user_id character varying, invoice_expo_user_id character varying, invoice_period character varying) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	select 
	b1.fecha_emi,
	b1.fecha_ven,
	b1.cuenta,
	b1.divisa,
	b1.tdp,
	b1.doc_partner,
	b1.partner,
	b1.td_sunat,
	b1.nro_comprobante,
	b1.saldo_mn,
	b1.saldo_me,
	case when b1.atraso between 0 and 30 then b1.saldo_mn else 0 end as cero_treinta,
	case when b1.atraso between 31 and 60 then b1.saldo_mn else 0 end as treinta1_sesenta,
	case when b1.atraso between 61 and 90 then b1.saldo_mn else 0 end as sesenta1_noventa,
	case when b1.atraso between 91 and 120 then b1.saldo_mn else 0 end as noventa1_ciento20,
	case when b1.atraso between 121 and 150 then b1.saldo_mn else 0 end as ciento21_ciento50,
	case when b1.atraso between 151 and 180 then b1.saldo_mn else 0 end as ciento51_ciento80,
	case when b1.atraso >180 then b1.saldo_mn else 0 end as ciento81_mas,
	b1.collection,
	b1.invoice_user,
	b1.expo_user,
	b1.invoice_period
	from
	(
	select 
	case when a1.fecha_doc::date is null then a1.fecha_con::date else a1.fecha_doc::date end as fecha_emi,
	a1.fecha_ven as fecha_ven,
	a1.cuenta as cuenta,
	case when a3.name is not null then a3.name else 'PEN' end as divisa,
	a1.td_partner as tdp,
	a1.doc_partner as doc_partner,
	a1.partner,
	a1.td_sunat,
	a1.nro_comprobante,
	-a1.saldo_mn as saldo_mn,
	-a1.saldo_me as saldo_me,
	case when a1.fecha_ven is not null then $2 - a1.fecha_ven else 0 end as atraso,
	a1.account_id,
	a2.internal_type,
	rp.name as collection,
	rp2.name as invoice_user,
	rp3.name as expo_user,
	ap.name as invoice_period
	from 
	get_saldos($1,$2,$3,1) a1
	left join account_account a2 on a2.id=a1.account_id
	left join res_currency a3 on a3.id=a2.currency_id
	left join account_move am on am.id = a1.move_id
	left join res_users ru on ru.id = am.collection_id
	left join res_users ru2 on ru2.id = am.invoice_user_id
	left join res_users ru3 on ru3.id = am.invoice_expo_user_id
	left join res_partner rp on rp.id = ru.partner_id
	left join res_partner rp2 on rp2.id = ru2.partner_id
	left join res_partner rp3 on rp3.id = ru3.partner_id
	left join account_period ap on ap.id = am.invoice_period_id
	where a1.nro_comprobante is not null
	)b1
	where b1.internal_type = $4;
END;
$BODY$;
------------------------------------------maturity_analysis_rep_it------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------------------------------------------
----------Con esta funcion obtenemos el detalle de comprobante, donde los parametros son fecha inicial, fecha final y company_id
DROP FUNCTION IF EXISTS public.get_fxo_saldo_detalle(
    IN fec_ini date,
    IN fec_fin date,
    IN id_compannia integer) CASCADE;
CREATE OR REPLACE FUNCTION public.get_fxo_saldo_detalle(
    IN fec_ini date,
    IN fec_fin date,
    IN id_compannia integer)
  RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying,
  	td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, 
  	nro_comprobante character varying, fecha_doc date, fecha_ven date, cuenta character varying, moneda character varying, debe numeric, haber numeric,
  	balance numeric,importe_me numeric, saldo numeric, saldo_me numeric, partner_id integer, account_id integer, 
  	collection character varying, invoice_period character varying) AS
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
        select 
		vst_d.periodo, 
		vst_d.fecha, 
		vst_d.libro, 
		vst_d.voucher,
		vst_d.td_partner, 
		vst_d.doc_partner, 
		vst_d.partner, 
		vst_d.td_sunat, 
		vst_d.nro_comprobante, 
		vst_d.fecha_doc, 
		vst_d.fecha_ven, 
		vst_d.cuenta,
		vst_d.moneda, 
		vst_d.debe, 
		vst_d.haber,
		vst_d.balance,
		vst_d.importe_me,
		vst_d.partner_id,
		vst_d.account_id,
    	rp.name as collection,
    	ap.name as invoice_period
		from vst_diariog vst_d
		left join account_account aa on aa.id = vst_d.account_id
    	left join account_move am on am.id = vst_d.move_id
    	left join res_users ru on ru.id = am.collection_id
    	left join res_partner rp on rp.id = ru.partner_id
    	left join account_period ap on ap.id = am.invoice_period_id
		where aa.is_document_an = True and (vst_d.fecha::date between fec_ini::date and fec_fin::date) and vst_d.company_id = id_compannia
		order by vst_d.partner_id,vst_d.account_id,vst_d.td_sunat,vst_d.nro_comprobante,vst_d.fecha       
               )
   LOOP
        -- Obtiene por unica vez el valor del primer registro
        IF contador = 0 THEN 
            quiebre := concat(var_r.partner_id,var_r.account_id,var_r.td_sunat,var_r.nro_comprobante);
            contador = contador + 1;
        END IF;
        
        -- Si los registros son los mismos
        IF quiebre =  concat(var_r.partner_id,var_r.account_id,var_r.td_sunat,var_r.nro_comprobante) THEN
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.importe_me;
        -- Si cambia, reinicio el saldo y actualizo
        ELSE
            saldo = 0;
            saldo_me = 0;
            quiebre := concat(var_r.partner_id,var_r.account_id,var_r.td_sunat,var_r.nro_comprobante);
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.importe_me;
        END IF;

        periodo = var_r.periodo ;
        fecha = var_r.fecha ;
        libro = var_r.libro ;
        voucher = var_r.voucher ;
        td_partner = var_r.td_partner ;
        doc_partner = var_r.doc_partner;
        partner = var_r.partner;
        collection = var_r.collection;
        invoice_period = var_r.invoice_period;
        td_sunat = var_r.td_sunat ;
        nro_comprobante  = var_r.nro_comprobante ;
        fecha_doc = var_r.fecha_doc ;
        fecha_ven  = var_r.fecha_ven ;
        cuenta  = var_r.cuenta ;
        moneda = var_r.moneda;
        debe = var_r.debe ;
        haber  = var_r.haber ;
        balance = var_r.balance ;
        importe_me  = var_r.importe_me ;
        partner_id = var_r.partner_id ;
        account_id = var_r.account_id ;
        
   RETURN NEXT;
   END LOOP;
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

------------------------------------------account_balance_doc_rep_it---------------------------------------------------------------