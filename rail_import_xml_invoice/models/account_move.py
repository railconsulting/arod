from odoo import models, fields, _, api
import tempfile
import base64
from lxml import objectify, etree
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
import logging

_logger = logging.getLogger(__name__)


class AccountTax(models.Model):
    _inherit = "account.tax"

    is_local_tax = fields.Boolean(string='Impuesto Local', default=False, copy=False)



class AccountMove(models.Model):
    _inherit = "account.move"

    xml_filename = fields.Char(
        string="Nombre XML",
    )

    xml_file = fields.Binary(
        string="XML",
    )

    xml_import_id = fields.Many2one(
        comodel_name="xml.import.invoice",
        string="XML import",
        required=False,
    )

    xml_import_invoice_id = fields.Many2one(
        'xml.import.invoice',
        string='line import',
        copy=False,
    )

    def action_post(self):
        if self.xml_file:
            precision = self.currency_id.decimal_places
            result = self.xml_file
            #data = base64.decodestring(result)
            data = base64.b64decode(result)            
            #namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/3'}
            try:
                fobj = tempfile.NamedTemporaryFile(delete=False)
                fname = fobj.name
                fobj.write(data)
                fobj.close()
                file_xml = open(fname, "r")
                tree = objectify.fromstring(file_xml.read().encode())
                _logger.critical("try")
            except:
                try:
                    recovering_parser = etree.XMLParser(recover=True)
                    tree = None
                    tree = etree.fromstring(data.decode("UTF-8"), parser=recovering_parser)
                except:
                    try:
                        tree = etree.fromstring(data, parser=recovering_parser)
                    except:
                        raise ValidationError("Core Err: No ha funcionado ningun metodo de decodificación...")

            # TODO: check if attachment field is xml type
            # if data_file.mimetype == 'application/xml':
            # 	raise UserError(
            # 		_('File %s is not xml type, please remove from list') % (
            # 			data_file.display_name))
            if tree.findall('{http://www.sat.gob.mx/cfd/4}Complemento'):
                namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}
            else:
                namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/3'}
            tfd = self._get_stamp_data(tree)
            if tfd is None:
                raise UserError(
                    _("No se ha encontrado el UUID en el XML")
                )
                """ if self.partner_id.vat != tree.Emisor.get('Rfc'):
                    raise UserError(
                        _("The provider's RFC (%s) does not match the RFC (%s) of the "
                          "attached xml") % (self.partner_id.vat, tree.Emisor.get('Rfc'))
                    )

                if self.company_id.vat != tree.Receptor.get('Rfc'):
                    raise UserError(
                        _("The company RFC (%s) does not match the RFC (%s) of the attached"
                          " xml") % (self.company_id.vat, tree.Receptor.get('Rfc'))
                    )

                sub_total = float(tree.get('SubTotal')) - (
                    float(tree.get('Descuento')) if tree.get('Descuento') else 0)

                if not float_is_zero(self.amount_untaxed - sub_total,
                                     precision_digits=precision):
                    raise UserError(
                        _("The sub-total amount (%s) of the invoice does not match the "
                          "sub-total amount (%s) of the attached xml") %
                        (str(self.amount_untaxed), sub_total)
                    )

                if not float_is_zero(self.amount_total - float(tree.get('Total')),
                                     precision_digits=precision):
                    raise UserError(
                        _("The total amount (%s) of the invoice does not match the total "
                          "amount (%s) of the attached xml") %
                        (str(self.amount_total), tree.get('Total'))
                    )

                if self.currency_id.name != tree.get('Moneda'):
                    raise UserError(
                        _("The invoice currency (%s) does not match the currency (%s) the "
                          "attached xml") % (self.currency_id.name, tree.get('Moneda'))
                    )
                date = tree.get('Fecha')[:10]
                if str(self.invoice_date) != date:
                    raise UserError(
                        _("The invoice date (%s) does not match the date of the XML "
                          "attachment (%s)") % (str(self.invoice_date), date,)
                    ) """
            else:
                if self.partner_id.vat != tree.xpath('cfdi:Emisor', namespaces=namespaces)[0].get('Rfc'):
                    raise UserError(
                        _("The provider's RFC (%s) does not match the RFC (%s) of the "
                          "attached xml") % (self.partner_id.vat, tree.xpath('cfdi:Emisor', namespaces=namespaces)[0].get('Rfc'))
                    )

                if self.company_id.vat != tree.xpath('cfdi:Receptor', namespaces=namespaces)[0].get('Rfc'):
                    raise UserError(
                        _("The company RFC (%s) does not match the RFC (%s) of the attached"
                          " xml") % (self.company_id.vat, tree.xpath('cfdi:Receptor', namespaces=namespaces)[0].get('Rfc'))
                    )

                sub_total = float(tree.get('SubTotal')) - (
                    float(tree.get('Descuento')) if tree.get('Descuento') else 0)

                if not float_is_zero(self.amount_untaxed - sub_total,
                                     precision_digits=precision):
                    raise UserError(
                        _("The sub-total amount (%s) of the invoice does not match the "
                          "sub-total amount (%s) of the attached xml") %
                        (str(self.amount_untaxed), sub_total)
                    )

                if not float_is_zero(self.amount_total - float(tree.get('Total')),
                                     precision_digits=precision):
                    raise UserError(
                        _("The total amount (%s) of the invoice does not match the total "
                          "amount (%s) of the attached xml") %
                        (str(self.amount_total), tree.get('Total'))
                    )

                if self.currency_id.name != tree.get('Moneda'):
                    raise UserError(
                        _("The invoice currency (%s) does not match the currency (%s) the "
                          "attached xml") % (self.currency_id.name, tree.get('Moneda'))
                    )
                date = tree.get('Fecha')[:10]
                if str(self.invoice_date) != date:
                    raise UserError(
                        _("The invoice date (%s) does not match the date of the XML "
                          "attachment (%s)") % (str(self.invoice_date), date,)
                    )
                uuid = tfd.get('UUID')
                invoice = self.env['account.move'].search([('ref', '=', uuid)], limit=1)
                if invoice:
                    raise UserError(
                        _("El UUID del xml cargado ya se encuentra registrado. \n"
                          + "Factura: (%s)"  % (invoice.name))
                    )
                else:
                    self.ref = uuid


        return super(AccountMove, self).action_post()

    """ @api.model
    def _get_stamp_data(self, cfdi):
        self.ensure_one()
        complemento = cfdi.xpath("//cfdi:Complemento", namespaces={'cfdi': 'http://www.sat.gob.mx/cfd/3'})
        if not complemento:#hasattr(cfdi, 'Complemento'):
            return None
        attribute = '//tfd:TimbreFiscalDigital'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = complemento[0].xpath(attribute, namespaces=namespace)
        _logger.critical(str(node))
        return node[0] if node else None """
    
    @api.model
    def _get_stamp_data(self, cfdi):
        self.ensure_one()
        if cfdi.findall('{http://www.sat.gob.mx/cfd/4}Complemento'):
            complemento = cfdi.xpath("//cfdi:Complemento", namespaces={'cfdi': 'http://www.sat.gob.mx/cfd/4'})
        else:
            complemento = cfdi.xpath("//cfdi:Complemento", namespaces={'cfdi': 'http://www.sat.gob.mx/cfd/3'})
        if not complemento:#hasattr(cfdi, 'Complemento'):
            return None
        attribute = '//tfd:TimbreFiscalDigital'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = complemento[0].xpath(attribute, namespaces=namespace)
        return node[0] if node else None