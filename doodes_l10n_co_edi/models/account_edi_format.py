# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, api, models, _

from datetime import timedelta


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _needs_web_services(self):
        # OVERRIDE
        return self.code == 'ubl_visualdte' or super()._needs_web_services()

    def _is_compatible_with_journal(self, journal):
        # OVERRIDE
        self.ensure_one()
        if self.code != 'ubl_visualdte':
            return super()._is_compatible_with_journal(journal)
        return journal.type in ['sale'] and journal.country_code == 'CO'

    def _check_move_configuration(self, move):
        # OVERRIDE
        self.ensure_one()
        edi_result = super()._check_move_configuration(move)
        if self.code != 'ubl_visualdte':
            return edi_result

        company = move.company_id
        journal = move.journal_id
        now = fields.Datetime.now()
        oldest_date = now - timedelta(days=5)
        newest_date = now + timedelta(days=10)

        visualdt_api = self.env['visualdte.api'].search(
            [('active', '=', True)], limit=1)

        if not visualdt_api:
            edi_result.append(("Necesita configurar una Visualdte API."))
        if not company.fe_code:
            edi_result.append(("Necesita un 'FE Codigo' para la compañia."))
        if (move.move_type != 'out_refund' and not move.debit_origin_id) and \
           (not journal.l10n_co_edi_dian_authorization_number or not journal.l10n_co_edi_dian_authorization_date or not journal.l10n_co_edi_dian_authorization_end_date):
            edi_result.append(
                _("'Resolución DIAN' fields must be set on the journal %s", journal.display_name))
        if not move.partner_id.vat:
            edi_result.append(
                _("You can not validate an invoice that has a partner without VAT number."))
        if not move.company_id.partner_id.l10n_co_edi_obligation_type_ids:
            edi_result.append(_("'Obligaciones y Responsabilidades' on the Customer Fiscal Data section needs to be set for the partner %s.",
                              move.company_id.partner_id.display_name))
        if not move.amount_total:
            edi_result.append(
                _("You cannot send Documents in Carvajal without an amount."))
        if not move.partner_id.commercial_partner_id.l10n_co_edi_obligation_type_ids:
            edi_result.append(_("'Obligaciones y Responsabilidades' on the Customer Fiscal Data section needs to be set for the partner %s.",
                              move.partner_id.commercial_partner_id.display_name))
        if (move.l10n_co_edi_type == '2' and
                any(l.product_id and not l.product_id.l10n_co_edi_customs_code for l in move.invoice_line_ids)):
            edi_result.append(
                _("Every exportation product must have a customs code."))
        elif move.invoice_date and not (oldest_date <= fields.Datetime.to_datetime(move.invoice_date) <= newest_date):
            move.message_post(body=_(
                'The issue date can not be older than 5 days or more than 5 days in the future'))
        elif any(l.product_id and not l.product_id.default_code and
                 not l.product_id.barcode and not l.product_id.unspsc_code_id for l in move.invoice_line_ids):
            edi_result.append(
                _("Every product on a line should at least have a product code (barcode, internal, UNSPSC) set."))

        if not move.company_id.partner_id.l10n_latam_identification_type_id.l10n_co_document_code:
            edi_result.append(
                _("The Identification Number Type on the company\'s partner should be 'NIT'."))
        if not move.partner_id.commercial_partner_id.l10n_latam_identification_type_id.l10n_co_document_code:
            edi_result.append(
                _("The Identification Number Type on the customer\'s partner should be 'NIT'."))

        # Sugar taxes
        for line in move.invoice_line_ids:
            if "IBUA" in line.tax_ids.l10n_co_edi_type.mapped('name') and line.product_id.volume == 0:
                edi_result.append(
                    _("You should set a volume on product: %s when using IBUA taxes.", line.product_id.name))

        return edi_result
