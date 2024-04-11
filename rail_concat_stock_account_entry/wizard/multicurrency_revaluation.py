
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from dateutil.relativedelta import relativedelta

from odoo import models, api, fields, _, Command
from odoo.tools import format_date
from odoo.exceptions import UserError

class MulticurrencyRevaluationWizard(models.TransientModel):
    _inherit = 'account.multicurrency.revaluation.wizard'

    @api.model
    def _get_move_vals(self):
        def _get_model_id(parsed_line, selected_model):
            for dummy, parsed_res_model, parsed_res_id in parsed_line:
                if parsed_res_model == selected_model:
                    return parsed_res_id

        def _get_adjustment_balance(line):
            for column in line.get('columns'):
                if column.get('expression_label') == 'adjustment':
                    return column.get('no_format')

        report = self.env.ref('account_reports.multicurrency_revaluation_report')
        included_line_id = report.line_ids.filtered(lambda l: l.code == 'multicurrency_included').id
        generic_included_line_id = report._get_generic_line_id('account.report.line', included_line_id)
        options = {**self._context['multicurrency_revaluation_report_options'], 'unfold_all': False}
        report_lines = report._get_lines(options)
        move_lines = []

        for report_line in report._get_unfolded_lines(report_lines, generic_included_line_id):
            parsed_line_id = report._parse_line_id(report_line.get('id'))
            balance = _get_adjustment_balance(report_line)
            # parsed_line_id[-1][-2] corresponds to res_model of the current line
            if (
                parsed_line_id[-1][-2] == 'account.account'
                and not self.env.company.currency_id.is_zero(balance)
            ):
                account_id = _get_model_id(parsed_line_id, 'account.account')
                currency_id = _get_model_id(parsed_line_id, 'res.currency')
                move_lines.append(Command.create({
                    'name': _(
                        "Provision para %(for_cur)s (1 %(for_cur)s = %(rate)s %(comp_cur)s)",
                        for_cur=self.env['res.currency'].browse(currency_id).display_name,
                        comp_cur=self.env.company.currency_id.display_name,
                        rate=options['currency_rates'][str(currency_id)]['inverse_rate']
                    ),
                    'debit': balance if balance > 0 else 0,
                    'credit': -balance if balance < 0 else 0,
                    'amount_currency': 0,
                    'currency_id': currency_id,
                    'account_id': account_id,
                }))
                if balance < 0:
                    move_line_name = _("Provision de gasto para %s", self.env['res.currency'].browse(currency_id).display_name)
                else:
                    move_line_name = _("Provision de ingreso para %s", self.env['res.currency'].browse(currency_id).display_name)
                move_lines.append(Command.create({
                    'name': move_line_name,
                    'debit': -balance if balance < 0 else 0,
                    'credit': balance if balance > 0 else 0,
                    'amount_currency': 0,
                    'currency_id': currency_id,
                    'account_id': self.expense_provision_account_id.id if balance < 0 else self.income_provision_account_id.id,
                }))

        return {
            'ref': _("Asiento de diferencial cambiario para %s", format_date(self.env, self.date)),
            'journal_id': self.journal_id.id,
            'date': self.date,
            'line_ids': move_lines,
        }