# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    move_id = fields.Many2one('account.move', 'Asiento contable', readonly=True, copy=False)

    def action_draft(self):
        if self.move_id:
            self.move_id.filtered(lambda x: x.state == 'posted').button_cancel()
            self.move_id.unlink()
        return super(HrPayslipRun, self).action_draft()

    def action_validate(self):
        res = super(HrPayslipRun, self).action_validate()
        for r in self:
            if r.company_id.entry_type == 'batch':
                lines = []
                debit_lines_dict = {}
                credit_lines_dict = {}
                date = r.date_end
                journal = r.journal_id.id
                currency = r.company_id.currency_id
                name = _('Nomina: %s') % (r.name)
                #type = dict(r.fields_get(["type"],['selection'])['type']["selection"]).get(r.type)
                ref = r.name
                move_dict = {
                    'narration': name,
                    'ref': ref,
                    'journal_id': journal,
                    'date': date,
                }
                dptos = []
                for l in self.slip_ids:
                    dptos.append(l.employee_id.department_id.id)
                dpt = self.env['hr.department'].search([('company_id','=',r.company_id.id),('id','in',dptos)])
                for d in dpt:
                    lines.append((0,0,{
                        'display_type': 'section',
                        'name': d.display_name,
                    }))
                    for dpt_account_ids in d.account_ids:
                        credit_account_id = dpt_account_ids.credit_account_id.id
                        debit_account_id = dpt_account_ids.debit_account_id.id
                        if not credit_account_id or not debit_account_id:
                            raise UserError(_('Credit/Debit account "%s" has not properly configured for: ') % (dpt_account_ids.rule_id.name))
                        for slip in r.slip_ids:
                            lines = slip.line_ids.filtered(lambda x: 
                                x.salary_rule_id.id == dpt_account_ids.rule_id.id and
                                dpt_account_ids.display_type == False and
                                x.total > 0 
                            )
                        if credit_account_id in credit_lines_dict:
                            credit_lines_dict[credit_account_id]['credit'] += currency.round(sum(lines.mapped('total')))
                            credit_lines_dict[credit_account_id]['debit'] += currency.round(sum(lines.mapped('total')))
                        else:
                            credit_line_vals = {
                                'account_id': credit_account_id,
                                'name': ref + ": " + dpt_account_ids.rule_id.name,
                                'credit': currency.round(sum(lines.mapped('total'))),
                                'debit': currency.round(sum(lines.mapped('total'))),
                            }
                        credit_lines_dict[credit_account_id] = credit_line_vals

                        if debit_account_id in debit_lines_dict:
                            debit_lines_dict[debit_account_id]['credit'] += currency.round(sum(lines.mapped('total')))
                            debit_lines_dict[debit_account_id]['debit'] += currency.round(sum(lines.mapped('total')))
                        else:
                            debit_line_vals = {
                                'account_id': debit_account_id,
                                'name': ref + ": " + dpt_account_ids.rule_id.name,
                                'credit': currency.round(sum(lines.mapped('total'))),
                                'debit': currency.round(sum(lines.mapped('total'))),
                            }
                        debit_lines_dict[debit_account_id] = debit_line_vals
                    
                    for account_id, values in credit_lines_dict.items():
                        credit_line = (0, 0, {
                            'account_id': int(account_id),
                            'name': values['name'],
                            'debit': 0,
                            'credit': values['credit'],
                        })
                        lines.append(credit_line)
                    for account_id, values in debit_lines_dict.items():
                        debit_line = (0, 0, {
                            'account_id': int(account_id),
                            'name': values['name'],
                            'debit': values['debit'],
                            'credit': 0,
                        })
                        lines.append(debit_line)
                    

                move_dict['line_ids'] = lines
                move = self.env['account.move'].create(move_dict)
                r.write({'move_id': move.id})
                move.post()


        return res
