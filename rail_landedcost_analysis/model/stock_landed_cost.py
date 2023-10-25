# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError,UserError
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)

class StockLandCost(models.Model):
    _inherit = "stock.landed.cost"


    type = fields.Selection(string="Tipo", 
                            selection=[
                                ('ca','Importacion C.A.'),
                                ('rm','Importacion R.M.')
                                ])
    no_doc = fields.Char("No. Poliza")
    sat_value = fields.Float("Valor", help="Valor de la importacion en la moneda de origen")
    insurance = fields.Float("Seguro", help="El monto establecido aqui es unicamente para efectos del calculo de DAI")
    shipment = fields.Float("Total transporte", help="El monto establecido aqui es unicamente para efectos del calculo del IVA")
    expenses_dai = fields.Float("Total gastos afectos", compute='_compute_expenses_dai', store=True, help="Gastos de destino afectos al calculo del DAI")
    amount_sat_total = fields.Float("Valor en aduana", compute='_compute_sat_total', store=True, help="Valor + Seguro + Transporte")
    amount_sat_total_currency = fields.Float("Total GTQ", compute='_compute_sat_total', store=True, help="Valor aduana * Tasa de cambio")
    currency_sat_id = fields.Many2one('res.currency', string="Moneda", help="Este tipo de cambio solo es para efectos de calculo del IVA")
    currency_rate = fields.Float("Tipo de cambio", help="Este valor es unicamente para efectos del calculo del IVA")
    dai = fields.Float(compute="_compute_dai_amount", store=True, help="Total DAI calculado en el tab DAI")
    iva = fields.Float("Total IVA", compute='_compute_iva_amount', store=True, help="(Total GTQ + DAI) * Porcentaje IVA")
    exclude_tax_reports = fields.Boolean('Excluir libro Compras')

    dai_lines = fields.One2many('stock.landed.cost.dai', 'landed_cost_id')
    picking_id = fields.Many2one('stock.picking', 
        domain=[('picking_type_code','=','incoming')], readonly=1)
    dest_location_id = fields.Many2one('stock.location', domain=[('usage','=','internal')])

    @api.onchange('date','currency_sat_id')
    def _onchange_currency_rate(self):
        if self.date and not self.exclude_tax_reports:
            for rec in self:
                rate = self.env['res.currency.rate'].search([('name', '<=', rec.date),('currency_id.id', '=', rec.currency_sat_id.id)], order='name desc', limit=1)
                if rate:
                    rec.write({
                        'currency_rate': rate.rate
                    })

    @api.depends('sat_value','insurance','shipment','currency_rate')
    def _compute_sat_total(self):
        total = 0
        total_currency = 0
        for r in self:
            total = r.sat_value + r.insurance + r.shipment
            total_currency = total * r.currency_rate
            r.update({
                'amount_sat_total': total,
                'amount_sat_total_currency': total_currency,
            })


    @api.depends('cost_lines','cost_lines.to_dai')
    def _compute_expenses_dai(self):
        amount = 0
        for r in self:
            for l in r.cost_lines:
                if l.to_dai:
                    amount += l.price_unit
            r.expenses_dai = amount
    
    @api.depends('amount_sat_total', 'insurance', 'expenses_dai', 'dai')
    def _compute_iva_amount(self):
        iva = 0
        for r in self:
            iva = (r.amount_sat_total_currency + r.insurance + r.shipment + r.dai) * (12/100)
        r.iva = iva

    @api.depends('dai_lines.product_id', 'dai_lines.dai_amount',
        'dai_lines.qty', 'dai_lines.former_cost')
    def _compute_dai_amount(self):
        total = 0
        for rec in self:
            for l in rec.dai_lines:
                total += l.dai_amount
            rec.dai = total

    def _get_picking_records(self):
        stock_ids = self.search([]).mapped('picking_ids').ids
        stock_picking_ids = self.env['stock.picking'].search([('id', 'not in', stock_ids)]).ids
        return [('id','in', stock_picking_ids )]

    @api.depends('company_id')
    def _compute_allowed_picking_ids(self):
        res = super(StockLandCost, self)._compute_allowed_picking_ids()
        stock_ids = self.search([]).mapped('picking_ids').ids
        pickings = []
        for cost in self:
            pickings.extend(
                [s_id for s_id in cost.allowed_picking_ids.ids if s_id not in stock_ids])
        cost.allowed_picking_ids = pickings if pickings else False

        return res


    def button_get_dai_amount_lines(self):
        dai_parameter = self.env['ir.config_parameter'].sudo().get_param('custom_landed_cost.landed_cost_product_id')
        if not dai_parameter:
            raise ValidationError(_("No hay configurado ningun producto para el DAI, por favor ve a los ajustes de inventario y asignalo."))
        else:
            dai_product_id = self.env['product.product'].search([('id','=',dai_parameter)])
        self.ensure_one()
        lines = []
        dai_amount, dai, splited_expense = 0, 0, 0
        amount_ids = self.dai_lines.mapped('move_line_id')
        cost_lines_obj = self.env['stock.landed.cost.lines']
        
        total_dai = 0
        dai_obj = self.env['stock.landed.cost.dai']
        dai_list = []
        total_expenses = self.expenses_dai
        total_insurance = self.insurance
        total_former_cost = 0
        for m in self._get_targeted_move_ids():
            if m.id not in amount_ids.ids and m.product_id.apply_dai:
                total_former_cost += sum(m.stock_valuation_layer_ids.mapped('value'))
        for move in self._get_targeted_move_ids():
            if move.id not in amount_ids.ids and move.product_id.apply_dai:
                if move.product_id.cost_method not in ('fifo', 'average') or move.state == 'cancel':
                    raise ValidationError("Hay productos que no tienen metodo de costeo FIFO o AVCO por favor revisa la configuracion de los productos")
                
                if move.product_id.apply_dai and move.product_id.dai and move.product_id.product_tmpl_id.supplier_taxes_id:
                    #subtotal = move.price_unit * move.product_qty
                    taxes = move.product_id.product_tmpl_id.supplier_taxes_id
                    tax_amount = 0
                    splited_expense = (sum(move.stock_valuation_layer_ids.mapped('value')) / total_former_cost) * total_expenses
                    splited_insurance = (sum(move.stock_valuation_layer_ids.mapped('value')) / total_former_cost) * total_insurance
                    for t in taxes:
                        tax_amount += t.amount
                    dai_amount =  (sum(move.stock_valuation_layer_ids.mapped('value')) + splited_expense + splited_insurance ) * (move.product_id.dai / 100)
                taxes = [tax.id for tax in dai_product_id.product_tmpl_id.supplier_taxes_id]
                vals = {
                    'landed_cost_id' : self.id,
                    'product_id': move.product_id.id,
                    'expenses': splited_expense,
                    'insurance': splited_insurance,
                    'dai_percentage': move.product_id.dai,
                    'tax_ids' : [(6,0,taxes)],
                    'move_line_id': move.id,
                    'former_cost' : sum(move.stock_valuation_layer_ids.mapped('value')),
                    'qty' : move.product_qty,
                    'price_unit' : move.price_unit,
                    'dai_amount' : dai_amount
                }
                total_dai += dai_amount
                line = dai_obj.create(vals)
                dai_list.append(line)
        dai_line = self.cost_lines.filtered(lambda x: x.product_id.name == 'DAI')
        if total_dai == 0 and self.dai_lines:
            for dl in self.dai_lines:
                total_dai += dl.dai_amount
        if not dai_line and total_dai > 0:
            cost_line = cost_lines_obj.create({
                'account_id': dai_product_id.property_account_expense_id.id,
                'cost_id': self.id,
                'name': 'DAI',
                'price_unit': total_dai,
                'product_id': dai_product_id.id,
                'split_method': 'dai',
            })
            """ dai_lines = dai_obj.search([('id','in', dai_list)])
            for d in dai_lines:
                d.update({
                    'cost_line_id': cost_line,
                }) """


    def _check_sum(self):
        """Inherit to add condition to compute only cost_line_id in valuation_adjustment_lines"""

        """ Check if each cost line its valuation lines sum to the correct amount
        and if the overall total amount is correct also """
        prec_digits = self.env.company.currency_id.decimal_places
        for landed_cost in self:
            total_amount = 0.0
            for v_line in landed_cost.valuation_adjustment_lines:
                if v_line.cost_line_id and v_line.cost_line_id.id:
                    total_amount += v_line.additional_landed_cost
            if not tools.float_is_zero(total_amount - landed_cost.amount_total, precision_digits=prec_digits):
                return False

            val_to_cost_lines = defaultdict(lambda: 0.0)
            for val_line in landed_cost.valuation_adjustment_lines:
                if val_line.cost_line_id and val_line.cost_line_id.id:
                    val_to_cost_lines[val_line.cost_line_id] += val_line.additional_landed_cost
            if any(not tools.float_is_zero(cost_line.price_unit - val_amount, precision_digits=prec_digits)
                   for cost_line, val_amount in val_to_cost_lines.items()):
                return False
        return True

    def compute_landed_cost(self):
        #override for dai proposes
        #compute dai lines if empty and click compute button
        if not self.dai_lines:
            self.button_get_dai_amount_lines()
        AdjustementLines = self.env['stock.valuation.adjustment.lines']
        AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

        towrite_dict = {}
        for cost in self.filtered(lambda cost: cost._get_targeted_move_ids()):
            rounding = cost.currency_id.rounding
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            all_val_line_values = cost.get_valuation_lines()
            for val_line_values in all_val_line_values:
                for cost_line in cost.cost_lines:
                    val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                    self.env['stock.valuation.adjustment.lines'].create(val_line_values)
                total_qty += val_line_values.get('quantity', 0.0)
                total_weight += val_line_values.get('weight', 0.0)
                total_volume += val_line_values.get('volume', 0.0)

                former_cost = val_line_values.get('former_cost', 0.0)
                # round this because former_cost on the valuation lines is also rounded
                total_cost += cost.currency_id.round(former_cost)

                total_line += 1

            for line in cost.cost_lines:
                value_split = 0.0
                for valuation in cost.valuation_adjustment_lines:
                    value = 0.0
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and total_qty:
                            per_unit = (line.price_unit / total_qty)
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and total_weight:
                            per_unit = (line.price_unit / total_weight)
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and total_volume:
                            per_unit = (line.price_unit / total_volume)
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price' and total_cost:
                            per_unit = (line.price_unit / total_cost)
                            value = valuation.former_cost * per_unit
                        elif line.split_method == 'dai' and total_cost:
                            dai_line = self.dai_lines.filtered(lambda x: x.product_id.id == valuation.product_id.id)
                            if dai_line:
                                value = dai_line.dai_amount  
                            else:
                                value = 0.00             
                        else:
                            value = (line.price_unit / total_line)

                        if rounding:
                            value = tools.float_round(value, precision_rounding=rounding, rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value
        for key, value in towrite_dict.items():
            AdjustementLines.browse(key).write({'additional_landed_cost': value})
        return True

    def create_internal_transfer(self):
        if not self.picking_ids:
            raise UserError(_('No hay ninguna transferencia seleccionada...!'))
        operation_type = self.env['ir.config_parameter'].sudo().get_param('custom_landed_cost.picking_type_id')
        if not operation_type:
            raise UserError(_('Por favor configura un tipo de operacion en los ajustes de inventario'))
        source_location_id = self.env['stock.picking.type'].search([
            ('id','=',int(operation_type))]).default_location_src_id
        # source_location_id = self.env.ref('custom_landed_cost.warehouse_custom')
        location_id = self.env['stock.location'].search([
            ('usage','=','internal')])
        if not self.dest_location_id:
            raise UserError(_('Por favor selecciona una ubicacion destino para el traslado interno'))
        if not location_id:
            raise UserError(_('No hay ninguna ubicacion interna creada'))
        

        picking_id = self.env['stock.picking'].create({
            'name': '/',
            'date': fields.datetime.now(), 
            'company_id': self.company_id.id,
            'picking_type_id':  int(operation_type),
            'location_id': source_location_id.id,
            'location_dest_id': self.dest_location_id.id,
            'move_type': 'direct',
            'origin': self.name,
        })
        _logger.critical(picking_id)

        self.picking_id = picking_id.id
        for line in self._get_targeted_move_ids():
            vals = {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'date': picking_id.date,
                    'picking_id': picking_id.id,
                    'picking_type_id': picking_id.picking_type_id.id,
                    'state': 'draft',
                    'name': line.name,
                    'location_id': source_location_id.id,
                    'location_dest_id': self.dest_location_id.id,
                    #'quantity_done': line.product_uom_qty,
                }
            self.env['stock.move'].create(vals)

class StockLandCostLines(models.Model):
    _inherit = "stock.landed.cost.lines"

    to_dai = fields.Boolean(string="Aplicar a DAI")
    bill_id = fields.Many2one('account.move', string="Vendor Bill", domain=[('move_type', '=', 'in_invoice')])
    split_method = fields.Selection(selection_add=[('dai', 'DAI')], ondelete={'dai': 'cascade'})

class StockValuationAdjustmentLines(models.Model):
    _inherit = "stock.valuation.adjustment.lines"

    amount_dai = fields.Float(string="Dai Amount")

class StockDaiAmount(models.Model):
    _name = "stock.landed.cost.dai"
    _description = "Stock Dai Amount"

    move_line_id = fields.Many2one('stock.move')
    product_id = fields.Many2one('product.product')
    dai_percentage = fields.Float("% Dai")
    expenses = fields.Float("Gastos afectos")
    insurance = fields.Float("Seguro")
    dai_amount = fields.Float("Dai Amount")
    landed_cost_id = fields.Many2one('stock.landed.cost')
    cost_line_id = fields.Many2one('stock.landed.cost.lines')
    qty = fields.Float("Quantity")
    former_cost = fields.Float()
    tax_ids = fields.Many2many('account.tax')
    subtotal_amount = fields.Float(compute="_compute_price_subtotal")
    price_unit = fields.Float()

    @api.depends('price_unit', 'product_id', 'qty')
    def _compute_price_subtotal(self):
        for line in self:
            line.subtotal_amount = line.price_unit*line.qty
