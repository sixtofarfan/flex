--------------------------------------------------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS tablefunc;
------------------------------------------account_bc_report---------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_bc_register(
    IN period_from character varying,
    IN period_to character varying,
    IN company integer)
  RETURNS TABLE(mayor text, cuenta character varying, nomenclatura text, 
                debe numeric(64,2), haber numeric(64,2), saldo_deudor numeric(64,2), 
                saldo_acreedor numeric(64,2), rubro text) AS
$BODY$
BEGIN

RETURN QUERY 
    select
    min(substring(aa.code,0,3)) as mayor,
    aa.code as cuenta,
    min(aa.name) as nomenclatura,
    sum(vd.debe) as debe,
    sum(vd.haber) as haber,
    case 
        when sum(vd.debe) > sum(vd.haber) 
        then sum(vd.debe) - sum(vd.haber)
        else 0
    end as saldo_deudor,
    case
        when sum(vd.haber) > sum(vd.debe)
        then sum(vd.haber) - sum(vd.debe)
        else 0
    end as saldo_acreedor,
    min(ati.name) as rubro
    from vst_diariog vd
    left join account_account aa on aa.code = vd.cuenta
    left join account_type_it ati on ati.id = aa.account_type_it_id
    inner join account_period ap on substring(ap.code,5,8)::int >= substring($1,5,8)::int 
                                 and substring(ap.code,5,8)::int <= substring($2,5,8)::int
    where vd.periodo = ap.code and aa.company_id = $3 
    group by aa.code;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

-------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_bc_balance(
    IN period_from character varying,
    IN period_to character varying,
    IN company integer)
  RETURNS TABLE(mayor text, nomenclatura character varying, 
                debe numeric(64,2), haber numeric(64,2), saldo_deudor numeric(64,2), 
                saldo_acreedor numeric(64,2)) AS
$BODY$
BEGIN

RETURN QUERY 
    select
    bcr.mayor,
    ag.name,
    sum(bcr.debe),
    sum(bcr.haber),
    case 
        when sum(bcr.debe) > sum(bcr.haber) 
        then sum(bcr.debe) - sum(bcr.haber)
        else 0
    end as saldo_deudor,
    case
        when sum(bcr.haber) > sum(bcr.debe)
        then sum(bcr.haber) - sum(bcr.debe)
        else 0
    end as saldo_acreedor
    from get_bc_register($1,$2,$3) bcr
    left join account_group ag on ag.code_prefix = bcr.mayor
    group by bcr.mayor,ag.name;

END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


------------------------------------------account_bc_report---------------------------------------------------------------

------------------------------------------account_efective_rep_it---------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_efective_flow(
	periodo_ini character varying,
	periodo_fin character varying,
	period_saldo_inicial character varying,
	company integer)
    RETURNS TABLE(name character varying, efective_group character varying, total numeric, efective_order integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN

RETURN QUERY

SELECT * 
FROM (
	SELECT
	T.account_efective_type_name,
	T.grupo,
	sum(T.balance) as balance,
	T.orden
	FROM(
		SELECT
		vst_d.cuenta AS account_code,
		ati.name AS account_efective_type_name,
		sum(vst_d.haber) as ingreso,
		sum(vst_d.debe) as egreso, 
		sum(haber-debe) as balance,
		ati."group" as grupo,
		ati.order as orden
		FROM vst_diariog vst_d 
		LEFT JOIN account_account aa ON aa.id = vst_d.account_id
		LEFT JOIN account_efective_type ati ON ati.id = aa.account_type_cash_id
		WHERE vst_d.move_id IN(
			SELECT move_id FROM vst_diariog
			WHERE LEFT(cuenta,2)='10' AND RIGHT(periodo,2) NOT IN ('00','13')
			AND (fecha between $1 AND $2)
			AND company_id = $4)
		AND LEFT(vst_d.cuenta,2)<>'10'
		GROUP BY vst_d.cuenta,ati.name,ati."group",ati.order
	) T
	GROUP BY T.account_efective_type_name,T.grupo,T.orden
	UNION ALL
	SELECT 
	'Saldo EFECT y EQUIV de EFECT al inicio del Ejercicio' as account_efective_type_name,
	'E7'::varchar as grupo,
	sum(haber-debe) as balance,
	-1::integer as orden
	FROM vst_diariog vst_d
	LEFT JOIN account_account aa ON aa.id = vst_d.account_id
	LEFT JOIN account_efective_type ati ON ati.id = aa.account_type_cash_id
	WHERE LEFT(cuenta,2)='10' AND periodo = $3
	AND aa.company_id = $4 
	GROUP BY ati.name,ati."group",ati.order)T
ORDER BY T.orden;

END;
$BODY$;

-------------------------------------------------account_efective_rep_it------------------------------------------------------------------

-------------------------------------------------account_htf1_report------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_f1_register(
    IN period_from character varying,
    IN period_to character varying,
	IN company integer)
  RETURNS TABLE(mayor text, cuenta character varying, nomenclatura text, 
                debe numeric(64,2), haber numeric(64,2), saldo_deudor numeric(64,2), 
                saldo_acreedor numeric(64,2), activo numeric(64,2), pasivo numeric(64,2), 
				perdinat numeric(64,2), ganannat numeric(64,2),perdifun numeric(64,2), 
				gananfun numeric(64,2),rubro text) AS
$BODY$
BEGIN

RETURN QUERY 
    
	select T.mayor,T.cuenta,T.nomenclatura,T.debe,T.haber,
		   T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and aa.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and aa.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and aa.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and aa.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and aa.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and aa.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and aa.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and aa.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and aa.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and aa.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun,
	T.rubro
	from(
		select
		min(substring(aa.code,0,3)) as mayor,
		aa.code as cuenta,
		min(aa.name) as nomenclatura,
		sum(vd.debe) as debe,
		sum(vd.haber) as haber,
		case 
			when sum(vd.debe) > sum(vd.haber) 
			then sum(vd.debe) - sum(vd.haber)
			else 0
		end as saldo_deudor,
		case
			when sum(vd.haber) > sum(vd.debe)
			then sum(vd.haber) - sum(vd.debe)
			else 0
		end as saldo_acreedor,
		min(ati.name) as rubro
		from vst_diariog vd
		left join account_account aa on aa.code = vd.cuenta
		left join account_type_it ati on ati.id = aa.account_type_it_id
		inner join account_period ap on substring(ap.code,5,8)::int >= substring($1,5,8)::int 
									 and substring(ap.code,5,8)::int <= substring($2,5,8)::int
		where vd.periodo = ap.code and aa.company_id = $3
		group by aa.code)T
	inner join account_account aa on aa.code = T.cuenta;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
-------------------------------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_f1_balance(
    IN period_from character varying,
    IN period_to character varying,
	IN company integer)
  RETURNS TABLE(mayor text, nomenclatura character varying, 
                debe numeric(64,2), haber numeric(64,2), saldo_deudor numeric(64,2), 
                saldo_acreedor numeric(64,2), activo numeric(64,2), pasivo numeric(64,2), 
				perdinat numeric(64,2), ganannat numeric(64,2),perdifun numeric(64,2), 
				gananfun numeric(64,2)) AS
$BODY$
BEGIN

RETURN QUERY 
    
	select T.mayor,T.name,T.debe,T.haber,
		   T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and ag.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and ag.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun
	from(
		select
		f1r.mayor,
		ag.name,
		ag.id,
		sum(f1r.debe) as debe,
		sum(f1r.haber) as haber,
		case 
			when sum(f1r.debe) > sum(f1r.haber) 
			then sum(f1r.debe) - sum(f1r.haber)
			else 0
		end as saldo_deudor,
		case
			when sum(f1r.haber) > sum(f1r.debe)
			then sum(f1r.haber) - sum(f1r.debe)
			else 0
		end as saldo_acreedor
		from get_f1_register($1,$2,$3) f1r
		left join account_group ag on ag.code_prefix = f1r.mayor
    	group by f1r.mayor,ag.name,ag.id)T
	inner join account_group ag on ag.id = T.id;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

-------------------------------------------------account_htf1_report------------------------------------------------------------------

-------------------------------------------------account_htf2_report------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_f2_register(
    IN period character varying,
	IN company integer)
  RETURNS TABLE(mayor text, cuenta character varying, nomenclatura text, debe_inicial numeric(64,2),
                haber_inicial numeric(64,2), debe numeric(64,2), haber numeric(64,2), 
				saldo_deudor numeric(64,2), saldo_acreedor numeric(64,2), activo numeric(64,2), 
				pasivo numeric(64,2), perdinat numeric(64,2), ganannat numeric(64,2), 
				perdifun numeric(64,2), gananfun numeric(64,2), rubro text) AS
$BODY$
BEGIN
RETURN QUERY 
	select T.mayor,T.cuenta,T.nomenclatura,T.debe_inicial,T.haber_inicial,
		   T.debe,T.haber,T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and aa.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and aa.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and aa.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and aa.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and aa.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and aa.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and aa.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and aa.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and aa.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and aa.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun,
	T.rubro
	from(
		select 
		min(substring(aa.code,0,3)) as mayor,
		A.cuenta as cuenta,
		min(aa.name) as nomenclatura,
		sum(A.debe_inicial) as debe_inicial,
		sum(A.haber_inicial) as haber_inicial,
		sum(A.debe_restante) as debe,
		sum(A.haber_restante) as haber,
		case 
			when sum(A.debe_inicial) + sum(A.debe_restante) > sum(A.haber_inicial) + sum(A.haber_restante) 
			then (sum(A.debe_inicial) + sum(A.debe_restante)) - (sum(A.haber_inicial) + sum(A.haber_restante))
			else 0
		end as saldo_deudor,
		case
			when sum(A.haber_inicial) + sum(A.haber_restante) > sum(A.debe_inicial) + sum(A.debe_restante)
			then (sum(A.haber_inicial) + sum(A.haber_restante)) - (sum(A.debe_inicial) + sum(A.debe_restante))
			else 0
		end as saldo_acreedor,
		min(ati.name) as rubro
		from (
			select
			0 as debe_inicial,
			0 as haber_inicial,
			vd.debe as debe_restante,
			vd.haber as haber_restante,
			vd.*
			from vst_diariog vd
			inner join account_period ap on substring(ap.code,5,8)::int >= 1
										 and substring(ap.code,5,8)::int <= substring($1,5,8)::int
			where vd.periodo = ap.code

			union all

			select
			vd.debe as debe_inicial,
			vd.haber as haber_inicial,
			0 as debe_restante,
			0 as haber_restante,
			vd.*
			from vst_diariog vd
			where vd.periodo = substring($1,0,5)||'00'
			) A
		left join account_account aa on aa.code = A.cuenta
		left join account_type_it ati on ati.id = aa.account_type_it_id	
		group by A.cuenta) T
	inner join account_account aa on aa.code = T.cuenta
    where aa.company_id = $2;              
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
-------------------------------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_f2_balance(
    IN period character varying,
	IN company integer)
  RETURNS TABLE(mayor text, nomenclatura character varying, 
                debe_inicial numeric(64,2), haber_inicial numeric(64,2), debe numeric(64,2), 
				haber numeric(64,2), saldo_deudor numeric(64,2), saldo_acreedor numeric(64,2), 
				activo numeric(64,2), pasivo numeric(64,2), perdinat numeric(64,2), 
				ganannat numeric(64,2),perdifun numeric(64,2), gananfun numeric(64,2)) AS
$BODY$
BEGIN

RETURN QUERY 
    
	select T.mayor,T.name,T.debe_inicial,T.haber_inicial,
		   T.debe,T.haber,T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and ag.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and ag.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun
	from(
		select
		f2r.mayor,
		ag.name,
		ag.id,
		sum(f2r.debe_inicial) as debe_inicial,
		sum(f2r.haber_inicial) as haber_inicial,
		sum(f2r.debe) as debe,
		sum(f2r.haber) as haber,
		case 
			when sum(f2r.debe) + sum(f2r.debe_inicial) > sum(f2r.haber) + sum(f2r.haber_inicial) 
			then (sum(f2r.debe) + sum(f2r.debe_inicial)) - (sum(f2r.haber) + sum(f2r.haber_inicial))
			else 0
		end as saldo_deudor,
		case
			when sum(f2r.haber) + sum(f2r.haber_inicial) > sum(f2r.debe) + sum(f2r.debe_inicial)
			then (sum(f2r.haber) + sum(f2r.haber_inicial)) - (sum(f2r.debe) + sum(f2r.debe_inicial))
			else 0
		end as saldo_acreedor
		from get_f2_register($1,$2) f2r
		left join account_group ag on ag.code_prefix = f2r.mayor
    	group by f2r.mayor,ag.name,ag.id)T
	inner join account_group ag on ag.id = T.id;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

-------------------------------------------------account_htf2_report------------------------------------------------------------------