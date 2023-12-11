# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    wc_move_id = fields.Many2one('acount.move')

    def button_mark_done(self):
        res = super(MrpProduction, self).button_mark_done()
        for r in self:
            if not r.wc_move_id:
                lines = []
                total = 0
                for wo in r.workorder_ids:#.filtered(lambda x: not x.time_ids):
                    times = wo.time_ids
                    analytic_dict = {}
                    if wo.workcenter_id and wo.workcenter_id.inventory_account_id and wo.workcenter_id.expense_account_id:
                        pass
                    else:
                        raise UserError("No se han configurado las cuentas contables para el centro de trabajo:\n"
                                        + wo.workcenter_id.name)
                    if wo.workcenter_id.costs_hour_account_id:
                        analytic_dict.update({
                            str(wo.workcenter_id.costs_hour_account_id.id): 100,
                        })
                    if times:
                        for t in times:
                            if not t.user_id.employee_id:
                                raise ValidationError("No se encuentra un empleado vinculado al usuario de: \n"
                                                      + t.user_id.name + "\n"
                                                      "Por favor vincula un empleado")

                            debit = (0,0,{
                                'account_id' : t.user_id.employee_id.inventory_account_id.id or wo.workcenter_id.inventory_account_id.id,
                                'name': wo.workcenter_id.name +' / '+ t.user_id.name + ': ' + wo.product_id.name,
                                'product_id': wo.product_id.id,
                                'analytic_distribution': analytic_dict,
                                'debit': round(wo.workcenter_id.employee_costs_hour * (t.duration / 60),2),
                                'credit': 0
                            })
                            credit = (0,0,{
                                'account_id' : t.user_id.employee_id.expense_account_id.id or wo.workcenter_id.expense_account_id.id,
                                'name': wo.workcenter_id.name +' / '+ t.user_id.name + ': ' + wo.product_id.name,
                                'product_id': wo.product_id.id,
                                'analytic_distribution': analytic_dict,
                                'debit': 0,
                                'credit': round(wo.workcenter_id.employee_costs_hour * (t.duration / 60),2)
                            })
                            lines.append(debit)
                            lines.append(credit)
                            total += round(wo.workcenter_id.employee_costs_hour * (t.duration / 60),2)

                    debit = (0,0,{
                        'account_id' : wo.workcenter_id.inventory_account_id.id,
                        'name': wo.workcenter_id.name + ': ' + wo.product_id.name,
                        'product_id': wo.product_id.id,
                        'analytic_distribution': analytic_dict,
                        'debit': round(wo.workcenter_id.costs_hour * (wo.duration / 60),2),
                        'credit': 0
                    })
                    credit = (0,0,{
                        'account_id' : wo.workcenter_id.expense_account_id.id,
                        'name': wo.workcenter_id.name + ': ' + wo.product_id.name,
                        'product_id': wo.product_id.id,
                        'analytic_distribution': analytic_dict,
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
