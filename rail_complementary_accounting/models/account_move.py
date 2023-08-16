# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    complementary_line = fields.Boolean("Linea complementaria")

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('journal_id')
    def _get_complementary_option(self):
        for r in self:
            r.complementary_entry = r.journal_id.complementary_entry

    complementary_entry = fields.Boolean("Asiento complementarios")

    def _compute_complementary_vals(self):
        for r in self:
            payable_line = r.line_ids.filtered(lambda x: x.account_type == 'liability_payable')
            if r.partner_id.property_complementary_account_id:
                complementary_account = r.partner_id.property_complementary_account_id
            else:
                complementary_account = r.journal_id.complementary_account_id
            if not complementary_account:
                raise ValidationError("No se ha encontrado una cuenta complementaria \n" +
                                      "Por favor elige una cuenta en la ficha del contacto o en el diario de proveedores")
            payable_amt = payable_line.credit #--100
            payable_amt_currency = payable_line.amount_currency #--5
            rate = payable_line.currency_rate
            new_payable_amt = payable_amt_currency
            complementary_amt = payable_amt + payable_amt_currency
            lines = []
            complementary_vals = ([0,0,{
                'account_id':complementary_account.id,
                'name': "Ajuste complementario",
                'currency_id': r.currency_id.id,
                'amount_currency': 0.00,
                'is_same_currency': False,
                'credit': complementary_amt,
                'display_type': 'epd',
                'move_id': r.id,
                'complementary_line': True,
            }])
            lines.append(complementary_vals)

            cxp = ([1, payable_line.id, {
                'credit': new_payable_amt * -1,
            }])
            lines.append(cxp)
            #raise ValidationError(str(lines))
            r.update({
                'line_ids': lines,
            })
    
    def action_post(self):
        #inherit of the function from account.move to validate a new tax and the priceunit of a downpayment
        for i in self:
            if i.complementary_entry:
                i._compute_complementary_vals()
        return super(AccountMove, self).action_post()
    
    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        for r in self:
            payable_line = r.line_ids.filtered(lambda x: x.account_type == 'liability_payable')
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