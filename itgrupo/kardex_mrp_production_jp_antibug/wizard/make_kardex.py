# -*- coding: utf-8 -*-
from odoo import models, fields, api
import base64



class make_kardex_mrp_report_antibug(models.Model):
    _name = 'make.kardex.mrp.report.antibug'

    _auto = False

    def init(self):
        self.env.cr.execute(""" 

CREATE OR REPLACE VIEW public.vst_kardex_fisico1 AS 
 SELECT stock_move.product_uom,
            CASE
                WHEN uom_uom.id <> uomt.id THEN round((stock_move.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
                ELSE stock_move.price_unit_it::double precision
            END
       AS price_unit,
        CASE
            WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
            ELSE sml.qty_done
        END AS product_qty,
    sml.location_id,
    sml.location_dest_id,
    stock_move.picking_type_id,
    stock_move.product_id,
    stock_move.picking_id,
    stock_picking.invoice_id,
        CASE
            WHEN stock_picking.use_kardex_date THEN stock_move.kardex_date
            ELSE COALESCE(invoice.invoice_date::timestamp without time zone, stock_move.kardex_date)
        END AS date,
    stock_picking.name,
    stock_picking.partner_id,
        CASE
            WHEN tok.id IS NOT NULL THEN (tok.code::text || '-'::text) || tok.name::text
            ELSE ''::text
        END AS guia,
    aaait.name::text AS analitic_id,
    stock_move.id,
    product_product.default_code,
    stock_move.state AS estado,
    l_o.complete_name AS u_origen,
    l_o.usage AS usage_origen,
    l_d.complete_name AS u_destino,
    l_d.usage AS usage_destino,
    pc.name AS categoria,
    pc.id AS categoria_id,
    pname.new_name AS producto,
    product_product.default_code AS cod_pro,
    uomt.name AS unidad
   FROM stock_move
    JOIN stock_move_line sml on sml.move_id = stock_move.id
     JOIN uom_uom ON stock_move.product_uom = uom_uom.id
     JOIN stock_location l_o ON l_o.id = sml.location_id
     JOIN stock_location l_d ON l_d.id = sml.location_dest_id
     JOIN stock_picking ON stock_move.picking_id = stock_picking.id
     LEFT JOIN account_move invoice ON invoice.id = stock_picking.invoice_id
     JOIN stock_picking_type ON stock_picking.picking_type_id = stock_picking_type.id
     JOIN stock_location sl ON sl.id = sml.location_dest_id
     JOIN product_product ON stock_move.product_id = product_product.id
     LEFT JOIN ( SELECT t_pp.id,
            ((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
           FROM product_product t_pp
             JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
             left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
             LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
             LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
             LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
          GROUP BY t_pp.id) pname ON pname.id = product_product.id
     JOIN product_template ON product_product.product_tmpl_id = product_template.id
     LEFT JOIN ir_translation it ON product_template.id = it.res_id AND it.name::text = 'product.template,name'::text AND it.lang::text = 'es_PE'::text AND it.state::text = 'translated'::text
     JOIN product_category pc ON pc.id = product_template.categ_id
     JOIN uom_uom uomt ON uomt.id = product_template.uom_id
     JOIN uom_uom original ON original.id = product_template.uom_id
     left join account_analytic_account aaait on aaait.id = stock_move.analytic_account_id
     LEFT JOIN type_operation_kardex tok ON stock_picking.type_operation_sunat_id = tok.id
  WHERE (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL  and coalesce(stock_move.no_mostrar,false) = false

 union all

select 
sm.product_uom,

        CASE
                WHEN uom_uom.id <> uomt.id THEN round((sm.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
                ELSE sm.price_unit_it::double precision
            
        END AS price_unit,
        CASE
            WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
            ELSE sml.qty_done
        END AS product_qty,
        sls.id as location_id,
        sld.id as location_dest_id,
        sm.picking_type_id,
        sm.product_id,
        null::integer as picking_id,
        null::integer as invoice_id,
        mp.kardex_date::timestamp + interval '5 hours'  as date,
        mp.name as name,
        null::integer as partner_id,
        ''::text as guia,
        aaait.name::text as analitic_id,
        sm.id,
        pp.default_code,
        sm.state as estado,
        sls.complete_name as u_origen,
        sls.usage as usage_origen,
        sld.complete_name as u_destino,
        sld.usage as usage_destino,
        pc.name as categoria,
        pc.id as categoria_id,
    pname.new_name AS producto,
        pp.default_code as cod_pro,
        uomt.name as unidad
from mrp_production mp
inner join stock_move sm on sm.production_id = mp.id  or sm.raw_material_production_id = mp.id
     JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id
inner join product_product pp on pp.id = sml.product_id
     LEFT JOIN ( SELECT t_pp.id,
            ((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
           FROM product_product t_pp
             JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
             left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
             LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
             LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
             LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
          GROUP BY t_pp.id) pname ON pname.id = pp.id
inner join product_template pt on pt.id = pp.product_tmpl_id
left join ir_translation it on pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
inner join product_category pc on pc.id = pt.categ_id
inner join uom_uom uomt on uomt.id = pt.uom_id
     left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
inner join stock_location sls on sls.id = sml.location_id
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and  coalesce(sm.no_mostrar,false) = false


 union all

select 
sm.product_uom,

        CASE
                WHEN uom_uom.id <> uomt.id THEN round((sm.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
                ELSE sm.price_unit_it::double precision
            
        END AS price_unit,
        CASE
            WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
            ELSE sml.qty_done
        END AS product_qty,
        sls.id as location_id,
        sld.id as location_dest_id,
        sm.picking_type_id,
        sm.product_id,
        null::integer as picking_id,
        null::integer as invoice_id,
        sm.date as date,
        sm.name as name,
        null::integer as partner_id,
        ''::text as guia,
        aaait.name::text as analitic_id,
        sm.id,
        pp.default_code,
        sm.state as estado,
        sls.complete_name as u_origen,
        sls.usage as usage_origen,
        sld.complete_name as u_destino,
        sld.usage as usage_destino,
        pc.name as categoria,
        pc.id as categoria_id,
        pname.new_name AS producto,
        pp.default_code as cod_pro,
        uomt.name as unidad
from stock_move sm 
     JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id
inner join product_product pp on pp.id = sml.product_id
     LEFT JOIN ( SELECT t_pp.id,
            ((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
           FROM product_product t_pp
             JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
             left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
             LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
             LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
             LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
          GROUP BY t_pp.id) pname ON pname.id = pp.id
inner join product_template pt on pt.id = pp.product_tmpl_id
left join ir_translation it on pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
inner join product_category pc on pc.id = pt.categ_id
inner join uom_uom uomt on uomt.id = pt.uom_id
     left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
inner join stock_location sls on sls.id = sml.location_id
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and sm.picking_type_id is null and sm.picking_id is null  and sm.production_id is null and sm.raw_material_production_id is null;





CREATE OR REPLACE FUNCTION get_kardex_v_actualizar_veloz_mrp(IN date_ini integer, IN date_end integer, IN productos integer[], IN almacenes integer[], IN fechaini integer, IN datemove_id integer, IN company_id integer,OUT almacen character varying, OUT categoria character varying, OUT name_template character varying, OUT fecha timestamp without time zone, OUT periodo character varying, OUT ctanalitica character varying, OUT serial character varying, OUT nro character varying, OUT operation_type character varying, OUT name character varying, OUT ingreso numeric, OUT salida numeric, OUT saldof numeric, OUT debit numeric, OUT credit numeric, OUT cadquiere numeric, OUT saldov numeric, OUT cprom numeric, OUT type character varying, OUT esingreso text, OUT product_id integer, OUT location_id integer, OUT doc_type_ope character varying, OUT ubicacion_origen integer, OUT ubicacion_destino integer, OUT stock_moveid integer, OUT account_invoice character varying, OUT product_account character varying, OUT default_code character varying, OUT unidad character varying, OUT mrpname character varying, OUT ruc character varying, OUT comapnyname character varying, OUT cod_sunat character varying, OUT tipoprod character varying, OUT coduni character varying, OUT metodo character varying, OUT cu_entrada numeric, OUT cu_salida numeric, OUT period_name character varying, OUT stock_doc character varying, OUT origen character varying, OUT destino character varying, OUT type_doc character varying, OUT numdoc_cuadre character varying, OUT doc_partner character varying, OUT fecha_albaran timestamp without time zone, OUT pedido_compra character varying, OUT licitacion character varying, OUT doc_almac character varying, OUT lote character varying, OUT correlativovisual integer)
    RETURNS SETOF record AS
$BODY$  
DECLARE 
    location integer;
    product integer;
    precprom numeric;
    h record;
    h1 record;
    hproduct record;
    h2 record;
    dr record;
    pt record;
    il record;
    loc_id integer;
    prod_id integer;
    contador integer;
    lote_idmp varchar;
    avanceop integer;


  rf record;
  loc_1 record;
  loc_2 record;
  
  pp_1 record;
  pp_2 record;

datos_con record;
    
BEGIN

    select res_partner.name,res_partner.vat as nro_documento from res_company 
    inner join res_partner on res_company.partner_id = res_partner.id
    into h;

    -- foreach product in array $3 loop
        
                        loc_id = -1;
                        prod_id = -1;
                        lote_idmp = -1;
--    foreach location in array $4  loop
--      for dr in cursor_final loop
            saldof =0;
            saldov =0;
            cprom =0;
            cadquiere =0;
            ingreso =0;
            salida =0;
            debit =0;
            credit =0;
            avanceop = 0;
            contador = 2;
            
            
            for dr in 
            select * from tmp_kardexv_veloz_mrp
                loop
                if dr.location_id = ANY ($4) and dr.product_id = ANY ($3) then
                    if dr.ipxvalue = 'specific' then
                                        if loc_id = dr.location_id then
                            contador = 1;
                            else
                            
                            loc_id = dr.location_id;
                            prod_id = dr.product_id;
                    --    foreach location in array $4  loop
                            
                    --      for dr in cursor_final loop
                            saldof =0;
                            saldov =0;
                            cprom =0;
                            cadquiere =0;
                            ingreso =0;
                            salida =0;
                            debit =0;
                            credit =0;
                        end if;
                            else
                        

                                if prod_id = dr.product_id and loc_id = dr.location_id then
                                contador =1;
                                else

                            loc_id = dr.location_id;
                            prod_id = dr.product_id;
                    --    foreach location in array $4  loop
                    --      for dr in cursor_final loop
                                saldof =0;
                                saldov =0;
                                cprom =0;
                                cadquiere =0;
                                ingreso =0;
                                salida =0;
                                debit =0;
                                credit =0;
                                end if;
                     end if;

                        select '' as category_sunat_code, '' as uom_sunat_code, product_product.default_code as codigoproducto
                        from product_product
                        inner join product_template on product_product.product_tmpl_id = product_template.id
                        inner join product_category on product_template.categ_id = product_category.id
                        inner join uom_uom on product_template.uom_id = uom_uom.id
                        --left join category_product_sunat on product_category.cod_sunat = category_product_sunat.id
                        --left join category_uom_sunat on uom_uom.cod_sunat = category_uom_sunat.id
                        where product_product.id = dr.product_id into h1;


                        select t_pp.id, max(t_pt.name)::varchar || ' ' || replace(array_agg(pav.name)::varchar,'{NULL}','') as new_name from product_product t_pp
inner join product_template t_pt on t_pp.product_tmpl_id = t_pt.id
left join product_variant_combination pvc on pvc.product_product_id = t_pp.id
left join product_template_attribute_value ptav on ptav.id = pvc.product_template_attribute_value_id
left join product_attribute_value pav on pav.id = ptav.product_attribute_value_id
where t_pp.id = dr.product_id
group by t_pp.id   into hproduct;


                                                            select * from stock_location where id = dr.location_id into h2;


            select * from stock_location where id = dr.id_origen into loc_1;
            select * from stock_location where id = dr.id_destino into loc_2;
 
            select put.factor as f1 , pu.factor as f2 from stock_move sm 
            inner join product_product pp on pp.id = sm.product_id
            inner join product_template pt2 on pt2.id = pp.product_tmpl_id
            inner join uom_uom pu on pu.id = pt2.uom_id
            inner join uom_uom put on put.id = sm.product_uom           
            where sm.id = dr.stock_moveid  into pp_1;

           select sp.name,sm.product_id from
           stock_picking sp
           inner join stock_move sm on sm.picking_id = sp.id
           where sm.id = dr.stock_moveid into datos_con;

          ---- esto es para las variables que estan en el crusor y pasarlas a las variables output
          select * from stock_move where id = dr.stock_moveid into rf;
          if dr.stock_moveid = $6 then
            UPDATE stock_move set price_unit_it = (cprom/ pp_1.f2) * pp_1.f1  where id = dr.stock_moveid;
          end if;
                
                    ---- esto es para las variables que estan en el crusor y pasarlas a las variables output
                    
                    almacen=dr.almacen;
                    categoria=dr.categoria;
                    name_template=hproduct.new_name;
                    fecha=dr.fecha - interval '5' hour;
                    periodo=dr.periodo;
                    ctanalitica=dr.ctanalitica;
                    serial=dr.serial;
                    nro=dr.nro;
                    operation_type=dr.operation_type;
                    name=dr.name;
                    type=dr.type;
                    esingreso=dr.esingreso;
                    product_id=dr.product_id;
                    correlativovisual = dr.correlativovisual;

                    correlativovisual = avanceop;

                    avanceop = avanceop +1;

                    location_id=dr.location_id;
                    doc_type_ope=dr.doc_type_ope;
                    ubicacion_origen=dr.id_origen;
                    ubicacion_destino=dr.id_destino;
                    stock_moveid=dr.stock_moveid;
                    account_invoice=0;
                    product_account=dr.product_account;
                    default_code=h1.codigoproducto;
                    unidad=dr.unidad;
                    mrpname='';
                    stock_doc=dr.stock_doc;
                    origen=dr.origen;
                    destino=dr.destino;
                    type_doc=dr.type_doc;
                                numdoc_cuadre=dr.numdoc_cuadre;
                                if dr.numdoc_cuadre::varchar = ''::varchar then
                                    numdoc_cuadre=dr.doc_almac;
                                end if;
                                doc_partner=dr.nro_documento;
                                lote= dr.lote;


                

                     ruc = h.nro_documento;
                     comapnyname = h.name;
                     cod_sunat = ''; 
                     default_code = h1.codigoproducto;
                     tipoprod = h1.category_sunat_code; 
                     coduni = h1.uom_sunat_code;
                     metodo = 'Costo promedio';
                     
                     period_name = dr.period_name;
                    
                     fecha_albaran = dr.fecha_albaran - interval '5' hour;
                     pedido_compra = dr.pedido_compra;
                     licitacion = dr.licitacion;
                     doc_almac = dr.doc_almac;


                    --- final de proceso de variables output

                
                    ingreso =coalesce(dr.ingreso,0);
                    salida =coalesce(dr.salida,0);
                    --if dr.serial is not null then 
                        debit=coalesce(dr.debit,0);
                    --else
                        --if dr.ubicacion_origen=8 then
                            --debit =0;
                        --else
                            ---debit = coalesce(dr.debit,0);
                        --end if;
                    --end if;
                    

                    
                        credit =coalesce(dr.credit,0);
                    
                    cadquiere =coalesce(dr.cadquiere,0);
                    precprom = cprom;
                    if cadquiere <=0::numeric then
                        cadquiere=cprom;
                    end if;
                    if salida>0::numeric then
                        credit = cadquiere * salida;
                    end if;
                    saldov = saldov + (debit - credit);
                    saldof = saldof + (ingreso - salida);
                    if saldof > 0::numeric then
                        if esingreso= 'ingreso' or ingreso > 0::numeric then
                            if saldof != 0 then
                                cprom = saldov/saldof;
                            else
                                            cprom = saldov;
                                 end if;
                            if ingreso = 0 then
                                            cadquiere = cprom;
                            else
                                    cadquiere =debit/ingreso;
                            end if;
                            --cprom = saldov / saldof;
                            --cadquiere = debit / ingreso;
                        else
                            if salida = 0::numeric then
                                if debit + credit > 0::numeric then
                                    cprom = saldov / saldof;
                                    cadquiere=cprom;
                                end if;
                            else
                                credit = salida * cprom;
                            end if;
                        end if;
                    else
                        cprom = 0;
                    end if;
                        

                    if saldov <= 0::numeric and saldof <= 0::numeric then
                        dr.cprom = 0;
                        cprom = 0;
                    end if;
                    --if cadquiere=0 then
                    --  if trim(dr.operation_type) != '05' and trim(dr.operation_type) != '' and dr.operation_type is not null then
                    --    cadquiere=precprom;
                    --    debit = ingreso*cadquiere;
                    --    credit=salida*cadquiere;
                    --  end if;
                    --end if;
                    dr.debit = round(debit,8);
                    dr.credit = round(credit,8);
                    dr.cprom = round(cprom,8);
                    dr.cadquiere = round(cadquiere,8);
                    dr.credit = round(credit,8);
                    dr.saldof = round(saldof,8);
                    dr.saldov = round(saldov,8);
                    if ingreso>0 then
                        cu_entrada =debit/ingreso;
                    else
                        cu_entrada =debit;
                    end if;

                    if salida>0 then
                        cu_salida =credit/salida;
                    else
                    cu_salida =credit;
                    end if;

                    RETURN NEXT;
                end if;
    end loop;
    --return query select * from vst_kardex_sunat where fecha_num(vst_kardex_sunat.fecha) between $1 and $2 and vst_kardex_sunat.product_id = ANY($3) and vst_kardex_sunat.location_id = ANY($4) order by location_id,product_id,fecha;
END
$BODY$
    LANGUAGE plpgsql VOLATILE
    COST 100
    ROWS 1000;

 """ )
