# -*- coding: utf-8 -*-

from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    wc_journal_id = fields.Many2one('account.journal', string="Diario contable")
