DROP FUNCTION IF EXISTS public.get_fxo_saldo_detalle_gamma(
	IN fec_ini date,
	IN fec_fin date,
	IN id_compannia integer) CASCADE;
CREATE OR REPLACE FUNCTION public.get_fxo_saldo_detalle_gamma(
	IN fec_ini date,
	IN fec_fin date,
	IN id_compannia integer)
  RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying,
	td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, 
	nro_comprobante character varying, fecha_doc date, fecha_ven date, cuenta character varying, moneda character varying, debe numeric, haber numeric,
	balance numeric,importe_me numeric, saldo numeric, saldo_me numeric, partner_id integer, account_id integer, 
	collection character varying, user_request character varying, invoice_period character varying, payment_request character varying, 
	operation_number character varying, internal_ref character varying, internal_ref_child character varying, 
	product character varying) AS
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
		rp2.name as user_request,
		ap.name as invoice_period,
		fpr.name as payment_request,
		so.name as operation_number,
		so.internal_ref,
		so.internal_ref_child,
		('[' || pt.default_code || '] ' || pt.name) as product
		from vst_diariog_gamma vst_d
		left join account_account aa on aa.id = vst_d.account_id
		left join account_move am on am.id = vst_d.move_id
		left join res_users ru on ru.id = am.collection_id
		left join res_partner rp on rp.id = ru.partner_id
		left join account_period ap on ap.id = am.invoice_period_id
		left join account_move_line aml on aml.id = vst_d.move_line_id
		left join fxo_payment_request fpr on fpr.id = aml.request_id
		left join res_users ru2 on ru2.id = fpr.user_request
		left join res_partner rp2 on rp2.id = ru2.partner_id
		left join sale_order so on so.id = aml.order_id
		left join product_product pp on pp.id = aml.product_id
		left join product_template pt on pt.id = pp.product_tmpl_id
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
		user_request = var_r.user_request;
		invoice_period = var_r.invoice_period;
		td_sunat = var_r.td_sunat ;
		nro_comprobante  = var_r.nro_comprobante ;
		fecha_doc = var_r.fecha_doc ;
		fecha_ven  = var_r.fecha_ven ;
		cuenta  = var_r.cuenta ;
		moneda = var_r.moneda ;
		debe = var_r.debe ;
		haber  = var_r.haber ;
		balance = var_r.balance ;
		importe_me  = var_r.importe_me ;
		partner_id = var_r.partner_id ;
		account_id = var_r.account_id ;
		payment_request = var_r.payment_request;
		operation_number = var_r.operation_number;
		internal_ref = var_r.internal_ref;
		internal_ref_child = var_r.internal_ref_child;
		product = var_r.product;
		
   RETURN NEXT;
   END LOOP;
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

------------------------------------------account_balance_doc_rep_it---------------------------------------------------------------

DROP VIEW IF EXISTS public.vst_diariog_gamma CASCADE;

CREATE OR REPLACE VIEW public.vst_diariog_gamma AS
 SELECT row_number() OVER () AS id,
    tt.periodo,
    tt.fecha,
    tt.libro,
    tt.voucher,
    tt.cuenta,
    tt.debe,
    tt.haber,
    tt.balance,
    tt.moneda,
    tt.tc,
    tt.importe_me,
    tt.cta_analitica,
    tt.glosa,
    tt.td_partner,
    tt.doc_partner,
    tt.partner,
    tt.td_sunat,
    tt.nro_comprobante,
    tt.fecha_doc,
    tt.fecha_ven,
    tt.col_reg,
    tt.monto_reg,
    tt.medio_pago,
    tt.estado,
    tt.ple_diario,
    tt.ple_compras,
    tt.ple_ventas,
    tt.journal_id,
    tt.account_id,
    tt.partner_id,
    tt.registro,
    tt.move_id,
    tt.move_line_id,
    tt.company_id,
    tt.col_reg_id,
    tt.perception_date,
    tt.code_cta_analitica,
    tt.analytic_tag_ids,
	tt.analytic_tag_names
   FROM ( SELECT
                CASE
                    WHEN a1.is_opening_close = true AND to_char(a1.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(a1.date::timestamp with time zone, 'yyyy'::text) || '00'::text
                    WHEN a1.is_opening_close = true AND to_char(a1.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(a1.date::timestamp with time zone, 'yyyy'::text) || '13'::text
                    ELSE to_char(a1.date::timestamp with time zone, 'yyyymm'::text)
                END AS periodo,
            to_char(a1.invoice_date::timestamp with time zone, 'yyyy/mm/dd'::text) AS fecha,
            a3.code AS libro,
            a1.name AS voucher,
            a4.code AS cuenta,
            a2.debit AS debe,
            a2.credit AS haber,
            a2.balance,
                CASE
                    WHEN a2.currency_id IS NULL THEN 'PEN'::character varying
                    ELSE a5.name
                END AS moneda,
            coalesce(case when a2.tc = 0 then  1 else a2.tc end,1) as tc,
            a2.amount_currency AS importe_me,
            a2.analytic_account_id AS cta_analitica,
            a1.glosa,
            a7.code_sunat AS td_partner,
            a6.vat AS doc_partner,
            a6.name AS partner,
            a8.code AS td_sunat,
            REPLACE(a2.nro_comp,'/','-')::character varying AS nro_comprobante,
            a1.invoice_date AS fecha_doc,
            a2.date_maturity AS fecha_ven,
            a10.name AS col_reg,
            a2.tax_amount_it AS monto_reg,
            a12.code AS medio_pago,
            a1.state AS estado,
            a1.ple_state AS ple_diario,
            a1.campo_41_purchase AS ple_compras,
            a1.campo_34_sale AS ple_ventas,
            a1.journal_id,
            a2.account_id,
            a2.partner_id,
            a3.register_sunat AS registro,
            a1.id AS move_id,
            a2.id AS move_line_id,
            a1.company_id,
            a10.id AS col_reg_id,
            a1.perception_date,
            a11.name AS code_cta_analitica,
            a13.analytic_tag_ids,
			a13.analytic_tag_names
           FROM account_move a1
             LEFT JOIN account_move_line a2 ON a2.move_id = a1.id
             LEFT JOIN account_journal a3 ON a3.id = a1.journal_id
             LEFT JOIN account_account a4 ON a4.id = a2.account_id
             LEFT JOIN res_currency a5 ON a5.id = a2.currency_id
             LEFT JOIN res_partner a6 ON a6.id = a2.partner_id
             LEFT JOIN l10n_latam_identification_type a7 ON a7.id = a6.l10n_latam_identification_type_id
             LEFT JOIN einvoice_catalog_01 a8 ON a8.id = a2.type_document_id
             LEFT JOIN account_account_tag_account_move_line_rel a9 ON a9.account_move_line_id = a2.id
             LEFT JOIN account_account_tag a10 ON a10.id = a9.account_account_tag_id
             LEFT JOIN account_analytic_account a11 ON a11.id = a2.analytic_account_id
             LEFT JOIN einvoice_catalog_payment a12 ON a12.id = a1.td_payment_id
             LEFT JOIN (SELECT ARRAY_AGG(aatamlr.account_analytic_tag_id) as analytic_tag_ids,
						ARRAY_AGG(aat.name) AS analytic_tag_names, account_move_line_id 
						FROM account_analytic_tag_account_move_line_rel aatamlr
						LEFT JOIN account_analytic_tag aat ON aat.id = aatamlr.account_analytic_tag_id
						GROUP BY aatamlr.account_move_line_id) a13 ON a13.account_move_line_id = a2.id
          WHERE a1.state::text = 'posted'::text AND a2.display_type IS NULL AND a2.account_id IS NOT NULL
          ORDER BY (date_part('month'::text, a1.date)), a3.code, a1.name, a2.debit DESC, a4.code) tt;

------------------------------------------account_balance_doc_rep_it---------------------------------------------------------------

DROP FUNCTION IF EXISTS public.get_saldos_gamma(date, date, integer, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_gamma(
    IN date_ini date,
    IN date_fin date,
    IN id_company integer,
    IN query_type integer)
  RETURNS TABLE(id bigint, periodo text, fecha_con text, libro character varying, voucher character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, cuenta character varying, debe numeric, haber numeric, saldo_mn numeric, saldo_me numeric,aml_ids integer[], journal_id integer, account_id integer, partner_id integer, move_id integer, move_line_id integer, company_id integer) AS
$BODY$
BEGIN
	IF query_type = 0 THEN
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
		b2.cuenta,
		b1.sum_debe as debe,
		b1.sum_haber as haber,
		b1.sum_balance as saldo_mn,
		b1.sum_importe_me as saldo_me,
		b1.aml_ids,
		b2.journal_id,
		b2.account_id,
		b2.partner_id,
		b2.move_id,
		b2.move_line_id,
		b2.company_id
		from(
		select a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante,
		sum(a1.debe) as sum_debe, sum(a1.haber) as sum_haber, sum(a1.balance) as sum_balance, 
		sum(a1.importe_me) as sum_importe_me, min(a1.move_line_id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from vst_diariog_gamma a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		)b1
		left join vst_diariog_gamma  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
	ELSIF query_type = 1 THEN
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
		b2.cuenta,
		b1.sum_debe as debe,
		b1.sum_haber as haber,
		b1.sum_balance as saldo_mn,
		b1.sum_importe_me as saldo_me,
		b1.aml_ids,
		b2.journal_id,
		b2.account_id,
		b2.partner_id,
		b2.move_id,
		b2.move_line_id,
		b2.company_id
		from(
		select a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante,
		sum(a1.debe) as sum_debe, sum(a1.haber) as sum_haber, sum(a1.balance) as sum_balance, 
		sum(a1.importe_me) as sum_importe_me, min(a1.move_line_id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from vst_diariog_gamma a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		having sum(a1.balance) <> 0
		)b1
		left join vst_diariog_gamma  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
	ELSIF query_type = 2 THEN 
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
		b2.cuenta,
		b1.sum_debe as debe,
		b1.sum_haber as haber,
		b1.sum_balance as saldo_mn,
		b1.sum_importe_me as saldo_me,
		b1.aml_ids,
		b2.journal_id,
		b2.account_id,
		b2.partner_id,
		b2.move_id,
		b2.move_line_id,
		b2.company_id
		from(
		select a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante,
		sum(a1.debe) as sum_debe, sum(a1.haber) as sum_haber, sum(a1.balance) as sum_balance, 
		sum(a1.importe_me) as sum_importe_me, min(a1.move_line_id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from vst_diariog_gamma a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha_doc::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		)b1
		left join vst_diariog_gamma  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
	ELSIF query_type = 3 THEN 
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
		b2.cuenta,
		b1.sum_debe as debe,
		b1.sum_haber as haber,
		b1.sum_balance as saldo_mn,
		b1.sum_importe_me as saldo_me,
		b1.aml_ids,
		b2.journal_id,
		b2.account_id,
		b2.partner_id,
		b2.move_id,
		b2.move_line_id,
		b2.company_id
		from(
		select a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante,
		sum(a1.debe) as sum_debe, sum(a1.haber) as sum_haber, sum(a1.balance) as sum_balance, 
		sum(a1.importe_me) as sum_importe_me, min(a1.move_line_id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from vst_diariog_gamma a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha_doc::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		having sum(a1.balance) <> 0
		)b1
		left join vst_diariog_gamma  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
	END IF;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

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
    	invoice_user_id character varying, invoice_expo_user_id character varying, invoice_period character varying,
		credit_limit numeric,partner_id numeric, pay_term character varying) 
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
	b1.invoice_period,
	b1.credit_limit,
	b1.partner_id,
	b1.pay_term
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
	ap.name as invoice_period,
	rp4.credit_limit2::numeric as credit_limit,
	a1.partner_id as partner_id,
	case when rp4.is_supplier
	then aptp.name
	else apts.name
	end as pay_term
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
	left join res_partner rp4 on rp4.id = a1.partner_id
	left join ir_model_fields imfs on imfs.model = 'res.partner' and imfs.name = 'property_payment_term_id'
	left join ir_model_fields imfp on imfp.model = 'res.partner' and imfp.name = 'property_payment_term_id'
	left join ir_property ips on ips.res_id = 'res.partner,'||a1.partner_id and ips.fields_id = imfs.id
	left join ir_property ipp on ipp.res_id = 'res.partner,'||a1.partner_id and ipp.fields_id = imfp.id
	left join account_payment_term apts on apts.id = split_part(ips.value_reference, ',', 2)::integer
	left join account_payment_term aptp on aptp.id = split_part(ipp.value_reference, ',', 2)::integer
	left join account_period ap on ap.id = am.invoice_period_id
	where a1.nro_comprobante is not null
	)b1
	where b1.internal_type = $4;
END;
$BODY$;
------------------------------------------maturity_analysis_rep_it------------------------------------------------------------------------------------------------------------
------------------------------------------maturity_analysis_dollars_rep_it------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_fxo_maturity_analysis_dollars(
	first_date date,
	end_date date,
	company_id integer,
	type character varying,
	rate numeric) CASCADE;
CREATE OR REPLACE FUNCTION public.get_fxo_maturity_analysis_dollars(
	first_date date,
	end_date date,
	company_id integer,
	type character varying,
	rate numeric)
    RETURNS TABLE(
    	partner character varying, collection text, invoice_user_id text, 
		invoice_expo_user_id text, credit_limit numeric,partner_id numeric,
		payment_term_id integer, whithout_debt numeric, between_1_7 numeric, between_8_15 numeric,
    	between_16_30 numeric, between_31_60 numeric, between_61_90 numeric, 
		between_91_more numeric)
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	select
	c1.partner,
	min(c1.collection) as collection,
	min(c1.invoice_user_id) as invoice_user_id,
	min(c1.invoice_expo_user_id) as invoice_expo_user_id,
	sum(c1.credit_limit)::numeric as credit_limit,
	min(c1.partner_id) as partner_id,
	c1.payment_term_id as payment_term_id,
	sum(c1.whithout_debt) as whithout_debt,
	sum(c1.between_1_7) as between_1_7,
	sum(c1.between_8_15) as between_8_15,
	sum(c1.between_16_30) as between_16_30,
	sum(c1.between_31_60) as between_31_60,
	sum(c1.between_61_90) as between_61_90,
	sum(c1.between_91_more) as between_91_more
	from (
	select 
	b1.partner,
	b1.collection as collection,
	b1.invoice_user_id as invoice_user_id,
	b1.invoice_expo_user_id as invoice_expo_user_id,
	b1.credit_limit::numeric as credit_limit,
	b1.partner_id::numeric as partner_id,
	b1.payment_term_id as payment_term_id,
	case
		when b1.atraso <= 0 and $5 > 0 then round(b1.saldo_mn / $5, 2)
		when b1.atraso <= 0 and b1.currency_rate > 0 then round(b1.saldo_mn / b1.currency_rate, 2)
		when b1.atraso <= 0 and b1.currency_rate <= 0 then b1.saldo_mn
		else 0
	end as whithout_debt,
	case
		when (b1.atraso between 1 and 7) and $5 > 0 then round(b1.saldo_mn / $5, 2)
		when (b1.atraso between 1 and 7) and b1.currency_rate > 0 then round(b1.saldo_mn / b1.currency_rate, 2)
		when (b1.atraso between 1 and 7) and b1.currency_rate <= 0 then b1.saldo_mn
		else 0
	end as between_1_7,
	case  
		when (b1.atraso between 8 and 15) and $5 > 0 then round(b1.saldo_mn / $5, 2)
		when (b1.atraso between 8 and 15) and b1.currency_rate > 0 then round(b1.saldo_mn / b1.currency_rate, 2) 
		when (b1.atraso between 8 and 15) and b1.currency_rate <= 0 then b1.saldo_mn
		else 0 
	end as between_8_15,
	case
		when (b1.atraso between 16 and 30) and $5 > 0 then round(b1.saldo_mn / $5, 2)
		when (b1.atraso between 16 and 30) and b1.currency_rate > 0 then round(b1.saldo_mn / b1.currency_rate, 2) 
		when (b1.atraso between 16 and 30) and b1.currency_rate <= 0 then b1.saldo_mn
		else 0 
	end as between_16_30,
	case
		when (b1.atraso between 31 and 60) and $5 > 0 then round(b1.saldo_mn / $5, 2)
		when (b1.atraso between 31 and 60) and b1.currency_rate > 0 then round(b1.saldo_mn / b1.currency_rate, 2) 
		when (b1.atraso between 31 and 60) and b1.currency_rate <= 0 then b1.saldo_mn
		else 0 
	end as between_31_60,
	case
		when (b1.atraso between 61 and 90) and $5 > 0 then round(b1.saldo_mn / $5, 2)
		when (b1.atraso between 61 and 90) and b1.currency_rate > 0 then round(b1.saldo_mn / b1.currency_rate, 2) 
		when (b1.atraso between 61 and 90) and b1.currency_rate <= 0 then b1.saldo_mn
		else 0 
	end as between_61_90,
	case
		when b1.atraso > 90 and $5 > 0 then round(b1.saldo_mn / $5, 2)
		when b1.atraso > 90 and b1.currency_rate > 0 then round(b1.saldo_mn / b1.currency_rate, 2) 
		when b1.atraso > 90 and b1.currency_rate <= 0 then b1.saldo_mn
		else 0 
	end as between_91_more
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
	abs(a1.saldo_mn) as saldo_mn,
	a1.saldo_me as saldo_me,
	case when a1.fecha_ven is not null then $2 - a1.fecha_ven else 0 end as atraso,
	a1.account_id,
	a2.internal_type,
	rp.name as collection,
	rp2.name as invoice_user_id,
	rp3.name as invoice_expo_user_id,
	ap.name as invoice_period,
	am.currency_rate,
	rp4.credit_limit2::numeric as credit_limit,
	a1.partner_id as partner_id,
	case when rp4.is_supplier
	then aptp.id
	else apts.id
	end as payment_term_id
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
	left join res_partner rp4 on rp4.id = a1.partner_id
	left join ir_model_fields imfs on imfs.model = 'res.partner' and imfs.name = 'property_payment_term_id'
	left join ir_model_fields imfp on imfp.model = 'res.partner' and imfp.name = 'property_payment_term_id'
	left join ir_property ips on ips.res_id = 'res.partner,'||a1.partner_id and ips.fields_id = imfs.id and ips.company_id = $3
	left join ir_property ipp on ipp.res_id = 'res.partner,'||a1.partner_id and ipp.fields_id = imfp.id and ipp.company_id = $3
	left join account_payment_term apts on apts.id = split_part(ips.value_reference, ',', 2)::integer
	left join account_payment_term aptp on aptp.id = split_part(ipp.value_reference, ',', 2)::integer
	left join account_period ap on ap.id = am.invoice_period_id
	where a1.nro_comprobante is not null
	)b1
	where b1.internal_type = $4
	)c1
	group by c1.partner, c1.payment_term_id;
END;
$BODY$;
------------------------------------------maturity_analysis_rep_it------------------------------------------------------------------------------------------------------------