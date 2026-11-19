{
    'name': "CRM - Sales Teams Advanced",
    'name_vi_VN': "CRM - Đội bán hàng nâng cao",
    'summary': """
Integrate Sales Team Advanced with CRM""",
    'summary_vi_VN': """
Tích hợp đội bán hàng nâng cao với CRM""",
    'description': """
This module extends CRM with more sales teams that offered by the module Sales Team Advanced to have complex sales teams organization that may be required by larger companies

Key Features
------------

* Improve access rights to crm models
* CRM reports now support filter and group by sales region, sales team leader, sales regional manager

Access Groups
=============
* **Sales / User: Own Documents Only**: this is a default group in Odoo.
* **Sales / Sales Team Leader**: new access group that inherits "Sales / User: Own Documents Only"
* **Sales / Regional Manager**: a new access group that inherits the group "Sales / Sales Team Leader"
* **Sales / User: All Documents**: this is a default group in Odoo. It now inherits "Sales / Regional Manager" instead of "Sales / User: Own Documents Only"
* **Sales / Manager**: Full access rights to Sales Management application

Security Policies
=================

* **Sales / User: Own Documents Only**: view team of which she or he is a member
* **Sales / Sales Team Leader**: view/edit team of which she or he is either a member or the team leader
* **Sales / Regional Manager**: view/edit/create/delete team of which she or he is either a member or the team leader or the regional manager
* **Sales / User: All Documents**: full access rights for all teams but sales configurations
* **Sales / Manager**: Full access rights to Sales Management application, including doing configuration

Note
====

For Sales & CRM Integration, you may also want the module "Sales - Sales Teams Advanced": https://apps.odoo.com/apps/modules/13.0/to_sales_team_advanced_sale/

Editions Supported
==================
1. Community Edition
2. Enterprise Edition

    """,

    'description_vi_VN': """
Module này làm gì
=================
Module này mở rộng CRM với nhiều đội bán hàng được cung cấp bởi module Đội bán hàng nâng cao để có tổ chức nhóm bán hàng phức tạp có thể được yêu cầu bởi các công ty lớn hơn.

* Cải thiện quyền truy cập vào các mô hình CRM
* Báo cáo CRM hiện hỗ trợ bộ lọc và nhóm theo khu vực bán hàng, đội trưởng bán hàng, quản lý khu vực bán hàng.

Nhóm truy cập
=============
* **Bán hàng / Người dùng: Chỉ tài liệu của chính mình**: đây là nhóm mặc định trong odoo.
* **Bán hàng / Đội trưởng bán hàng**: nhóm truy cập mới kế thừa nhóm "Bán hàng / Người dùng: Chỉ tài liệu của chính mình"
* **Bán hàng / Người quản lý khu vực**: nhóm truy cập mới kế thừa nhóm "Bán hàng / Đội trưởng bán hàng"
* **Bán hàng / Người dùng: Tất cả tài liệu**: đây là nhóm mặc định trong odoo. Bây giờ nó kế thừa "Bán hàng / Người quản lý khu vực" thay vì "Bán hàng / Người dùng: Chỉ tài liệu của chính mình"
* **Bán hàng / Người quản lý**: Đầy đủ quyền truy cập đến ứng dụng Quản lý bán hàng.

Chính sách bảo mật
==================

* **Bán hàng / Người dùng: Chỉ tài liệu của chính mình**: xem đội mà anh ấy hoặc cô ấy là thành viên
* **Bán hàng / Đội trưởng bán hàng**: xem/chỉnh sửa đội mà cô ấy hoặc anh ấy là thành viên hoặc đội trưởng
* **Bán hàng / Người quản lý khu vực**: xem/sửa/tạo/xóa đội mà anh ấy là thành viên hoặc đội trưởng hoặc người quản lý khu vực
* **Bán hàng / Người dùng: Tất cả tài liệu**: đầy đủ tất cả các quyền truy cập các đội trừ cấu hình bán hàng
* **Bán hàng / Người quản lý**: Toàn quyền truy cập vào ứng dụng bán hàng, bao gồm cả cấu hình bán hàng

Ghi chú
=======

Để tích hợp Bán hàng và CRM, bạn cũng có thể muốn module "Bán hàng - Đội bán hàng nâng cao"

Ấn bản hỗ trợ
=============
1. Ấn bản cộng đồng
2. Ấn bản doanh nghiệp

    """,

    'author': "T.V.T Marine Automation (aka TVTMA)",
    'website': 'https://www.tvtmarine.com',
    'live_test_url': 'https://v13demo-int.erponline.vn',
    'support': 'support@ma.tvtmarine.com',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['to_sales_team_advanced', 'crm'],

    # always loaded
    'data': [
        'security/crm_security.xml',
        'report/crm_activity_report_views.xml',
        'report/crm_opportunity_report_views.xml',
        'views/crm_lead_views.xml',
        'views/crm_team_region_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
    'price': 45.9,
    'currency': 'EUR',
    'license': 'OPL-1',
}
