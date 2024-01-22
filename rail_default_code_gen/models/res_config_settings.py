# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    product_int_ref_generator = fields.Boolean(
        string="Product Internal Reference Generator Feature")
    product_sequence = fields.Many2one(
        'ir.sequence', string="Product Sequence")
    


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_int_ref_generator = fields.Boolean(
        string="Product Internal Reference Generator Feature", related='company_id.product_int_ref_generator', readonly=False)
    product_sequence = fields.Many2one(
        'ir.sequence', string="Product Sequence", related='company_id.product_sequence', readonly=False)
    
   
    def action_generate_int_ref(self):
        return {
            'name': 'Generate Internal Reference',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'internal.reference.wizard',
            'target': 'new',
        }
