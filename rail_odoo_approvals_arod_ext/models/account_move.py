# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError
import werkzeug.urls

class AccountMove(models.Model):
    _inherit = 'account.move'

    approval_state = fields.Selection(string="Aprobacion", selection=[
        ('to_approve','Por aprobar'),
        ('approved','Aprobado'),
        ('rejected','Rechazado')], default='to_approve')

    def _get_obj_url(self, obj):
        base = 'web#'
        fragment = {
            'view_type': 'form',
            'model': obj._name,
            'id': obj.id
        }
        url = base + werkzeug.urls.url_encode(fragment)
        return "%s/%s" % (
            self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            url
        )

    def request_aproval(self):
        '''
        1. create request
        2. Submit request
        3. update x_has_request_approval = True
        4. open request form view
        '''
        #self.ensure_one()
        ctx = self._context
        model_name = ctx.get('active_model')
        active_ids = self.env.context.get('active_ids')
        bills = self.env['account.move'].search([('id','in',active_ids)])
        for r in bills:
            res_id = r.id
            types = self.env['multi.approval.type']._get_types(model_name)
            approval_type = self.env['multi.approval.type'].filter_type(
                types, model_name, res_id)
            
            record = r
            record_name = record.display_name or _('this object')
            title = _('Request approval for {}').format(record_name)
            record_url = self._get_obj_url(record)
            account_analytic_obj = self.env['account.analytic.account']
            analytic_str = ""
            try:
                for l in record.order_line:
                    analytic_list = list(l.analytic_distribution)
                    for a in analytic_list:
                        analytic_id = account_analytic_obj.search([('id','=', a)])
                        analytic_str += analytic_id.name + ","
            except:
                pass
            
            if approval_type.request_tmpl:
                request_tmpl= werkzeug.urls.url_unquote(_(approval_type.request_tmpl))
                descr = request_tmpl.format(
                    approval = self,
                    record_url=record_url,
                    record_name=record_name,
                    record=record,
                    analytic_str=analytic_str
                )
            else:
                descr = ''

            if record.x_has_request_approval and \
                    not approval_type.is_free_create:
                raise UserError(
                    _('Request has been created before !'))
            # create request
            vals = {
                'name': title,
                'priority': '0',
                'type_id': approval_type.id,
                'description': descr,
                'origin_ref': '{model},{res_id}'.format(
                    model=model_name,
                    res_id=res_id)
            }
            request = self.env['multi.approval'].create(vals)
            request.action_submit()
            #record.update({
            #        'approval_state': 'request'
            #    })


    def action_approve(self):
        for r in self:
            r.update({
                'approval_state': 'approved'
            })

    def action_reject(self):
        for r in self:
            r.update({
                'approval_state': 'rejected'
            })