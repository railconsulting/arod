# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    downpayment_product = fields.Boolean('Uso en anticipos')

    @api.onchange('detailed_type')
    def _onchange_detailed_type_downpayment(self):
        if self.detailed_type != 'service':
            self.downpayment_product = False