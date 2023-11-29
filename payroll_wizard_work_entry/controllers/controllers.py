# -*- coding: utf-8 -*-
# from odoo import http


# class WizardWorkEntry(http.Controller):
#     @http.route('/wizard_work_entry/wizard_work_entry', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wizard_work_entry/wizard_work_entry/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wizard_work_entry.listing', {
#             'root': '/wizard_work_entry/wizard_work_entry',
#             'objects': http.request.env['wizard_work_entry.wizard_work_entry'].search([]),
#         })

#     @http.route('/wizard_work_entry/wizard_work_entry/objects/<model("wizard_work_entry.wizard_work_entry"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wizard_work_entry.object', {
#             'object': obj
#         })
