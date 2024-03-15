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
            query = f"""
                SELECT
                    SUM(account_move_line.amount_currency) AS amount_currency
                FROM {tables}
                LEFT JOIN res_company company_table ON company_table.id = "account_move_line__account_id".company_id
                WHERE {where_clause}
                AND account_move_line.currency_id != company_table.currency_id
                GROUP BY account_move_line.account_id
            """

            self._cr.execute(query, where_params)
            amount_currency_list = []
            for res in self._cr.dictfetchall():
                amount_currency_list.append(res.get("amount_currency"))

            line_vals["cr_amount_currency"] = sum(amount_currency_list)

        return line_vals


class AccountReport(models.Model):
    _inherit = 'account.report'

    filter_amount_currency = fields.Boolean(string="Show amount in currency",compute=lambda x: x._compute_report_option_filter('filter_amount_currency', False), readonly=False, store=True,depends=['root_report_id'])


    def _init_options_amount_currency(self, options, previous_options=None):
        if self.filter_amount_currency:
            options['filter_amount_currency'] = (
                previous_options or {}).get('filter_amount_currency', False)

    def _get_column_headers_render_data(self, options):
        if self.filter_amount_currency and options.get('filter_amount_currency'):
            options['column_headers'][0].append({'name': 'Amount in Currency'})
        result = super(
            AccountReport, self)._get_column_headers_render_data(options)
        return result

    def _get_lines(self, options, all_column_groups_expression_totals=None):
        lines = super(AccountReport, self)._get_lines(options,all_column_groups_expression_totals)
        if lines:
            total_line = lines[-1]
            if total_line and total_line.get("id","").startswith('total'):
                for line in lines[:-1]:
                    if "cr_amount_currency" not in total_line:
                        total_line["cr_amount_currency"] = line.get("cr_amount_currency",0)
                    else:
                        total_line["cr_amount_currency"] += line.get("cr_amount_currency",0)
        return lines

