# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('partner_id')
    def _onchange_partner_for_cfdi_usage(self):
        if self.partner_id:
            self.l10n_mx_edi_usage = self.partner_id.uso_cfdi