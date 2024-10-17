# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    account_ids = fields.One2many('hr.department.account','department_id')