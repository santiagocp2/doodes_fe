# coding: utf-8
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

from datetime import timedelta
import base64
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def l10n_co_edi_upload_electronic_invoice(self):
        visualdt_api = self.env['visualdte.api'].search(
            [('active', '=', True)], limit=1)
        if not visualdt_api:
            return super(AccountMove, self).l10n_co_edi_upload_electronic_invoice()
        return self._send_document_to_visualdte(visualdt_api)

    def _send_document_to_visualdte(self, api):
        '''Sends the xml to visualdte.
        '''
        now = fields.Datetime.now()
        oldest_date = now - timedelta(days=5)
        newest_date = now + timedelta(days=10)
        to_process = self.filtered(
            lambda move: move._l10n_co_edi_is_l10n_co_edi_required())
        if to_process:
            if to_process.filtered(lambda m: not m.partner_id.vat):
                raise UserError(
                    _('You can not validate an invoice that has a partner without VAT number.'))
            if to_process.filtered(lambda m: (not m.partner_id.l10n_co_edi_obligation_type_ids and not m.partner_id.type == 'invoice') or
                                   (m.partner_id.type == 'invoice' and not m.partner_id.commercial_partner_id.l10n_co_edi_obligation_type_ids)):
                raise UserError(
                    _('All the information on the Customer Fiscal Data section needs to be set.'))
            for invoice in to_process:
                if invoice.invoice_date and not (oldest_date <= fields.Datetime.to_datetime(invoice.invoice_date) <= newest_date):
                    invoice.message_post(body=_(
                        'The issue date can not be older than 5 days or more than 5 days in the future'))
                # TODO: Add check for unspsc_code_id attribute, once 'UNSPSC product codes' module is ready.
                if (invoice.l10n_co_edi_type == '2' and
                    any(l.product_id and not l.product_id.l10n_co_edi_customs_code for l in invoice.invoice_line_ids)) \
                    or (any(l.product_id and not l.product_id.default_code and
                        not l.product_id.barcode for l in invoice.invoice_line_ids)):
                    raise UserError(_(
                        'Every product on a line should at least have a product code (barcode, internal) set.'))

                xml_filename = self._l10n_co_edi_generate_electronic_invoice_filename()

                xml = self.l10n_co_edi_generate_electronic_invoice_xml()
                xml_base64 = base64.b64encode(xml)
                self.env['ir.attachment'].create({
                    'name': xml_filename,
                    'res_id': invoice.id,
                    'res_model': invoice._name,
                    'type': 'binary',
                    'raw': xml,
                    'mimetype': 'application/xml',
                    'description': _('Colombian invoice UBL XML generated for the %s document.', invoice.name),
                })

                json_data = {
                    "nombrearchivo": invoice.company_id.fe_code + invoice.company_id.fe_code + xml_filename,
                    "base64": xml_base64.decode("ascii")
                }
                data = {
                    'id': invoice.id,
                    'json_data': json_data
                }
                result = api._post_request_send_xml(data)
                if result:

                    invoice.l10n_co_edi_cufe_cude_ref = result.get('cufe', False)
                    data_zip = result.get('zip', False)
                    msg = 'Integración con VisualDTE exitosa. Mensaje de VisualDTE:<br/>%s' % result['response']

                    # == Create the attachment ==
                    attachment = self.env['ir.attachment'].create({
                        'name': xml_filename.replace('.xml', '.zip'),
                        'res_id': invoice.id,
                        'res_model': invoice._name,
                        'type': 'binary',
                        'datas': data_zip,
                        'mimetype': 'application/xml',
                        'description': _('Colombia UBL - adjuntos generados para la factura %s.', invoice.name),
                    })

                    # == Chatter ==
                    invoice.with_context(no_new_invoice=True).message_post(
                        body=msg, attachment_ids=attachment.ids)
                else:

                    msg = 'Error en la integración con VisualDTE'
                    # == Chatter ==
                    invoice.with_context(no_new_invoice=True).message_post(body=msg)
