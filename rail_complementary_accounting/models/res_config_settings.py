# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    complementary_accounting = fields.Boolean("Asientos complementarios", related="company_id.complementary_accounting",
                                              readonly = False)