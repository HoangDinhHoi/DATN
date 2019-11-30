# -*- coding: utf-8 -*-
{
    'name': "POS Report Birt",

    'summary': """
                    Các báo cáo BIRT của POS
                """,

    'description': """
        - Các báo cáo doanh thu
        - Các báo cáo công nợ KH và NCC
        - Các báo cáo phân bổ doanh thu cho nhân viên
        - Các báo cáo bảng kê bán hàng, chứng từ
        - Báo cáo điểm đỏ
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'POS Report BIRT',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_pos'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/menu_reports.xml',
        'views/rpt_pos_allocation_employee.xml',
        'views/rpt_pos_allocation_revenue_by_shop.xml',
        'views/rpt_pos_revenue_shop_daily.xml',
        'views/rpt_pos_by_payment.xml',
        'views/rpt_pos_employee_do_service.xml',
        'views/rpt_pos_revenue_customer_by_product_and_service_group.xml',
        'views/rpt_pos_revenue_by_product.xml',
        'views/rpt_pos_list_card_according_to_branch.xml',
        'views/rpt_pos_revenue_product_and_service_by_date.xml',
    ],
}
