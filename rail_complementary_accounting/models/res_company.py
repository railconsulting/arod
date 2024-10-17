# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    complementary_accounting = fields.Boolean("Contabilidad complementaria")