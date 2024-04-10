#-*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ResCompany(models.Model):
    _inherit = 'res.company'

    entry_type = fields.Selection(
        string='Tipo poliza', 
        selection=[
            ('employee','Por Empleado'),
            ('batch','Por Lote')],
        default='employee'
        )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    entry_type = fields.Selection(
        string='Tipo poliza', 
        selection=[
            ('employee','Por Empleado'),
            ('batch','Por Lote')],
        related='company_id.entry_type',
        readonly=False
        )
