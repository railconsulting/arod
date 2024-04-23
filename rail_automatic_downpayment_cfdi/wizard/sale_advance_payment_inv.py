# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'


    auto_cfdi_flow = fields.Boolean("Crear y aplicar NC CFDI")
    l10n_mx_edi_origin = fields.Char("CFDI Origen", compute='_get_cfdi_origin')
    origin_move_id = fields.Many2one('account.move',"Factura origen", compute='_get_cfdi_origin')
    nc_date_mode = fields.Selection(selection=[
            ('custom', 'Especifico'),
            ('entry', 'Fecha contable factura')
    ], required=True, default='custom', string="Fecha de reversion")
    nc_date = fields.Date(string='Fecha NC', default=fields.Date.context_today)
    nc_reason = fields.Char(string='Razon NC', default="Cancelacion por facturacion de anticipo")
    nc_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Usar diario especifico',
        compute='_compute_journal_id',
        readonly=False,
        store=True,
        check_company=True,
        help='If empty, uses the journal of the journal entry to be reversed.',
    )

    @api.depends('auto_cfdi_flow')
    def _get_cfdi_origin(self):
        dp_invoices = []
        message=""
        _logger.critical(str(self.sale_order_ids.order_line.filtered('is_downpayment')))
        for l in self.sale_order_ids.order_line.filtered('is_downpayment'):
            
            for i in l.invoice_lines:
                dp_invoices.append(i.move_id)
                message += i.move_id.display_name + "\n"
                cfdi_origin = i.move_id.l10n_mx_edi_cfdi_uuid
                origin_move = i.move_id.id
        dp_invoices = list(set(dp_invoices))
        if len(dp_invoices) > 1:
            raise ValidationError("Solo puedes aplicar flujo automatico a un unico documento.!!!\n"
                                  + "Facturas relacionadas:\n"
                                  + message)
        elif len(dp_invoices) == 1 and cfdi_origin:
            self.l10n_mx_edi_origin = "07|" + cfdi_origin
            self.origin_move_id =  origin_move
        else:
            self.auto_cfdi_flow = False
            self.origin_move_id = False
            self.l10n_mx_edi_origin = ""

    @api.depends('sale_order_ids')
    def _compute_journal_id(self):
        for record in self:
            if record.nc_journal_id:
                record.nc_journal_id = record.nc_journal_id
            else:
                journals = record.sale_order_ids.order_line.invoice_lines.journal_id.filtered(lambda x: x.active)
                record.nc_journal_id = journals[0] if journals else None

    @api.onchange('advance_payment_method','deduct_down_payments')
    def _auto_cfdi_flow_onchange(self):
        if not self.advance_payment_method == 'delivered' or not self.deduct_down_payments:
            self.auto_cfdi_flow = False

    def _prepare_default_reversal(self, move):
        reverse_date = self.nc_date if self.nc_date_mode == 'custom' else move.nc_date
        return {
            'ref': _('Reversion de: %(move_name)s, %(reason)s', move_name=move.name, reason=self.nc_reason)
                   if self.nc_reason
                   else _('Reversion de: %s', move.name),
            'date': reverse_date,
            'invoice_date_due': reverse_date,
            'invoice_date': move.is_invoice(include_receipts=True) and (self.nc_date or move.date) or False,
            'journal_id': self.nc_journal_id.id,
            'invoice_payment_term_id': None,
            'invoice_user_id': move.invoice_user_id.id,
            'auto_post': 'at_date' if reverse_date > fields.Date.context_today(self) else 'no',
        }

    def reverse_moves(self,move_id):
        self.ensure_one()
        moves = move_id
        default_values_list = []
        for move in moves:
            default_values_list.append(self._prepare_default_reversal(move))
        batches = [
            [self.env['account.move'], [], True],   # Moves to be cancelled by the reverses.
            [self.env['account.move'], [], False],  # Others.
        ]
        for move, default_vals in zip(moves, default_values_list):
            is_auto_post = default_vals.get('auto_post') != 'no'
            is_cancel_needed = not is_auto_post #and self.refund_method in ('cancel', 'modify')
            batch_index = 0 if is_cancel_needed else 1
            batches[batch_index][0] |= move
            batches[batch_index][1].append(default_vals)

        # Handle reverse method.
        moves_to_redirect = self.env['account.move']
        for moves, default_values_list, is_cancel_needed in batches:
            new_moves = moves._reverse_moves(default_values_list, cancel=is_cancel_needed)

            moves_to_redirect |= new_moves


    def _create_invoices(self, sale_orders):
        res = super(SaleAdvancePaymentInv, self)._create_invoices(sale_orders)
        if self.auto_cfdi_flow and self.l10n_mx_edi_origin:
            self.ensure_one()
            res.l10n_mx_edi_origin = self.l10n_mx_edi_origin
            self.reverse_moves(self.origin_move_id)
        elif self.auto_cfdi_flow and not self.l10n_mx_edi_origin:
            raise ValidationError("Para ejecuar el flujo automatico debe de existir un valor en el campo CFDI origen")
        
        return res
            