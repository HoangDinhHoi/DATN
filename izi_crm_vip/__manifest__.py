# -*- coding: utf-8 -*-
{
    'name': "CRM Vip",

    'summary': """
        CRM Vip""",

    'description': """
        CRM VIP
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'VIP',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'sale', 'izi_base', 'izi_crm', 'point_of_sale',
                'izi_pos', 'izi_pos_use_service', 'izi_pos_customer_confirm', 'izi_pos_refund'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/crm_vip_security.xml',
        'views/res_partner_vip.xml',
        'views/crm_customer_rank.xml',
        'views/crm_customer_rank_rule.xml',
        'views/partner_rank_confirm.xml',
        'views/partner_rank_history.xml',
        'views/pos_order.xml',
        # 'views/pos_use_use_service.xml',
        'views/res_partner.xml',
        'views/res_partner_revenue.xml',
        'wizards/confirm_edit_img.xml',
        'wizards/partner_up_rank.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
