# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from itertools import groupby
from operator import itemgetter
import logging

_logger = logging.getLogger(__name__)

class StockValuationLayers(models.Model):
    _inherit = "stock.valuation.layer"

    def _validate_accounting_entries(self):
        am_vals = []
        for svl in self:
            if not svl.with_company(svl.company_id).product_id.valuation == 'real_time':
                continue
            if svl.currency_id.is_zero(svl.value):
                continue
            move = svl.stock_move_id
            if not move:
                move = svl.stock_valuation_layer_id.stock_move_id
            am_vals += move.with_company(svl.company_id)._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)
        #_logger.critical(str(am_vals))
        if am_vals:
            #----  Making changes to concat entries in a single one
            am_vals.sort(key=itemgetter('partner_id', 'date', 'journal_id'))
            grouped_entries = []
            for key, group in groupby(am_vals, key=itemgetter('partner_id', 'date', 'journal_id')):
                group_dict = dict(zip(['partner_id', 'date', 'journal_id'], key))
                group_dict['line_ids'] = []
                group_dict['invoice_date'] = group_dict.get('date')
                refs_set = set()

                for entry in group:
                    group_dict['line_ids'].extend(entry['line_ids'])
                    ref_prefix, _ = entry['ref'].split(' - ', 1)
                    refs_set.add(ref_prefix)

                group_dict['ref'] = ','.join(refs_set)
                grouped_entries.append(group_dict)
            account_moves = self.env['account.move'].sudo().create(grouped_entries)
            #---- End
            #account_moves = self.env['account.move'].sudo().create(am_vals) NOTE: Commented for concat entries proposes this it's the original line
            account_moves._post()
        for svl in self:
            # Eventually reconcile together the invoice and valuation accounting entries on the stock interim accounts
            if svl.company_id.anglo_saxon_accounting:
                svl.stock_move_id._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=svl.product_id)



class AccountMove(models.Model):
    _inherit = 'account.move'

    picking_id = fields.Many2one('stock.picking', string='Recept')
    stock_move_ids = fields.Many2many('stock.move', string='Stock Moves')