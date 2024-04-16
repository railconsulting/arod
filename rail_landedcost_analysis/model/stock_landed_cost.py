# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError,UserError
from collections import defaultdict
import logging

class StockLandCostLines(models.Model):
    _inherit = "stock.landed.cost.lines"

    bill_id = fields.Many2one('account.move', string="Vendor Bill", domain=[('move_type', '=', 'in_invoice')])

