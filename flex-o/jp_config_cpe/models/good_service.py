from odoo import api, fields, models

class TypeOperation(models.Model):
    _name = 'type.operation'
    _description = 'Types of Operations'
    
    name = fields.Char(string='Code')
    description = fields.Char(string='Description')

    def name_get(self):
        result = []
        for type_operation in self:
            result.append([type_operation.id,type_operation.description])
        return result

class GoodService(models.Model):
    _name = 'good.service'
    _description = 'Goods or Services'
    
    name = fields.Char(string='Code')
    description = fields.Char(string='Description')

    def name_get(self):
        result = []
        for good_service in self:
            result.append([good_service.id,good_service.description])
        return result
