from odoo import fields, models, api, _
import requests
import logging

_logger = logging.getLogger(__name__)


class VisualdteApi(models.Model):
    _name = 'visualdte.api'
    _description = 'Visualdte API'
    _order = 'id desc'

    name = fields.Char(
        string='Nombre',
        required=True
    )
    active = fields.Boolean(
        default=True
    )
    key = fields.Char(
        string='Key',
        required=True
    )
    url = fields.Char(
        string='URL',
        required=True
    )
    endpoint_send_invoice = fields.Char(
        string='Endpoint - Envio Factura',
        required=True
    )
    total_invoice_send = fields.Integer(
        string='Total Facturas Enviadas',
        compute='_compute_total_invoice_send'
    )
    log_line_ids = fields.One2many(
        comodel_name='web.api.log',
        inverse_name='visualdte_api_id',
        string='Facturas Enviadas Exitosamente',
        domain=[('state', '=', 'success')]
    )

    @api.depends('log_line_ids')
    def _compute_total_invoice_send(self):
        for record in self:
            record.total_invoice_send = len(record.log_line_ids)

    def action_view_log_invoice_send(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'doodes_l10n_co_edi.action_web_api_log')
        action['domain'] = [('visualdte_api_id.id', '=', self.id), ('state', '=', 'success')]
        return action

    def _post_request_send_xml(self, data):

        url = self.url + self.endpoint_send_invoice
        key = self.key
        json_data = data['json_data']
        date_request = fields.Datetime.now()

        values = {
            'res_model': 'account.move',
            'res_id': data['id'],
            'function': _('Envio XML - Visualdte API'),
            'visualdte_api_id': self.id,
            'user_id': self.env.user.id,
            'date_request': date_request
        }

        headers = {'Authorization': f'Api-Key {key}'}

        log = self.env['web.api.log']
        values['values'] = json_data
        try:
            get_q = requests.post(url, data=json_data,
                                  headers=headers, timeout=30)
            if get_q.status_code == 200:
                values['response'] = get_q.text
                values['date_done'] = fields.Datetime.now()
                log._register_success_log(values)
                _logger.info("ENVIO EXITOSO DE LA FACTURA A VISUALDTE")
                return get_q.json()
            else:
                values['response'] = get_q.json()
                values['date_done'] = fields.Datetime.now()
                log._register_error_log(values)
                _logger.error("ERROR EN EL ENVIO DE LA FACTURA A VISUALDTE: "+str(get_q.json()))
        except requests.exceptions.ConnectionError as e:
            values['response'] = e
            values['date_done'] = fields.Datetime.now()
            log._register_error_log(values)
            _logger.error("ERROR EN EL ENVIO DE LA FACTURA A VISUALDTE: "+str(e))
        except requests.exceptions.HTTPError as e:
            values['response'] = e
            values['date_done'] = fields.Datetime.now()
            log._register_error_log(values)
            _logger.error("ERROR EN EL ENVIO DE LA FACTURA A VISUALDTE: "+str(e))
        except Exception as e:
            values['response'] = e
            values['date_done'] = fields.Datetime.now()
            log._register_error_log(values)
            _logger.error("ERROR EN EL ENVIO DE LA FACTURA A VISUALDTE: "+str(e))
        return False
