# -*- coding: utf-8 -*-
from contextlib import ExitStack, contextmanager
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import format_amount

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    complementary_line = fields.Boolean("Linea complementaria")

    @api.ondelete(at_uninstall=False)
    def _prevent_automatic_line_deletion(self):
        if not self.env.context.get('dynamic_unlink'):
            for line in self:
                if line.display_type == 'tax' and line.move_id.line_ids.tax_ids:
                    raise ValidationError(_(
                        "You cannot delete a tax line as it would impact the tax report"
                    ))
                elif line.display_type == 'payment_term' and not line.move_id.complementary_entry:
                    raise ValidationError(_(
                        "You cannot delete a payable/receivable line as it would not be consistent "
                        "with the payment terms"
                    ))

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('company_id','journal_id','currency_id')
    def _get_complementary_option(self):
        for r in self:
            comp_entry = False
            if r.move_type == 'in_invoice' and r.company_id.complementary_accounting and r.currency_id.complementary_currency:
                comp_entry = True
            r.complementary_entry = comp_entry

    complementary_entry = fields.Boolean("Asiento complementarios", compute="_get_complementary_option")
    manual_rate = fields.Monetary("Tipo de cambio", currency_field="company_currency_id")

    @contextmanager
    def _check_balanced(self, container):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        with self._disable_recursion(container, 'check_move_validity', default=True, target=False) as disabled:
            yield
            if disabled:
                return

        unbalanced_moves = self._get_unbalanced_moves(container)
        if unbalanced_moves:
            error_msg = _("An error has occurred.")
            for move_id, sum_debit, sum_credit in unbalanced_moves:
                move = self.browse(move_id)
                error_msg += _(
                    "\n\n"
                    "The move (%s) is not balanced.\n"
                    "The total of debits equals %s and the total of credits equals %s.\n"
                    "You might want to specify a default account on journal \"%s\" to automatically balance each move.",
                    move.display_name,
                    format_amount(self.env, sum_debit, move.company_id.currency_id),
                    format_amount(self.env, sum_credit, move.company_id.currency_id),
                    move.journal_id.name)
            _logger.critical(error_msg)

    def _compute_complementary_vals(self):
        for r in self:
            payable_line = r.line_ids.filtered(lambda x: x.account_type == 'liability_payable' and x.complementary_line == False)
            all_debit_lines = r.line_ids.filtered(lambda x: x.id != payable_line.id and x.debit > 0 and x.complementary_line == False)
            all_credit_lines = r.line_ids.filtered(lambda x: x.complementary_line == False and x.credit > 0 and x.account_type != 'liability_payable')
            if r.partner_id.property_complementary_account_id:
                complementary_account = r.partner_id.property_complementary_account_id
            else:
                complementary_account = r.journal_id.complementary_account_id
            if not complementary_account:
                raise ValidationError("No se ha encontrado una cuenta complementaria \n" +
                                      "Por favor elige una cuenta en la ficha del contacto o en el diario de proveedores")
            
            payable_amt = payable_line.credit
            rate = r.manual_rate
            currency_decimal_places = r.currency_id.decimal_places

            lines = []

            for d in all_debit_lines:
                dvals = ([1, d.id, {
                    'amount_currency':  d.debit,
                    'debit': round(d.debit * rate, currency_decimal_places),
                }])
                lines.append(dvals)
            """ for c in all_credit_lines:
                cvals = ([1, c.id, {
                    #'amount_currency':  round(c.credit * rate, currency_decimal_places),
                    'credit': round(c.credit * rate, currency_decimal_places),
                }])
                lines.append(cvals) """

            # First recompute the debit and credit values that are not related to payable amounts
            # This is because odoo recompute the debit amount based on the balance amount on create write methods
            r.update({
                'line_ids': lines,
            })

            # Recompute the cxp value and append the complementary line
            cxp_list = []
            cxp = ([1, payable_line.id, {
                'amount_currency': payable_line.amount_currency,
                'credit': payable_line.amount_currency * -1,
            }])
            cxp_list.append(cxp)

            complementary_amt = round(payable_amt * rate, currency_decimal_places) - payable_amt #928 * 18.67

            complementary_vals = ([0,0,{
                'account_id':complementary_account.id,
                'name': "Ajuste complementario: " + r.name,
                'currency_id': payable_line.currency_id.id,
                'date_maturity': payable_line.date_maturity,
                'amount_currency': 0,#round(complementary_amt / rate, currency_decimal_places) * -1,
                'is_same_currency': False,
                'credit': complementary_amt,#complementary_amt,
                'display_type': 'payment_term',
                'partner_id': payable_line.partner_id.id,
                'move_id': r.id,
                'complementary_line': True,
            }])
            cxp_list.append(complementary_vals)
            r.update({
                'line_ids': cxp_list
            })
            
    
    def action_post(self):
        #inherit of the function from account.move to validate a new tax and the priceunit of a downpayment
        for invoice in self:
            if invoice.complementary_entry:
                invoice._compute_complementary_vals()
        return super(AccountMove, self).action_post()
    
    
    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        for r in self:
            payable_line = r.line_ids.filtered(lambda x: x.account_type == 'liability_payable' and x.complementary_line == False)
            complementary_line = r.line_ids.filtered(lambda x: x.complementary_line == True)
            new_payable_amt = payable_line.credit + complementary_line.credit
            lines = []
            for l in complementary_line:
                vals = ([2, l.id])
                lines.append(vals)
            cxp = ([1, payable_line.id, {
                'credit': new_payable_amt,
            }])
            lines.append(cxp)
            r.write({
                'line_ids': lines,
            })
            return res