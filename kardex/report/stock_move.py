from odoo import api, models
import logging

class StockMove(models.Model):
    _inherit = 'stock.move'

    def create(self, vals):
        res = super(StockMove, self).create(vals)
        for rec in res:
            if not rec.purchase_line_id:
                rec.price_unit = rec.product_id.standard_price
        return res
