# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type')
    landed_cost_product_id = fields.Many2one('product.product', string='Landed Cost Product')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update(
            picking_type_id= int(ICPSudo.get_param('custom_landed_cost.picking_type_id')),
            landed_cost_product_id= int(ICPSudo.get_param('custom_landed_cost.landed_cost_product_id')),
        )

        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'custom_landed_cost.picking_type_id', self.picking_type_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            'custom_landed_cost.landed_cost_product_id', self.landed_cost_product_id.id)
        return res
