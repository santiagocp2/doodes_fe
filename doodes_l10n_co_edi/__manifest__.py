# -*- coding: utf-8 -*-
{
    'name': 'Electronic invoicing with DOODES',
    'version': '0.1',
    'category': 'Accounting',
    'summary': 'Colombian Localization for EDI documents with DOODES',
    'author': 'Santiago Cortazar <santiagocp333@outlook.es>',
    'depends': ['l10n_co_edi'],
    'data': [
        'data/account_edi_data.xml',
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/web_api_log_views.xml',
        'views/visualdte_api_views.xml'
    ],
    'qweb':[
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'installable': True,
    'application': False,
    'auto_install': False
}
