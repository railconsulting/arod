# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError

from itertools import chain
import logging

_logger = logging.getLogger(__name__)

class MulticurrencyRevaluationReportCustomHandler(models.AbstractModel):
    _inherit = 'account.multicurrency.revaluation.report.handler'

    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        active_currencies = self.env['res.currency'].search([('active', '=', True)])
        if len(active_currencies) < 2:
            raise UserError(_("You need to activate more than one currency to access this report."))
        rates = active_currencies._get_rates(self.env.company, options.get('date').get('date_to'))
        # Normalize the rates to the company's currency
        company_rate = rates[self.env.company.currency_id.id]
        for key in rates.keys():
            rates[key] /= company_rate

        
        options['currency_rates'] = {
            str(currency_id.id): {
                'currency_id': currency_id.id,
                'currency_name': currency_id.name,
                'currency_main': self.env.company.currency_id.name,
                'rate': (rates[currency_id.id]
                         if not (previous_options or {}).get('currency_rates', {}).get(str(currency_id.id), {}).get('rate') else
                         float(previous_options['currency_rates'][str(currency_id.id)]['rate'])),
                'inverse_rate': 1 / (rates[currency_id.id]
                         if not (previous_options or {}).get('currency_rates', {}).get(str(currency_id.id), {}).get('inverse_rate') else
                         float(previous_options['currency_rates'][str(currency_id.id)]['inverse_rate'])),
            } for currency_id in active_currencies
        }

        options['company_currency'] = options['currency_rates'].pop(str(self.env.company.currency_id.id))

        options['custom_rate'] = any(
            not float_is_zero(cr['rate'] - rates[cr['currency_id']], 6)
            for cr in options['currency_rates'].values()
        )

        options['warning_multicompany'] = len(self.env.companies) > 1
        #options['buttons'].append({'name': _('Adjustment Entry'), 'sequence': 30, 'action': 'action_multi_currency_revaluation_open_revaluation_wizard'})

    def _custom_line_postprocessor(self, report, options, lines):
        line_to_adjust_id = self.env.ref('account_reports.multicurrency_revaluation_to_adjust').id
        line_excluded_id = self.env.ref('account_reports.multicurrency_revaluation_excluded').id

        rslt = []
        for index, line in enumerate(lines):
            res_model_name, res_id = report._get_model_info_from_id(line['id'])

            if res_model_name == 'account.report.line' and (
                   (res_id == line_to_adjust_id and report._get_model_info_from_id(lines[index + 1]['id']) == ('account.report.line', line_excluded_id)) or
                   (res_id == line_excluded_id and index == len(lines) - 1)
            ):
                # 'To Adjust' and 'Excluded' lines need to be hidden if they have no child
                continue
            elif res_model_name == 'res.currency':
                # Include the rate in the currency_id group lines
                line['name'] = '{for_cur} (1 {for_cur} = {inverse_rate:.6} {comp_cur})'.format(
                    for_cur=line['name'],
                    comp_cur=self.env.company.currency_id.display_name,
                    rate=float(options['currency_rates'][str(res_id)]['rate']),
                    inverse_rate = float(options['currency_rates'][str(res_id)]['inverse_rate']),
                )

            rslt.append(line)

        return rslt