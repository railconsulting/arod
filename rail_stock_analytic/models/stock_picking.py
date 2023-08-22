# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models,fields


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        self = self.with_context(validate_analytic=True)
        return super().button_validate()
    
    account_id = fields.Many2one('account.account', "Cuenta contable", domain=[('account_type','=','expense')])
    account_analytic_id = fields.Many2one('account.analytic.account', "Analitica")
