# -*- coding: utf-8 -*-
{
    'name': "bs_booking_service",

    'summary': """
        - Chứa các cấu hình cơ bản cho phần đặt dịch vụ
        """,

    'description': """
        - Cấu hình và thông tin của giường
        - Các trường cơ bản của phần đặt dịch vụ
    """,

    'author': "HoiHD",
    'website': "https://facebook.com/hoihandsome",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'CRM',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/bs_service_bed.xml',
        'views/booking_service.xml',
        'views/product_product.xml',
        'views/menu.xml',
    ],
}
