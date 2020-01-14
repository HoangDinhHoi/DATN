# -*- coding: utf-8 -*-
{
    'name': "CRM Lead",

    'summary': """
       CRM Lead""",

    'description': """
        CRM Lead
    """,

    'author': "HoiHD",
    'website': "http://www.fb.com/hoihandsome",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customer Relationship Management',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'izi_crm_contact', 'izi_partner', 'izi_partner_source', 'izi_message_dialog'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizards/crm_lead_assign.xml',
        'views/crm_lead.xml',
    ],
}
