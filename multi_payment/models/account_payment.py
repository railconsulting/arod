from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class AccountPaymentInvoices(models.Model):
    _name = 'account.payment.invoice'


    invoice_id = fields.Many2one('account.move', string='Invoice')
    payment_id = fields.Many2one('account.payment', string='Payment')
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    origin = fields.Char(related='invoice_id.invoice_origin')
    date_invoice = fields.Date(related='invoice_id.invoice_date')
    date_due = fields.Date(related='invoice_id.invoice_date_due')
    payment_state = fields.Selection(related='payment_id.state', store=True)
    reconcile_amount = fields.Monetary(string='Reconcile Amount')
    amount_total = fields.Monetary(related="invoice_id.amount_total")
    residual = fields.Monetary(related="invoice_id.amount_residual")

    @api.constrains('reconcile_amount')
    def _check_reconcile_amount(self):
        for rec in self:
            if rec.residual < rec.reconcile_amount or rec.reconcile_amount < 0.0:
                raise UserError(_("Ingresa el monto correctamente \n"+ rec.invoice_id.name + "\nSaldo: " + str(rec.residual) + "\nPago: " + str(rec.reconcile_amount))) 



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    batch_reconcile = fields.Boolean(string="Batch reconcile", readonly=True, copy=False, store=True, states={"draft": [("readonly", False)]}, default=False)

    payment_invoice_ids = fields.One2many('account.payment.invoice', 'payment_id', string="Customer Invoices")
    payment_amount_due = fields.Monetary(compute='_payment_amount_due', string='Amount Due')
    applied_amount = fields.Monetary(compute='_payment_amount_due', string='Applied Amount')
    amount = fields.Monetary(currency_field='currency_id', compute='get_amount_payment', store=True, readonly=False)

    @api.onchange('is_internal_transfer')
    def _onchange_internal_transfer_for_batch(self):
        if self.is_internal_transfer == True:
            self.batch_reconcile = False

    @api.depends('payment_invoice_ids.reconcile_amount')
    def get_amount_payment(self):
        for rec in self:
            if rec.batch_reconcile:
                amount = sum(rec.mapped('payment_invoice_ids').mapped('reconcile_amount'))
                rec.amount = amount
            else:
                rec.amount = rec.amount

    def _payment_amount_due(self):
        for rec in self:
            if rec.batch_reconcile:
                rec.payment_amount_due = sum(rec.mapped('payment_invoice_ids').mapped('residual'))
                rec.applied_amount = rec.amount - sum(rec.mapped('payment_invoice_ids').mapped('reconcile_amount'))

    def refresh_invoice(self):
        if self.batch_reconcile:
            self.payment_invoice_ids = [(6, 0, [])]
            if self.payment_type == 'inbound' and self.partner_type == 'customer':
                invoice_type = 'out_invoice'
            elif self.payment_type == 'outbound' and self.partner_type == 'customer':
                invoice_type = 'out_refund'
            elif self.payment_type == 'outbound' and self.partner_type == 'supplier':
                invoice_type = 'in_invoice'
            else:
                invoice_type = 'in_refund'
            invoice_recs = self.env['account.move'].search([
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'posted'),
                ('move_type', '=', invoice_type),
                ('payment_state', '!=', 'paid'),
                ('amount_residual', '!=', 0),
                ('amount_total', '!=', 0),
                ('currency_id', '=', self.currency_id.id)])
            payment_invoice_values = []
            for invoice_rec in invoice_recs:
                payment_invoice_values.append([0, 0, {'invoice_id': invoice_rec.id}])
            self.payment_invoice_ids = payment_invoice_values

    @api.onchange('payment_type', 'partner_type', 'partner_id', 'currency_id')
    def _onchange_to_get_vendor_invoices(self):
        if self.payment_type in ['inbound', 'outbound'] and self.partner_type and self.partner_id and self.currency_id and self.batch_reconcile:
            self.payment_invoice_ids = [(6, 0, [])]
            if self.payment_type == 'inbound' and self.partner_type == 'customer':
                invoice_type = 'out_invoice'
            elif self.payment_type == 'outbound' and self.partner_type == 'customer':
                invoice_type = 'out_refund'
            elif self.payment_type == 'outbound' and self.partner_type == 'supplier':
                invoice_type = 'in_invoice'
            else:
                invoice_type = 'in_refund'
            invoice_recs = self.env['account.move'].search([
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'posted'),
                ('move_type', '=', invoice_type),
                ('payment_state', '!=', 'paid'),
                ('amount_residual', '!=', 0),
                ('amount_total', '!=', 0),
                ('currency_id', '=', self.currency_id.id)])
            payment_invoice_values = []
            for invoice_rec in invoice_recs:
                payment_invoice_values.append([0, 0, {'invoice_id': invoice_rec.id}])
            self.payment_invoice_ids = payment_invoice_values

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for payment in self:
            reconcile_amount = sum(payment.mapped('payment_invoice_ids').mapped('reconcile_amount'))
            if payment.batch_reconcile:
                if payment.amount == reconcile_amount:
                    row = 1
                    for line_id in payment.payment_invoice_ids.filtered(lambda x: x.reconcile_amount > 0):
                        if line_id.residual <= line_id.reconcile_amount:
                            self.ensure_one()
                            if payment.payment_type == 'inbound':
                                lines = payment.move_id.line_ids.filtered(lambda line: line.credit > 0)
                                lines += line_id.invoice_id.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                                lines.reconcile()
                            elif payment.payment_type == 'outbound':
                                lines = payment.move_id.line_ids.filtered(lambda line: line.debit > 0)
                                lines += line_id.invoice_id.line_ids.filtered(
                                    lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                                lines.reconcile()
                        else:
                            self.ensure_one()
                            if payment.payment_type == 'inbound':
                                lines = payment.move_id.line_ids.filtered(lambda line: line.credit > 0)
                                lines += line_id.invoice_id.line_ids.filtered(
                                    lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                                _logger.critical("ROW: " + str(row) + " ELSE: " + str(lines))
                                lines.with_context(amount=line_id.reconcile_amount).reconcile()
                                row += 1
                            elif payment.payment_type == 'outbound':
                                lines = payment.move_id.line_ids.filtered(lambda line: line.debit > 0)
                                lines += line_id.invoice_id.line_ids.filtered(
                                    lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                                lines.with_context(amount=line_id.reconcile_amount).reconcile()
                else:
                    raise UserError('El monto total a reconciliar no coincide con el monto del pago')

        return res
