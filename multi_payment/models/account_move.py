from odoo import _, api, fields, models
from datetime import date
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class Accountmove(models.Model):
    _inherit = 'account.move'

    def _update_payments_edi_documents(self):
        ''' Update the edi documents linked to the current journal entries. These journal entries must be linked to an
        account.payment of an account.bank.statement.line. This additional method is needed because the payment flow is
        not the same as the invoice one. Indeed, the edi documents must be updated when the reconciliation with some
        invoices is changing.
        '''
        edi_document_vals_list = []
        for payment in self:
            _logger.critical("payment._get_reconciled_invoices().journal_id.edi_format_ids" + str(payment._get_reconciled_invoices().journal_id.edi_format_ids))
            edi_formats = payment._get_reconciled_invoices().journal_id.edi_format_ids + payment.edi_document_ids.edi_format_id
            edi_formats = self.env['account.edi.format'].browse(edi_formats.ids) # Avoid duplicates
            _logger.critical("EDI_FORMATS:" + str(edi_formats))
            for edi_format in edi_formats:
                _logger.critical("EDI_FORMAT:" + str(edi_format.name))
                existing_edi_document = payment.edi_document_ids.filtered(lambda x: x.edi_format_id == edi_format)
                _logger.critical("EXISTING_EDI_DOCUMENT: "+ str(existing_edi_document))
                move_applicability = edi_format._get_move_applicability(payment)
                if move_applicability:
                    if existing_edi_document:
                        existing_edi_document.write({
                            'state': 'to_send',
                            'error': False,
                            'blocking_level': False,
                        })
                    else:
                        edi_document_vals_list.append({
                            'edi_format_id': edi_format.id,
                            'move_id': payment.id,
                            'state': 'to_send',
                        })
                elif existing_edi_document:
                    existing_edi_document.write({
                        'state': False,
                        'error': False,
                        'blocking_level': False,
                    })
        self.env['account.edi.document'].create(edi_document_vals_list)
        self.edi_document_ids._process_documents_no_web_services()

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    invoice_id = fields.Many2one('account.move', string='Invoice')

    def reconcile(self):
        ''' Reconcile the current move lines all together.
        :return: A dictionary representing a summary of what has been done during the reconciliation:
                * partials:             A recorset of all account.partial.reconcile created during the reconciliation.
                * exchange_partials:    A recorset of all account.partial.reconcile created during the reconciliation
                                        with the exchange difference journal entries.
                * full_reconcile:       An account.full.reconcile record created when there is nothing left to reconcile
                                        in the involved lines.
                * tax_cash_basis_moves: An account.move recordset representing the tax cash basis journal entries.
        '''
        results = {'exchange_partials': self.env['account.partial.reconcile']}

        if not self:
            return results

        not_paid_invoices = self.move_id.filtered(lambda move:
            move.is_invoice(include_receipts=True)
            and move.payment_state not in ('paid', 'in_payment')
        )

        # ==== Check the lines can be reconciled together ====
        company = None
        account = None
        for line in self:
            if line.reconciled:
                raise UserError(_("You are trying to reconcile some entries that are already reconciled."))
            if not line.account_id.reconcile and line.account_id.account_type not in ('asset_cash', 'liability_credit_card'):
                raise UserError(_("Account %s does not allow reconciliation. First change the configuration of this account to allow it.")
                                % line.account_id.display_name)
            if line.move_id.state != 'posted':
                raise UserError(_('You can only reconcile posted entries.'))
            if company is None:
                company = line.company_id
            elif line.company_id != company:
                raise UserError(_("Entries doesn't belong to the same company: %s != %s")
                                % (company.display_name, line.company_id.display_name))
            if account is None:
                account = line.account_id
            elif line.account_id != account:
                raise UserError(_("Entries are not from the same account: %s != %s")
                                % (account.display_name, line.account_id.display_name))

        sorted_lines = self.sorted(key=lambda line: (line.date_maturity or line.date, line.currency_id, line.amount_currency))

        # ==== Collect all involved lines through the existing reconciliation ====

        involved_lines = sorted_lines._all_reconciled_lines()
        involved_partials = involved_lines.matched_credit_ids | involved_lines.matched_debit_ids

        # ==== Create partials ====
        # THIS PART IS MODIFIED TO RECONCILE THE PARTIAL AMOUNTS 

        partial_amount = self.env.context.get('amount', False)
        if partial_amount:
            partial_no_exch_diff = bool(self.env['ir.config_parameter'].sudo().get_param('account.disable_partial_exchange_diff'))
            message_list = [{
                'record' + str(line) +'\n' 
                'balance' + str(line.balance) +'\n'
                'amount_currency' + str(line.amount_currency) +'\n'
                'amount_residual' + str(line.amount_residual) +'\n'
                'amount_residual_currency' + str(line.amount_residual_currency) +'\n'
                'company' + str(line.company_id) +'\n'
                'currency' + str(line.currency_id) +'\n'
                'date' + str(line.date) +'\n'
                'reconciled' + str(line.reconciled) +'\n'
            } for line in self ]
            #raise UserError(str(message_list))
            vals_list = []
            for line in self.filtered(lambda x:x.payment_id):
                if line.payment_id.payment_type == 'outbound':
                    amount = partial_amount 
                else:
                    amount = partial_amount * -1
                vals_list.append({
                    'record': line,
                    'balance': amount,
                    'amount_currency': amount,
                    'amount_residual': amount,
                    'amount_residual_currency': amount,
                    'company': line.company_id,
                    'currency': line.currency_id,
                    'date': line.date,
                    'reconciled': line.reconciled,  
                })
            for line in self.filtered(lambda x: not x.payment_id):
                vals_list.append({
                    'record': line,
                    'balance': line.balance,
                    'amount_currency': line.amount_currency,
                    'amount_residual': line.amount_residual,
                    'amount_residual_currency': line.amount_residual_currency,
                    'company': line.company_id,
                    'currency': line.currency_id,
                    'date': line.date,
                    'reconciled': line.reconciled,
                })
            #raise UserError(str(vals_list))
            partials_vals_list, exchange_data = self._prepare_reconciliation_partials(vals_list)
            partials = self.env['account.partial.reconcile'].create(partials_vals_list)
            #raise UserError(str(partials))
            # ==== Create exchange difference moves ====
            for index, exchange_vals in exchange_data.items():
                partials[index].exchange_move_id = self._create_exchange_difference_move(exchange_vals)

            results['partials'] = partials
            involved_partials += partials
            exchange_move_lines = partials.exchange_move_id.line_ids.filtered(lambda line: line.account_id == account)
            involved_lines += exchange_move_lines
            exchange_diff_partials = exchange_move_lines.matched_debit_ids + exchange_move_lines.matched_credit_ids
            involved_partials += exchange_diff_partials
            results['exchange_partials'] += exchange_diff_partials
        else:
            partial_no_exch_diff = bool(self.env['ir.config_parameter'].sudo().get_param('account.disable_partial_exchange_diff'))
            sorted_lines_ctx = sorted_lines.with_context(no_exchange_difference=self._context.get('no_exchange_difference') or partial_no_exch_diff)
            partials = sorted_lines_ctx._create_reconciliation_partials()
            results['partials'] = partials
            involved_partials += partials
            exchange_move_lines = partials.exchange_move_id.line_ids.filtered(lambda line: line.account_id == account)
            involved_lines += exchange_move_lines
            exchange_diff_partials = exchange_move_lines.matched_debit_ids + exchange_move_lines.matched_credit_ids
            involved_partials += exchange_diff_partials
            results['exchange_partials'] += exchange_diff_partials

        # ==== Create entries for cash basis taxes ====

        is_cash_basis_needed = account.company_id.tax_exigibility and account.account_type in ('asset_receivable', 'liability_payable')
        if is_cash_basis_needed and not self._context.get('move_reverse_cancel'):
            tax_cash_basis_moves = partials._create_tax_cash_basis_moves()
            results['tax_cash_basis_moves'] = tax_cash_basis_moves

        # ==== Check if a full reconcile is needed ====

        def is_line_reconciled(line):
            # Check if the journal item passed as parameter is now fully reconciled.
            return line.reconciled \
                   or line.currency_id.is_zero(line.amount_residual_currency) \
                   or line.company_currency_id.is_zero(line.amount_residual)

        if all(is_line_reconciled(line) for line in involved_lines):

            # ==== Create the exchange difference move ====
            # This part could be bypassed using the 'no_exchange_difference' key inside the context. This is useful
            # when importing a full accounting including the reconciliation like Winbooks.

            exchange_move = None
            if not self._context.get('no_exchange_difference'):
                # In normal cases, the exchange differences are already generated by the partial at this point meaning
                # there is no journal item left with a zero amount residual in one currency but not in the other.
                # However, after a migration coming from an older version with an older partial reconciliation or due to
                # some rounding issues (when dealing with different decimal places for example), we could need an extra
                # exchange difference journal entry to handle them.
                exchange_lines_to_fix = self.env['account.move.line']
                amounts_list = []
                exchange_max_date = date.min
                for line in involved_lines:
                    if not line.company_currency_id.is_zero(line.amount_residual):
                        exchange_lines_to_fix += line
                        amounts_list.append({'amount_residual': line.amount_residual})
                    elif not line.currency_id.is_zero(line.amount_residual_currency):
                        exchange_lines_to_fix += line
                        amounts_list.append({'amount_residual_currency': line.amount_residual_currency})
                    exchange_max_date = max(exchange_max_date, line.date)
                exchange_diff_vals = exchange_lines_to_fix._prepare_exchange_difference_move_vals(
                    amounts_list,
                    company=involved_lines[0].company_id,
                    exchange_date=exchange_max_date,
                )

                # Exchange difference for cash basis entries.
                if is_cash_basis_needed:
                    involved_lines._add_exchange_difference_cash_basis_vals(exchange_diff_vals)

                # Create the exchange difference.
                if exchange_diff_vals['move_vals']['line_ids']:
                    exchange_move = involved_lines._create_exchange_difference_move(exchange_diff_vals)
                    if exchange_move:
                        exchange_move_lines = exchange_move.line_ids.filtered(lambda line: line.account_id == account)

                        # Track newly created lines.
                        involved_lines += exchange_move_lines

                        # Track newly created partials.
                        exchange_diff_partials = exchange_move_lines.matched_debit_ids \
                                                 + exchange_move_lines.matched_credit_ids
                        involved_partials += exchange_diff_partials
                        results['exchange_partials'] += exchange_diff_partials

            # ==== Create the full reconcile ====

            results['full_reconcile'] = self.env['account.full.reconcile'].create({
                'exchange_move_id': exchange_move and exchange_move.id,
                'partial_reconcile_ids': [(6, 0, involved_partials.ids)],
                'reconciled_line_ids': [(6, 0, involved_lines.ids)],
            })

        not_paid_invoices.filtered(lambda move:
            move.payment_state in ('paid', 'in_payment')
        )._invoice_paid_hook()

        return results