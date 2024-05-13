<<<<<<< Updated upstream
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from dateutil.relativedelta import relativedelta

from odoo import models, api, fields, _, Command
from odoo.tools import format_date
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class PaymentIntegrationLines(models.TransientModel):
    _name = 'payment.integration.lines'
    _description = 'Payment integration lines'

    wizard_id = fields.Many2one('payment.integration.moves')
    sequence = fields.Integer('Secuencia')
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)
    move_id = fields.Many2one('account.move')
    name = fields.Char('Nombre')
    account_id = fields.Many2one('account.account', 'Cuenta')
    currency_id = fields.Many2one('res.currency',"Moneda")
    amount_currency = fields.Float("Importe en moneda")
    debit = fields.Float('Debe')
    credit = fields.Float("Haber")
    is_subtotal = fields.Boolean("Es subtotal")


class PaymentIntegrationMoves(models.TransientModel):
    _name = 'payment.integration.moves'
    _description = 'Payment integration Moves'

    move_lines = fields.One2many('payment.integration.lines','wizard_id')

    def _get_report_data(self):
        active_obj = self.env.context.get('active_id')
        payment_id = self.env['account.payment'].search([('id','=',active_obj)])
        lines = []
        for l in self.move_lines.filtered(lambda x: x.is_subtotal == False):
            vals = {
                'display_type': l.display_type,
                'name': l.name,
                'account_id': l.account_id.display_name,
                'debit': l.debit,
                'credit': l.credit,
            }
            lines.append(vals)
        data = {
            'ids': self.env.context.get('active_ids', []),
            'model': 'payment.integration.moves',
            'payment': payment_id.name,
            'lines': lines,
        }
        return self.env.ref('rail_mrp_workorder_custom.payment_integration_report').report_action(self, data=data)

    def generate_report(self):
        return self._get_report_data()


    @api.model    
    def default_get(self, fields):       
        rec = super(PaymentIntegrationMoves, self).default_get(fields)        
        move_lines = [(5,0,0)]        
        active_obj = self.env.context.get('active_id')
        payment_id = self.env['account.payment'].search([('id','=',active_obj)])  
        if payment_id.reconciled_invoice_ids:
            records = payment_id.reconciled_invoice_ids
        else:
            records = payment_id.reconciled_bill_ids

        exchange_moves = []
        source_lines = records.line_ids.filtered(lambda x: x.matched_debit_ids or x.matched_credit_ids)
        exchange_entries = source_lines.matched_debit_ids.filtered(lambda x: x.exchange_move_id)
        exchange_entries += source_lines.matched_credit_ids.filtered(lambda x: x.exchange_move_id)
        for entry in exchange_entries:
            exchange_moves.append(entry.exchange_move_id.id)
        moves = self.env['account.move'].search([('id','in',exchange_moves)])

        moves += self.env['account.move'].search([('tax_cash_basis_origin_move_id','in', records.ids),('state','=','posted')])
        seq = total_debit  = total_credit = 0
        for m in moves:
            seq += 1
            move_lines.append(Command.create({
                'move_id':m.id,
                'sequence': seq,
                'display_type': 'line_section',
                'name': m.display_name,
            }))
            for line in m.line_ids:
                total_debit += line.debit
                total_credit += line.credit
                move_lines.append(Command.create({
                    'move_id': line.move_id.id,
                    'sequence': seq,
                    'name': line.name,
                    'debit': float(line.debit),
                    'credit': float(line.credit),
                    'amount_currency': float(line.amount_currency),
                    'currency_id': line.currency_id.id,
                    'account_id': line.account_id.id
                })) 
                seq +=1 
            move_lines.append(Command.create({
                'move_id':m.id,
                'is_subtotal': True,
                'sequence': seq,
                'display_type': 'line_section',
                'name': "TOTAL " + m.display_name + "                                                                                                                                 "\
                        + '{:.2f}'.format(total_debit) + "                  " + '{:.2f}'.format(total_credit),
            }))
            seq += 1
        rec['move_lines'] = move_lines
        return rec

    """  @api.depends('payment_id')
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
        } """
=======
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from dateutil.relativedelta import relativedelta

from odoo import models, api, fields, _, Command
from odoo.tools import format_date
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class PaymentIntegrationLines(models.TransientModel):
    _name = 'payment.integration.lines'
    _description = 'Payment integration lines'

    wizard_id = fields.Many2one('payment.integration.moves')
    sequence = fields.Integer('Secuencia')
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)
    move_id = fields.Many2one('account.move')
    name = fields.Char('Nombre')
    account_id = fields.Many2one('account.account', 'Cuenta')
    currency_id = fields.Many2one('res.currency',"Moneda")
    amount_currency = fields.Float("Importe en moneda")
    debit = fields.Float('Debe')
    credit = fields.Float("Haber")
    is_subtotal = fields.Boolean("Es subtotal")


class PaymentIntegrationMoves(models.TransientModel):
    _name = 'payment.integration.moves'
    _description = 'Payment integration Moves'

    move_lines = fields.One2many('payment.integration.lines','wizard_id')

    def _get_report_data(self):
        active_obj = self.env.context.get('active_id')
        payment_id = self.env['account.payment'].search([('id','=',active_obj)])
        lines = []
        for l in self.move_lines.filtered(lambda x: x.is_subtotal == False):
            vals = {
                'display_type': l.display_type,
                'name': l.name,
                'account_id': l.account_id.display_name,
                'debit': l.debit,
                'credit': l.credit,
            }
            lines.append(vals)
        data = {
            'ids': self.env.context.get('active_ids', []),
            'model': 'payment.integration.moves',
            'payment': payment_id.name,
            'lines': lines,
        }
        return self.env.ref('rail_mrp_workorder_custom.payment_integration_report').report_action(self, data=data)

    def generate_report(self):
        return self._get_report_data()


    @api.model    
    def default_get(self, fields):       
        rec = super(PaymentIntegrationMoves, self).default_get(fields)        
        move_lines = [(5,0,0)]        
        active_obj = self.env.context.get('active_id')
        payment_id = self.env['account.payment'].search([('id','=',active_obj)])  
        if payment_id.reconciled_invoice_ids:
            records = payment_id.reconciled_invoice_ids
        else:
            records = payment_id.reconciled_bill_ids

        exchange_moves = []
        source_lines = records.line_ids.filtered(lambda x: x.matched_debit_ids or x.matched_credit_ids)
        exchange_entries = source_lines.matched_debit_ids.filtered(lambda x: x.exchange_move_id)
        exchange_entries += source_lines.matched_credit_ids.filtered(lambda x: x.exchange_move_id)
        for entry in exchange_entries:
            exchange_moves.append(entry.exchange_move_id.id)
        moves = self.env['account.move'].search([('id','in',exchange_moves)])

        moves += self.env['account.move'].search([('tax_cash_basis_origin_move_id','in', records.ids),('state','=','posted')])
        seq = total_debit  = total_credit = 0
        for m in moves:
            seq += 1
            move_lines.append(Command.create({
                'move_id':m.id,
                'sequence': seq,
                'display_type': 'line_section',
                'name': m.display_name,
            }))
            for line in m.line_ids:
                total_debit += line.debit
                total_credit += line.credit
                move_lines.append(Command.create({
                    'move_id': line.move_id.id,
                    'sequence': seq,
                    'name': line.name,
                    'debit': float(line.debit),
                    'credit': float(line.credit),
                    'amount_currency': float(line.amount_currency),
                    'currency_id': line.currency_id.id,
                    'account_id': line.account_id.id
                })) 
                seq +=1 
            subtotal_string =  "TOTAL {:<150}{:>15.2f}                  {:.2f}".format(m.display_name, total_debit, total_credit)
            _logger.critical(subtotal_string)
            move_lines.append(Command.create({
                'move_id':m.id,
                'is_subtotal': True,
                'sequence': seq,
                'display_type': 'line_section',
                'name': subtotal_string,
            }))
            seq += 1
        rec['move_lines'] = move_lines
        return rec

    """  @api.depends('payment_id')
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
        } """
>>>>>>> Stashed changes
