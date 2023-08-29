# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime,date
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


class ResUsers(models.Model):
	_inherit = "res.users"

	picking_type_ids = fields.Many2many('stock.picking.type',string="Tipos de operacion permitidos")
	available_location_ids = fields.Many2many('stock.location', string='Ubicaciones permitidas')
	available_warehouse_ids = fields.Many2many('stock.warehouse', string='Almacenes permitidos')

	def write(self, vals):
		if 'available_location_ids' in vals:
			self.env['ir.model.access'].call_cache_clearing_methods()
			self.env['ir.rule'].clear_caches()
   # self.has_group.clear_cache(self)

		if 'picking_type_ids' in vals:
			self.env['ir.model.access'].call_cache_clearing_methods()
			self.env['ir.rule'].clear_caches()
   # self.has_group.clear_cache(self)

		if 'available_warehouse_ids' in vals:
			self.env['ir.model.access'].call_cache_clearing_methods()
			self.env['ir.rule'].clear_caches()
   # self.has_group.clear_cache(self)

		self.env['ir.model.access'].call_cache_clearing_methods()
		self.env['ir.rule'].clear_caches()
  # self.has_group.clear_cache(self)

		return super(ResUsers, self).write(vals)
