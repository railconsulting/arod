# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast
import datetime
import io
import json
import logging
import math
import re
import base64
from ast import literal_eval
from collections import defaultdict
from functools import cmp_to_key

import markupsafe
from babel.dates import get_quarter_names
from dateutil.relativedelta import relativedelta

from odoo.addons.web.controllers.utils import clean_action
from odoo import models, fields, api, _, osv, _lt
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import config, date_utils, get_lang, float_compare, float_is_zero
from odoo.tools.float_utils import float_round
from odoo.tools.misc import formatLang, format_date, xlsxwriter
from odoo.tools.safe_eval import expr_eval, safe_eval
from odoo.models import check_method_name

_logger = logging.getLogger(__name__)

ACCOUNT_CODES_ENGINE_SPLIT_REGEX = re.compile(r"(?=[+-])")

ACCOUNT_CODES_ENGINE_TERM_REGEX = re.compile(
    r"^(?P<sign>[+-]?)"\
    r"(?P<prefix>([A-Za-z\d.]*|tag\([\w.]+\))((?=\\)|(?<=[^CD])))"\
    r"(\\\((?P<excluded_prefixes>([A-Za-z\d.]+,)*[A-Za-z\d.]*)\))?"\
    r"(?P<balance_character>[DC]?)$"
)

ACCOUNT_CODES_ENGINE_TAG_ID_PREFIX_REGEX = re.compile(r"tag\(((?P<id>\d+)|(?P<ref>\w+\.\w+))\)")

# Performance optimisation: those engines always will receive None as their next_groupby, allowing more efficient batching.
NO_NEXT_GROUPBY_ENGINES = {'tax_tags', 'account_codes'}

LINE_ID_HIERARCHY_DELIMITER = '|'



class AccountReport(models.Model):
    _inherit = 'account.report'

     
    def _init_options_partner(self, options, previous_options=None):
        
        if self.env.ref('account_reports.aged_receivable_report').id  == options['report_id'] or  self.env.ref('account_reports.aged_payable_report').id  == options['report_id']:
            options['res_currency'] = (previous_options or {}).get('currency_filter', self.env['res.currency'].search([]).ids) 
            options['account_account'] = (previous_options or {}).get('account_filter', []) 
            options['new_filters'] = True
        return super()._init_options_partner(options, previous_options=None)
        
    def _get_options_domain(self, options, date_scope):
        self.ensure_one()
        
        domain = super()._get_options_domain(options, date_scope)
        if self.env.ref('account_reports.aged_receivable_report').id  == options['report_id'] or  self.env.ref('account_reports.aged_payable_report').id  == options['report_id']:
            options['new_filters'] = True
            if  options['res_currency']:
                domain += ['&',('currency_id','in',options['res_currency'] )]
            if  options['account_account']:
                
                domain += ['&',('account_id','in',options['account_account'] )]
        
        return domain