# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def button_open_tax_entries(self):
        ''' Redirect the user to the invoice(s) paid by this payment.
        :return:    An action on account.move.
        '''
        self.ensure_one()

        action = {
            'name': _("Impuestos trasladados"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
        }
        action.update({
            'view_mode': 'list,form',
            'domain': [('tax_cash_basis_origin_move_id', 'in', self.reconciled_invoice_ids.ids)],
        })
        return action
    
    def button_open_exhange_diff(self):
        ''' Redirect the user to the invoice(s) paid by this payment.
        :return:    An action on account.move.
        '''
        self.ensure_one()
        company = self.company_id
        exchange_journal = company.currency_exchange_journal_id
        if self.reconciled_invoice_ids:
            records = self.reconciled_invoice_ids
        else:
            records = self.reconciled_bill_ids

        exchange_moves = []
        source_lines = records.line_ids.filtered(lambda x: x.matched_debit_ids or x.matched_credit_ids)
        exchange_entries = source_lines.matched_debit_ids.filtered(lambda x: x.exchange_move_id)
        exchange_entries += source_lines.matched_credit_ids.filtered(lambda x: x.exchange_move_id)
        _logger.critical(str(exchange_entries))
        for entry in exchange_entries:
            exchange_moves.append(entry.exchange_move_id.id)
        moves = self.env['account.move'].search([('id','in',exchange_moves)])

        action = {
            'name': _("Diferencias de cambio"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
        }
        action.update({
            'view_mode': 'list,form',
            'domain': [('id', 'in', moves.ids)],
        })
        return action