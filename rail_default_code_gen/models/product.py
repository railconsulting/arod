# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo.exceptions import ValidationError
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    prefix_id = fields.Many2one('product.code.prefix',"Tipo Prefijo")

class ProductProduct(models.Model):
    _inherit = 'product.product'

    prefix_id = fields.Many2one('product.code.prefix', "Tipo Prefijo", related='product_tmpl_id.prefix_id')

    @api.model_create_multi
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        if self.env.company and self.env.company.product_int_ref_generator:
            if not self.env.company.product_sequence:
                raise ValidationError("Debes configurar una secuencia para la referencia de los productos")
            prefix = res.prefix_id
            if not prefix:
                raise ValidationError("Debes elegir un prefijo para este producto")
            sequence = self.env['ir.sequence'].next_by_code(self.env.company.product_sequence.code)
            product_code_str = prefix.code + str(sequence)  
                        
            if product_code_str != '':
                res.default_code = product_code_str   
        return res
