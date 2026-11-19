# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')]


class ApprovalCategory(models.Model):
    _inherit = "approval.category"

    has_sale_order = fields.Selection(CATEGORY_SELECTION,
                                      string="Has Sale Order",
                                      default="no",
                                      required=True)

    @api.model
    def create(self, vals):
        elem = super(ApprovalCategory, self).create(vals)
        for i in elem:
            sales = self.env['sale.order'].search([]).filtered(lambda r: i.id in r.team_id.approval_sale_id.ids)
            sales.actualizacion_masiva()
        return elem

    def write(self, vals):
        elem = super(ApprovalCategory, self).write(vals)
        for i in self:
            sales = self.env['sale.order'].search([]).filtered(lambda r: i.id in r.team_id.approval_sale_id.ids)
            sales.actualizacion_masiva()
        return elem


class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    sale_id = fields.Many2one(comodel_name='sale.order', string='Sale Order')
    sale_id_project = fields.Many2one(comodel_name='sale.order', string='Sale Order Project')
    has_sale_order = fields.Selection(related="category_id.has_sale_order")
    project_id = fields.Many2one('project.project', 'Proyecto')

    def action_approve(self):
        t = super(ApprovalRequest, self).action_approve()
        self.date = fields.Datetime.now()
        approver = self.mapped('approver_ids').filtered(
            lambda approver: approver.user_id == self.env.user
        )
        approver.write({'datetime_approve': fields.Datetime.now()})
        return t


class CrmTeam(models.Model):
    _inherit = "crm.team"

    approval_id = fields.Many2many('approval.category', 'crmteam_aprobal_proyect_rel', 'crm_id', 'aprobal_id',
                                   'Aprobacion Proyecto')

    approval_sale_id = fields.Many2many('approval.category', 'crmteam_aprobal_cotizacion_rel', 'crm_id', 'aprobal_id',
                                        'Aprobacion Cotizacion')

    user_factibility_id = fields.Many2one('wk.team', 'Equipo de Factibilidad')
    user_project_manager_id = fields.Many2one('wk.team', 'Equipo de Manager Proyecto')


class Sale(models.Model):
    _inherit = "sale.order"

    approval_id = fields.One2many(comodel_name='approval.request',
                                  inverse_name='sale_id',
                                  string='Aprovate')  # este es de projecto

    approval_sale_id = fields.One2many(comodel_name='approval.request',
                                       inverse_name='sale_id_project',
                                       string='Aprobacion Cotizacion')

    @api.onchange('team_id')
    def onchange_team_id(self):
        # self.create_level_ids()
        pass

    def actualizacion_masiva(self):
        for i in self:
            if i.type_id.is_approval_required == True and i.state == 'draft':
                for aprobacion in i.approval_sale_id:
                    if aprobacion.request_status in ('new', 'pending'):
                        self.env.cr.execute(""" delete from approval_request where id =  """ + str(aprobacion.id))

                for item in i.team_id.approval_sale_id:
                    if len(self.env['approval.request'].search(
                            [('sale_id_project', '=', i.id), ('name', '=', str(i.name + "-" + item.name))])) == 0:
                        data = {
                            'name': str(i.name + "-" + item.name),
                            'category_id': item.id,
                            'partner_id': i.partner_id.id,
                            'request_owner_id': self.env.user.id,
                            'reference': str(i.name),
                            'sale_id_project': i.id
                        }
                        temp = self.env['approval.request'].create(data)

                        for user in item.user_ids:
                            self.env['approval.approver'].create({
                                'user_id': user.id,
                                'request_id': temp.id,
                            })
                        temp.action_confirm()

    @api.model
    def create_level_ids(self):
        if self.ids and self[0].type_id.is_approval_required == True:

            search = self.env['approval.request'].search([(
                'sale_id_project', '=', self.ids[0]
            )])
            for elemt in search:
                self.env.cr.execute(""" delete from approval_request where id =  """ + str(element.id))

            for item in self.team_id.approval_sale_id:
                data = {
                    'name': str(self.name + "-" + item.name),
                    'category_id': item.id,
                    'partner_id': self.partner_id.id,
                    'request_owner_id': self.env.user.id,
                    'reference': str(self.name),
                    'sale_id_project': self.ids[0]
                }
                temp = self.env['approval.request'].create(data)

                for user in item.user_ids:
                    self.env['approval.approver'].create({
                        'user_id': user.id,
                        'request_id': temp.id,
                    })
                temp.action_confirm()

    # search = self.env['approval.request'].search([(   #aca se ponia para los projects in saleorder
    #    'sale_id','=', self.ids[0]
    # )])
    # for elemt in search:
    #    elemt.action_cancel()
    #    elemt.unlink()

    # flag = False

    # for line in self.order_line:
    #    if line.product_id.project_template_id.id:
    #        flag= True

    # if flag:
    #    for item in self.team_id.approval_id:
    #        data = {
    #            'name': str(self.name + "-" + item.name),
    #            'category_id': item.id,
    #            'partner_id': self.partner_id.id,
    #            'request_owner_id': self.env.user.id,
    #            'reference': str(self.name),
    #            'sale_id': self.ids[0]
    #        }
    #        temp = self.env['approval.request'].create(data)

    #        for user in item.user_ids:
    #            self.env['approval.approver'].create({
    #                'user_id': user.id,
    #                'request_id': temp.id,
    #            })
    #        temp.action_confirm()

    @api.model
    def create(self, vals):
        t = super(Sale, self).create(vals)
        if 'team_id' in vals:
            t.create_level_ids()
        return t

    def write(self, vals):
        t = super(Sale, self).write(vals)
        if 'team_id' in vals:
            self.create_level_ids()
        return t


class Project_Project(models.Model):
    _inherit = 'project.project'

    approval_id = fields.One2many(comodel_name='approval.request',
                                  inverse_name='project_id',
                                  string='Aprovate')  # este es de projecto

    @api.model
    def create_level_ids(self):
        if self.ids:

            search = self.env['approval.request'].search([(
                'project_id', '=', self.ids[0]
            )])
            for elemt in search:
                elemt.action_cancel()
                elemt.unlink()

            for item in self.sale_order_id.team_id.approval_id:
                data = {
                    'name': str(self.name + "-" + item.name),
                    'category_id': item.id,
                    'partner_id': self.partner_id.id,
                    'request_owner_id': self.env.user.id,
                    'reference': str(self.name),
                    'project_id': self.ids[0]
                }
                temp = self.env['approval.request'].create(data)

                for user in item.user_ids:
                    self.env['approval.approver'].create({
                        'user_id': user.id,
                        'request_id': temp.id,
                    })
                temp.action_confirm()

    @api.model
    def create(self, vals):
        t = super(Project_Project, self).create(vals)
        if 'sale_order_id' in vals:
            t.create_level_ids()
        return t

    def write(self, vals):
        t = super(Project_Project, self).write(vals)
        if 'sale_order_id' in vals:
            self.create_level_ids()
        return t


class ProjectTask(models.Model):
    _inherit = "project.task"

    is_closed = fields.Boolean(compute="get_is_closed")

    def get_is_closed(self):
        for i in self:
            if i.stage_id.closed:
                i.is_closed = True
            else:
                i.is_closed = False

    is_sale_approvate = fields.Boolean(string='Sale Approvate',
                                       compute='_validate_approved')

    is_actitave_invoice = fields.Boolean(compute='_compute_actitave_invoice',
                                         string='Invoice')

    def _compute_actitave_invoice(self):
        for record in self:
            task = self.env['project.task'].search([(
                'project_id', '=', record.project_id.id
            )])
            record.is_actitave_invoice = True

            for item in task:
                if item.is_closed == False:
                    record.is_actitave_invoice = False

    def _validate_approved(self):
        for record in self:
            record.is_sale_approvate = True
            if len(record.project_id.approval_id) > 0:
                for item in record.project_id.approval_id:
                    if item.request_status != 'approved':
                        record.is_sale_approvate = False

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        if self.is_sale_approvate == False:
            raise UserError(_("Falta Autorizar el pedido"))

    def activate_invoice(self):
        self.sale_line_id.subscription_id.is_actitave_invoice = True

    def next_stage_id(self):
        project = self.env['project.task.type'].search([(
            'project_ids', 'in', self.project_id.id
        )])
        temp = 0
        for item in project:
            if item.sequence > self.stage_id.sequence:
                self.stage_id = item
                break


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    is_actitave_invoice = fields.Boolean(string='Invoice Activate')


class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    datetime_approve = fields.Datetime('Fecha y Hora')
