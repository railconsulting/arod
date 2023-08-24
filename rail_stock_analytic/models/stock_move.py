# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move", "analytic.mixin"]

    def _prepare_account_move_line(
        self, qty, cost, credit_account_id, debit_account_id, svl_id, description
    ):
        self.ensure_one()
        res = super(StockMove, self)._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id, svl_id, description
        )
        #raise ValidationError("Cuenta:" + str(self.picking_id.account_id.name) +"\n" + "Analitica: " + str(self.picking_id.analytic_account_id.name))
        check = False
        if self.picking_id.account_id:
            check = True
        elif self.analytic_distribution:
            check = True
        
        if not check:
            return res
        for line in res:
            if (
                line[2]["account_id"]
                != self.product_id.categ_id.property_stock_valuation_account_id.id
            ):
                # Add analytic account in debit line
                if self.picking_id and self.picking_id.account_id:
                    line[2].update({"account_id": self.picking_id.account_id.id})
                if self.picking_id and self.picking_id.analytic_account_id:
                    analytic_distribution = {
                        self.picking_id.analytic_account_id.id: 100
                    }
                else:
                    analytic_distribution = self.analytic_distribution
                line[2].update({"analytic_distribution": analytic_distribution})
        return res

    def _prepare_procurement_values(self):
        """
        Allows to transmit analytic account from moves to new
        moves through procurement.
        """
        res = super()._prepare_procurement_values()
        if self.picking_id.account_id:
            res.update({
                "account_id": self.picking_id.account_id.id
            })
        if self.picking_id.analytic_account_id and not self.analytic_ids:
            res.update({
                "analytic_disctribution": {self.picking_id.analytic_account_id.id: 100},
            })
        if self.analytic_distribution and not self.picking_id.analytic_account_id:
            res.update({
                "analytic_distribution": self.analytic_distribution,
            })
        return res

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """
        We fill in the analytic account when creating the move line from
        the move
        """
        res = super()._prepare_move_line_vals(
            quantity=quantity, reserved_quant=reserved_quant
        )
        """ if self.picking_id.account_id:
            res.update({
                "account_id": self.picking_id.account_id.id
            }) """
        if self.picking_id.analytic_account_id and not self.analytic_ids:
            res.update({
                "analytic_disctribution": {self.picking_id.analytic_account_id.id: 100},
            })
        if self.analytic_distribution and not self.picking_id.analytic_account_id:
            res.update({
                "analytic_distribution": self.analytic_distribution,
            })
        return res

    def _action_done(self, cancel_backorder=False):
        for move in self:
            # Validate analytic distribution only for outgoing moves.
            if move.location_id.usage not in (
                "internal",
                "transit",
            ) or move.location_dest_id.usage in ("internal", "transit"):
                continue
            move._validate_distribution(
                **{
                    "product": move.product_id.id,
                    "business_domain": "stock_move",
                    "company_id": move.company_id.id,
                }
            )
        return super()._action_done(cancel_backorder=cancel_backorder)


class StockMoveLine(models.Model):
    _name = "stock.move.line"
    _inherit = ["stock.move.line", "analytic.mixin"]

    @api.model
    def _prepare_stock_move_vals(self):
        """
        In the case move lines are created manually, we should fill in the
        new move created here with the analytic account if filled in.
        """
        res = super()._prepare_stock_move_vals()
        if self.picking_id.account_id:
            res.update({
                "account_id": self.picking_id.account_id.id
            })
        if self.picking_id.analytic_account_id and not self.analytic_ids:
            res.update({
                "analytic_disctribution": {self.picking_id.analytic_account_id.id: 100},
            })
        if self.analytic_distribution and not self.picking_id.analytic_account_id:
            res.update({
                "analytic_distribution": self.analytic_distribution,
            })
        return res
