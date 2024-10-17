# -- coding: utf-8 --
"""
@author: Oscar González M.
@Date: 10/10/24
@project rail-consulting-arod
@name: res_config_settings_extended
"""
from odoo import fields, models


class ResConfigSettingsExtended(models.TransientModel):
    _inherit = 'res.config.settings'

    permited_margin = fields.Float(
        string="Margen permitido",
        default=0.0,
        help="El margen permitido para la diferencia entre el XML importado y lo registrado en la factura.",
        config_parameter="rail_import_xml.diferencia_maxima_permitida"
    )

    cuenta_contable_diferencia = fields.Many2one(
        "account.account",
        string="Cuenta contable para diferencias",
        help="Cuenta contable para registrar diferencias de balance",
        config_parameter="rail_import_xml.cuenta_diferencia_fact_proveedor"
    )
