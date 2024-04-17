
from odoo import fields, models, _


class WebApiLog(models.Model):
    _name = 'web.api.log'
    _description = 'Web API Log'
    _rec_name = 'function'
    _order = 'date_request desc'

    res_model = fields.Char(
        string='Modelo',
        required=True,
        help='Modelo desde donde se realiza la petición'
    )
    res_id = fields.Integer(
        string='ID',
        help='ID del registro'
    )
    visualdte_api_id = fields.Many2one(
        comodel_name='visualdte.api',
        string='API',
        help='API VisualDTE'
    )
    function = fields.Char(
        string='Función a ejecutar'
    )
    date_request = fields.Datetime(
        required=True
    )
    date_done = fields.Datetime()
    response = fields.Char(
        string='Respuesta',
        help='Mensaje de respuesta del servidor'
    )
    values = fields.Text(
        string='Valores a enviar',
        help='Valores a enviar en la petición'
    )
    state = fields.Selection(
        [('waiting', 'Esperando'),
         ('error', 'Error'),
         ('success', 'Exitoso')],
        default='waiting'
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Usuario',
        default=lambda self: self.env.user
    )

    def _register_success_log(self, data):
        data['state'] = 'success'
        return self.create(data)

    def _register_error_log(self, data):
        data['state'] = 'error'
        return self.create(data)

    def _register_waiting_log(self, data):
        data['state'] = 'waiting'
        return self.create(data)
