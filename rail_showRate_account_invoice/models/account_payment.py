# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    currency_rate_amount = fields.Float(
        string="Currency exchange rate", compute="_compute_currency_rate_amount", digits=0,
    )

    def get_rates(self, currency, company, date):
        self.env['res.currency.rate'].flush_model(['rate', 'currency_id', 'company_id', 'name'])
        query = """SELECT c.id,
                          COALESCE((SELECT r.rate FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name = %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) AS rate
                   FROM res_currency c
                   WHERE c.id IN (%s)"""
        try:
            self._cr.execute(query, (date, company.id, currency.id))
            currency_rates = dict(self._cr.fetchall())
        except:
            currency_rates = dict(id=1,rate=1.0)
        return currency_rates
        
    @api.depends(
        "date",
        "company_id",
        "currency_id"
    )
    def _compute_currency_rate_amount(self):
        currencyRate=0
        try:
            for item in self:
                if item.currency_id != item.company_id.currency_id:
                    rates = self.get_rates(item.currency_id, item.company_id, item.date)
                    currencyRate = rates.get(item.currency_id.id)
                    if currencyRate == 1.0:
                        item.currency_rate_amount = -1
                        raise ValidationError(_('Currency rate not found for date ') + str(item.date))
                    else:
                        item.currency_rate_amount = 1/currencyRate
                else:
                    item.currency_rate_amount = 1
        except:
            item.currency_rate_amount = 1