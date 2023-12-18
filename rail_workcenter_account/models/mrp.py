# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    wc_move_id = fields.Many2one('acount.move')

    def button_mark_done(self):
        res = super(MrpProduction, self).button_mark_done()
        for r in self:
            if not r.wc_move_id:
                lines = []
                total = 0
                inv_lines = {}
                exp_lines = {}

                for wo in r.workorder_ids:
                    times = wo.time_ids
                    if wo.workcenter_id and wo.workcenter_id.inventory_account_id and wo.workcenter_id.expense_account_id:
                        pass
                    else:
                        raise UserError("No se han configurado las cuentas contables para el centro de trabajo:\n"
                                        + wo.workcenter_id.name)
                    if times:
                        for t in times:
                            if t.employee_id:
                                user = t.employee_id
                                inv_account = t.employee_id.inventory_account_id.id
                                exp_account = t.employee_id.employee_id.expense_account_id.id
                            else:
                                user = t.user_id.employee_id
                                inv_account = t.user_id.employee_id.inventory_account_id.id
                                exp_account = t.user_id.employee_id.expense_account_id.id

                            if not inv_account or not exp_account:
                                raise ValidationError("No se encuentra un cuenta contable valida para: "
                                                      + user.name)

                            if inv_account in inv_lines:
                                inv_lines[inv_account]['debit'] += round(wo.workcenter_id.employee_costs_hour * (t.duration / 60), 2)
                                inv_lines[inv_account]['credit'] += round(wo.workcenter_id.employee_costs_hour * (t.duration / 60), 2)
                            else:
                                line_inventory = {
                                'account_id': inv_account,
                                'name': 'TIEMPO DE TRABAJO: ' + wo.workcenter_id.name + ': ' + wo.product_id.name,
                                'product_id': wo.product_id.id,
                                'debit': round(wo.workcenter_id.employee_costs_hour * (t.duration / 60), 2),
                                'credit': round(wo.workcenter_id.employee_costs_hour * (t.duration / 60), 2)
                            }
                            inv_lines[inv_account] = line_inventory

                            if exp_account in exp_lines:
                                exp_lines[exp_account]['debit'] += round(wo.workcenter_id.employee_costs_hour * (t.duration / 60), 2)
                                exp_lines[exp_account]['credit'] += round(wo.workcenter_id.employee_costs_hour * (t.duration / 60), 2)
                            else:
                                line_expense = {
                                'account_id': exp_account,
                                'name': 'TIEMPO DE TRABAJO: ' + wo.workcenter_id.name + ': ' + wo.product_id.name,
                                'product_id': wo.product_id.id,
                                'debit': round(wo.workcenter_id.employee_costs_hour * (t.duration / 60), 2),
                                'credit': round(wo.workcenter_id.employee_costs_hour * (t.duration / 60), 2)
                            }
                            exp_lines[exp_account] = line_expense

                            total += round(wo.workcenter_id.employee_costs_hour * (t.duration / 60),2)

                    for account_id, values in inv_lines.items():
                        debit_line = (0, 0, {
                            'account_id': int(account_id),
                            'name': values['name'],
                            'product_id': values['product_id'],
                            'debit': values['debit'],
                            'credit': 0,
                        })
                        lines.append(debit_line)
                    for account_id, values in exp_lines.items():
                        credit_line = (0, 0, {
                            'account_id': int(account_id),
                            'name': values['name'],
                            'product_id': values['product_id'],
                            'debit': 0,
                            'credit': values['credit'],
                        })
                        lines.append(credit_line)
                    debit = (0,0,{
                        'account_id' : wo.workcenter_id.inventory_account_id.id,
                        'name': wo.workcenter_id.name + ': ' + wo.product_id.name,
                        'product_id': wo.product_id.id,
                        'debit': round(wo.workcenter_id.costs_hour * (wo.duration / 60),2),
                        'credit': 0
                    })
                    credit = (0,0,{
                        'account_id' : wo.workcenter_id.expense_account_id.id,
                        'name': wo.workcenter_id.name + ': ' + wo.product_id.name,
                        'product_id': wo.product_id.id,
                        'debit': 0,
                        'credit': round(wo.workcenter_id.costs_hour * (wo.duration / 60),2)
                    })
                    lines.append(debit)
                    lines.append(credit)
                    total += round(wo.workcenter_id.costs_hour * (wo.duration / 60),2)
                if total > 0:
                    move = self.env['account.move'].create({
                        'move_type': 'entry',
                        'ref': 'CENTROS DE TRABAJO: ' + r.name,
                        'journal_id': r.company_id.wc_journal_id.id,
                        'line_ids': lines,
                    })
                if move.amount_total_signed > 0:
                    move._post()
                else:
                    raise ValidationError("El asiento contable para los centros de trabajo ha sido mal registrado.\n"
                                          +"Por favor revisa la configuracion contable en cada centro de trabajo")
                r.write({
                    'wc_move_id': move.id
                })
        return res
