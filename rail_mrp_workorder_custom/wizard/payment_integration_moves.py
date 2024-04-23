# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from dateutil.relativedelta import relativedelta

from odoo import models, api, fields, _, Command
from odoo.tools import format_date
from odoo.exceptions import UserError


class PaymentIntegrationMoves(models.TransientModel):
    _name = 'payment.integration.moves'
    _description = 'Payment integration Moves'

    payment_id = fields.Many2one('account.payment')
    preview_data = fields.Text(compute='_compute_preview_data')

    @api.depends('payment_id')
    def _compute_preview_data(self):
        preview_columns = [
            {'field': 'account_id', 'label': _("Cuenta")},
            {'field': 'name', 'label': _("Etiqueta")},
            {'field': 'currency_id', 'label': _("Moneda")},
            {'field': 'amount_currency', 'label': _("Importe en moneda")},
            {'field': 'debit', 'label': _("Debe"), 'class': 'text-end text-nowrap'},
            {'field': 'credit', 'label': _("Haber"), 'class': 'text-end text-nowrap'},
        ]
        for record in self:
            preview_vals = [self.env['account.move']._move_dict_to_preview_vals(
                self._get_move_vals(),
                record.payment_id.company_id.currency_id)
            ]
            #raise UserError(str(preview_vals))
            record.preview_data = json.dumps({
                'groups_vals': preview_vals,
                'options': {
                    'columns': preview_columns,
                },
            })

    @api.model
    def _get_move_vals(self):
        move_lines = []
        if self.payment_id.reconciled_invoice_ids:
            records = self.payment_id.reconciled_invoice_ids
        else:
            records = self.payment_id.reconciled_bill_ids

        exchange_moves = []
        source_lines = records.line_ids.filtered(lambda x: x.matched_debit_ids or x.matched_credit_ids)
        exchange_entries = source_lines.matched_debit_ids.filtered(lambda x: x.exchange_move_id)
        exchange_entries += source_lines.matched_credit_ids.filtered(lambda x: x.exchange_move_id)
        for entry in exchange_entries:
            exchange_moves.append(entry.exchange_move_id.id)
        moves = self.env['account.move'].search([('id','in',exchange_moves)])

        moves += self.env['account.move'].search([('tax_cash_basis_origin_move_id','in', records.ids),('state','=','posted')])

        for m in moves:
            for line in m.line_ids:
                move_lines.append(Command.create({
                    'name': line.name,
                    'debit': float(line.debit),
                    'credit': float(line.credit),
                    'amount_currency': float(line.amount_currency),
                    'currency_id': line.currency_id.name,
                    'account_id': line.account_id.id
                }))
        return {
            'ref': _("Integracion de movimientos al pago: %s", self.payment_id.display_name),
            'journal_id': self.payment_id.journal_id.id,
            'date': self.payment_id.date,
            'line_ids': move_lines,
        }
