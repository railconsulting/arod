# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import models, fields, api
from psycopg2 import sql


class GeneralLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.general.ledger.report.handler'

    def _get_account_title_line(self, report, options, account, has_lines, eval_dict):
        line_vals = super(GeneralLedgerCustomHandler, self)._get_account_title_line(
            report, options, account, has_lines, eval_dict)
        if options.get('filter_amount_currency'):

            tables, where_clause, where_params = report._query_get(
                options, "normal", domain=[("account_id", "=", account.id)])
            currency_table = self.env['res.currency']._get_query_currency_table(options)
            query = f"""
                SELECT
                    SUM(ROUND(account_move_line.amount_currency * currency_table.rate,currency_table.precision)) AS amount_currency
                FROM {tables}
                LEFT JOIN res_company company_table ON company_table.id = "account_move_line__account_id".company_id
               JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
                WHERE {where_clause}
                AND account_move_line.currency_id != company_table.currency_id
                GROUP BY account_move_line.account_id
            """
            #TODO: check journald where clause if amount_currency is not there            
            self._cr.execute(query, where_params)
            amount_currency_list = []
            for res in self._cr.dictfetchall():
                amount_currency_list.append(res.get("amount_currency"))

            line_vals["cr_amount_currency"] = sum(amount_currency_list)
            rounding = self.env.company.currency_id.decimal_places
            amount_currency = self.env['account.report'].format_value(value=line_vals["cr_amount_currency"], figure_type='monetary', digits=rounding)
            line_vals["cr_amount_currency_formatted"] = amount_currency

            line_vals['columns'][6] = {
                'class': 'number',
                'name': line_vals.get("cr_amount_currency_formatted", " "),
                'no_format': line_vals.get("cr_amount_currency", 0)
            }
        return line_vals

class TrialBalanceCustomHandler(models.AbstractModel):
    _inherit = 'account.trial.balance.report.handler'
    def _custom_options_initializer(self, report, options, previous_options=None):
        """ Modifies the provided options to add a column group for initial balance and end balance, as well as the appropriate columns.
        """

        super()._custom_options_initializer(report, options, previous_options=previous_options)
        if options.get('filter_amount_currency') and len(options.get('column_headers',[])) and len(options['column_headers'][0]):
            options['column_headers'][0][-1]["colspan"] = 3


class AccountReport(models.Model):
    _inherit = 'account.report'

    filter_amount_currency = fields.Boolean(string="Show amount in currency",compute=lambda x: x._compute_report_option_filter('filter_amount_currency', False), readonly=False, store=True,depends=['root_report_id'])


    def _init_options_amount_currency(self, options, previous_options=None):
        if self.filter_amount_currency:
            options['filter_amount_currency'] = (
                previous_options or {}).get('filter_amount_currency', False)

    # def _get_column_headers_render_data(self, options):
    #     if self.filter_amount_currency and options.get('filter_amount_currency'):
    #         options['column_headers'][0].append({'name': 'Amount in Currency'})
    #     result = super(
    #         AccountReport, self)._get_column_headers_render_data(options)
    #     return result
            

    def _get_lines(self, options, all_column_groups_expression_totals=None):
        if options.get('filter_amount_currency'):
            column_copy = options['columns'][-1].copy()
            column_copy['expression_label'] = 'amount_currency'
            column_copy['name'] = 'Amount in currency'
            options['columns'].append(column_copy)

        lines = super(AccountReport, self)._get_lines(options,all_column_groups_expression_totals)
        if lines:
            total_line = lines[-1]
            if total_line and total_line.get("id","").startswith('total'):
                total_line["cr_amount_currency"] = 0
                for line in lines[:-1]:
                    if "cr_amount_currency" not in total_line:
                        total_line["cr_amount_currency"] = line.get("cr_amount_currency",0)
                    else:
                        total_line["cr_amount_currency"] += line.get("cr_amount_currency",0)
                rounding = self.env.company.currency_id.decimal_places
                amount_currency = self.format_value(value=total_line["cr_amount_currency"], figure_type='monetary',
                                                    digits=rounding, blank_if_zero=False)
                total_line['cr_amount_currency_formatted'] = amount_currency

                if len(total_line['columns']) > 6:
                    total_line['columns'][6] = {
                        'class': 'number',
                        'name': total_line.get("cr_amount_currency_formatted", " "),
                        'no_format': total_line.get("cr_amount_currency", 0)
                    }

        return lines

