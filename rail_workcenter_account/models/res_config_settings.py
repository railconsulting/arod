# -*- coding: utf-8 -*-

from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    wc_journal_id = fields.Many2one('account.journal', related="company_id.wc_journal_id",readonly=False)
    