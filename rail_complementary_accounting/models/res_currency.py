# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    complementary_currency = fields.Boolean("Moneda complementaria")