# -*- coding: utf-8 -*-

from odoo import models, api, fields

class ProductCodePrefix(models.Model):
    _name = 'product.code.prefix'
    _description = "Model to store the prefix data"

    name = fields.Char('Nombre')
    code = fields.Char('Codigo')
