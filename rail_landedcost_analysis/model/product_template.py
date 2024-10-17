from odoo import api, fields, models, tools, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    apply_dai = fields.Boolean(string="Calcular DAI")
    dai = fields.Float(string="% DAI")
