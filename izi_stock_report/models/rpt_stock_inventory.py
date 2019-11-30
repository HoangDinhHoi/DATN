# -*- coding: utf-8 -*-

import odoo.tools.config as config
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import except_orm, UserError, ValidationError

try:
    import cStringIO as stringIOModule
except ImportError:
    try:
        import StringIO as stringIOModule
    except ImportError:
        import io as stringIOModule
import base64
import xlwt
from xlwt import Formula
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class StockReportInventoryReport(models.TransientModel):
    _name = 'stock.report.inventory.report'

    name = fields.Char(default='Báo cáo tồn kho')
    compute_at_date = fields.Selection([
        (0, 'Current Inventory'),
        (1, 'At a Specific Date')
    ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")
    date = fields.Date('Inventory at Date', help="Choose a date to get the inventory at that date")
    all = fields.Boolean('All')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    view_location_id = fields.Many2one('stock.location', 'View Location', related='warehouse_id.view_location_id',
                                       store=False)
    location_ids = fields.Many2many('stock.location', string='Locations',domain=[('usage','=','internal')])
    inventory_line = fields.One2many('stock.report.inventory.line', 'inventory_id', 'Lines')


    def open_table(self):
        self.ensure_one()
        self.inventory_line.unlink()
        today = datetime.today().strftime('%Y-%m-%d')

        if self.compute_at_date == 0 or self.date == today:
            self.update({
                'name': 'Báo cáo tồn kho ngày ' + today
            })
            # HoiHD: Xóa bản ghi được tạo ra trước đó, để tránh đầy database
            self._cr.execute('''DELETE FROM stock_report_inventory_line WHERE inventory_id=%s''', (self.id-1,))
            # end HoiHD

            list_location = []
            if len(self.location_ids) >= 1:
                for location_parent in self.location_ids:
                    list_location.append(location_parent.id)
            else:
                obj_location = self.env['stock.location'].search(
                    [('branch_id', '=', self.warehouse_id.branch_id.id), ('active', '=', 't')])
                if len(obj_location) >= 1:
                    for i in obj_location:
                        list_location.append(i.id)
            if len(list_location) >= 1:
                for location in list_location:
                    locations = self._list_location(location, [location])
                    if len(locations) >= 1:
                        for location in locations:
                            sql = " INSERT INTO stock_report_inventory_line(" \
                                  "inventory_id,product_id,categ_id,warehouse_id,company_id,lot_id,location_id," \
                                  "quantity,quantity_standard_tablet,uom_id, create_date, create_uid,write_uid,write_date)" \
                                  "  SELECT" \
                                  " (%d) as inventory_id," \
                                  " pp.id as product_id," \
                                  " pt.categ_id as categ_id," \
                                  " (%d) as warehouse_id," \
                                  " co.id as company_id," \
                                  " spl.id as lot_id," \
                                  " d.id as location_id," \
                                  " SUM(quantity) as quantity," \
                                  "(CASE " \
                                  "	WHEN ( " \
                                  "		pt.volume <>0 " \
                                  " ) THEN " \
                                  "	SUM(quantity) * pt.volume " \
                                  "	ELSE " \
                                  " SUM(quantity) END ) quantity_standard_tablet , " \
                                  " u.id as uom_id," \
                                  " now() as create_date," \
                                  " (%d) as create_uid," \
                                  " (%d) as write_uid," \
                                  " now() as write_date" \
                                  " FROM stock_quant quant" \
                                  " JOIN product_product pp ON quant.product_id = pp.id" \
                                  " JOIN product_template pt ON pp.product_tmpl_id = pt.id" \
                                  " JOIN uom_uom u ON u.id = pt.uom_id" \
                                  " LEFT JOIN stock_production_lot spl ON spl.id = quant.lot_id" \
                                  " INNER JOIN stock_location d ON quant.location_id = d.id" \
                                  " INNER JOIN res_company co ON d.company_id = co.id" \
                                  " AND d.id = %d" \
                                  " GROUP BY pp.id,co.id,spl.id,u.id,d.id, pt.id,pt.categ_id" \
                                  " ORDER BY pp.id "
                            self._cr.execute(sql % (self.id, self.warehouse_id, self.env.user.id, self.env.user.id, location))
        else:
            if not self.date:
                raise except_orm(_('Thông báo'), _('Bạn chưa chọn ngày!'))
            self.update({
                'name': 'Báo cáo tồn kho ngày ' + self.date.strftime('%d/%m/%Y')
            })
            date_time_str = self.date.strftime(DEFAULT_SERVER_DATE_FORMAT) + ' 23:59:59'
            date_time_obj = datetime.strptime(date_time_str, DEFAULT_SERVER_DATETIME_FORMAT)
            # HoiHD: Xóa bản ghi trước khi tạo mới
            self._cr.execute('''DELETE FROM stock_report_inventory_line WHERE inventory_id=%s''', (self.id-1,))
            # end HoiHD
            for location_parent in self.location_ids:
                list = []
                list.append(location_parent.id)
                locations = self._list_location(location_parent.id,list)
                for location_id in locations:
                    sql = """
                                INSERT INTO stock_report_inventory_line (
                    inventory_id,
                    product_id,
                    categ_id,
                    company_id,
                    lot_id,
                    warehouse_id,
                    location_id,
                    quantity,
                    uom_id,
                    quantity_standard_tablet,
                    create_date,
                    create_uid,
                    write_uid,
                    write_date
                ) SELECT 
                                (%d) as inventory_id,
                                product_id,
                                categ_id,
                                (%d) as company_id,
                                lot_id,
                                (%d) as warehouse_id,
                                (%d) AS location_id,
                                sum(ton_kho) tonkho,
                                uom_id,
                                (CASE 
                    WHEN volume <>0 THEN
                    SUM(ton_kho) * volume
                    ELSE 
                    SUM(ton_kho) END ) quantity_standard_tablet,
                    now() as create_date,
                    (%d) as create_uid,
                    (%d) as write_uid,
                    now() as write_date
                      FROM(SELECT
                        a1.product_id,
                        (
                            SELECT
                                categ_id
                            FROM
                                product_template pt
                            INNER JOIN product_product pp ON pt. ID = pp.product_tmpl_id
                            WHERE
                                pp.id = a1.product_id
                        ) categ_id,
                        a1.lot_id,
                        sum(sl) ton_kho,
                        (
                            SELECT
                                uom_id
                            FROM
                                product_template pt
                            INNER JOIN product_product pp ON pt. ID = pp.product_tmpl_id
                            WHERE
                                pp. ID = a1.product_id
                        ) uom_id,
                            (SELECT
                                pt.volume
                            FROM
                                product_template pt
                            INNER JOIN product_product pp ON pt. ID = pp.product_tmpl_id
                            WHERE
                                pp. ID = a1.product_id
                        )volume,
                        now() AS create_date,
                        now() AS write_date
                    FROM
                        (
                      SELECT p.id product_id, l.id lot_id, -(sml.qty_done/u1.factor*u2.factor) sl
                        FROM stock_move_line sml
                        LEFT JOIN product_product p on sml.product_id = p.id
                        LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                        INNER JOIN product_product pp ON sml.product_id = pp.id 
                        INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                        INNER JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                        INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                        WHERE sml.date <= '%s'
                        AND sml.state = 'done'
                        AND sml.location_id = %d
                        AND sml.location_dest_id != %d
                        UNION ALL
                        SELECT p.id product_id, l.id lot_id,(sml.qty_done/u1.factor*u2.factor) sl
                        FROM stock_move_line sml
                        LEFT JOIN product_product p on sml.product_id = p.id
                        LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                        INNER JOIN product_product pp ON sml.product_id = pp.id 
                        INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                        INNER JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                        INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                        WHERE sml.date <= '%s'
                        AND sml.state = 'done'
                        AND sml.location_id != %d
                        AND sml.location_dest_id = %d
                        ) a1
                        GROUP BY a1.product_id, a1.lot_id) a
                        WHERE a.ton_kho <> 0
                        GROUP BY product_id,lot_id,categ_id,uom_id, volume;
                                            """
                    self._cr.execute(sql % (
                    self.id, self.env.user.company_id.id, self.warehouse_id.id, location_id, self.env.user.id,
                    self.env.user.id, date_time_obj,
                    location_id,location_id,
                    date_time_obj, location_id,location_id))

        pivot_view_id = self.env.ref('izi_stock_report.view_inventory_report_pivot').id

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'pivot',
            'name': _('Inventory'),
            'res_id': False,
            'res_model': 'stock.report.inventory.line',
            'views': [(pivot_view_id, 'pivot')],
            'context': dict(self.env.context),
            'domain': [('inventory_id', '=', self.id)],
        }
        return action

    def _list_location(self, location_id, list):
        location_ids = self.env['stock.location'].search([('location_id', '=', location_id)])

        # line location row
        for line in location_ids:
            if line.id not in list:
                list.append(line.id)

        for line_location in location_ids:
            self._list_location(line_location.id, list)
        return list

    """
        Author: HoiHD
        Description: - Lấy ra dữ liệu tồn kho tại kho và theo ngày rồi đổ vào bảng tạm
                     - Hàm trả về 1 list gồm:
                            + các param
                            + 1 đường link để view on web
                            + 1 đường link để xuất báo cáo ra file excel
        Date: 20/05/2019 on 9:26 AM
    """
    @api.multi
    def get_data_inventory(self):
        self.ensure_one()
        self.inventory_line.unlink()
        today = datetime.today().strftime('%Y-%m-%d')

        birt_datasource = config['birt_datasource'] or '0'
        db_user = config['db_user'] or '0'
        db_password = config['db_password'] or '0'
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise ValidationError("You must config birt_url in file config")
        if birt_datasource == '0':
            raise ValidationError("You must config birt_datasource in file config")

        # cho toan bo id cua location vao trong 1 string ngan cach boi dau phay
        location = '0'
        if len(self.location_ids) != 0:
            for line in self.location_ids:
                location += ',' + str(line.id)

        param_str = {
            '&database_url': birt_datasource + self.pool._db.dsn['database'],
            '&db_user': db_user,
            '&db_password': db_password,
            '&warehouse_id': str(self.warehouse_id.id),
            '&location_id': location,
        }

        if self.compute_at_date == 0 or self.date == today:
            self.update({
                'name': 'Báo cáo tồn kho ngày ' + today
            })
            # HoiHD: Xóa bản ghi trùng lặp trước khi tạo mới
            self._cr.execute('''DELETE FROM stock_report_inventory_line WHERE inventory_id=%s''', (self.id-1,))
            # end HoiHD
            list_location = []
            if len(self.location_ids) >= 1:
                for location_parent in self.location_ids:
                    list_location.append(location_parent.id)
            else:
                obj_location = self.env['stock.location'].search(
                    [('branch_id', '=', self.warehouse_id.branch_id.id), ('active', '=', 't')])
                if len(obj_location) >= 1:
                    for i in obj_location:
                        list_location.append(i.id)
            if len(list_location) >= 1:
                for location in list_location:
                    locations = self._list_location(location, [location])
                    if len(locations) >= 1:
                        for location in locations:
                            sql = " INSERT INTO stock_report_inventory_line(" \
                                  "inventory_id,product_id,categ_id,warehouse_id,company_id,lot_id,location_id," \
                                  "quantity,quantity_standard_tablet,uom_id, create_date, create_uid,write_uid,write_date)" \
                                  "  SELECT" \
                                  " (%d) as inventory_id," \
                                  " pp.id as product_id," \
                                  " pt.categ_id as categ_id," \
                                  " (%d) as warehouse_id," \
                                  " co.id as company_id," \
                                  " spl.id as lot_id," \
                                  " d.id as location_id," \
                                  " SUM(quantity) as quantity," \
                                  "(CASE " \
                                  "	WHEN ( " \
                                  "		pt.volume <>0 " \
                                  " ) THEN " \
                                  "	SUM(quantity) * pt.volume " \
                                  "	ELSE " \
                                  " SUM(quantity) END ) quantity_standard_tablet , " \
                                  " u.id as uom_id," \
                                  " now() as create_date," \
                                  " (%d) as create_uid," \
                                  " (%d) as write_uid," \
                                  " now() as write_date" \
                                  " FROM stock_quant quant" \
                                  " JOIN product_product pp ON quant.product_id = pp.id" \
                                  " JOIN product_template pt ON pp.product_tmpl_id = pt.id" \
                                  " JOIN uom_uom u ON u.id = pt.uom_id" \
                                  " LEFT JOIN stock_production_lot spl ON spl.id = quant.lot_id" \
                                  " INNER JOIN stock_location d ON quant.location_id = d.id" \
                                  " INNER JOIN res_company co ON d.company_id = co.id" \
                                  " AND d.id = %d" \
                                  " GROUP BY pp.id,co.id,spl.id,u.id,d.id, pt.id,pt.categ_id" \
                                  " ORDER BY pp.id "
                            self._cr.execute(sql % (self.id, self.warehouse_id, self.env.user.id, self.env.user.id, location))
            report_name = "rpt_stock_inventory_at_warehouse.rptdesign"  # báo cáo tồn kho tại kho
            param_str.update({
                '&compute_at_date': '0',
            })
        else:
            if not self.date:
                raise except_orm(_('Thông báo'), _('Bạn chưa chọn ngày!'))
            self.update({
                'name': 'Báo cáo tồn kho ngày ' + self.date.strftime('%d/%m/%Y')
            })
            date_time_str = self.date.strftime(DEFAULT_SERVER_DATE_FORMAT) + ' 23:59:59'
            date_time_obj = datetime.strptime(date_time_str, DEFAULT_SERVER_DATETIME_FORMAT)
            # HoiHD: Xóa bản ghi trước khi tạo mới
            self._cr.execute('''DELETE FROM stock_report_inventory_line WHERE inventory_id=%s''', (self.id-1,))
            # end HoiHD
            list_location = []
            if len(self.location_ids) >= 1:
                for location_parent in self.location_ids:
                    list_location.append(location_parent.id)
            else:
                obj_location = self.env['stock.location'].search(
                    [('branch_id', '=', self.warehouse_id.branch_id.id), ('active', '=', 't')])
                if len(obj_location) >= 1:
                    for i in obj_location:
                        list_location.append(i.id)
            if len(list_location) >= 1:
                for location in list_location:
                    locations = self._list_location(location, [location])
                    if len(locations) >= 1:
                        for location_id in locations:
                            sql = """
                                                INSERT INTO stock_report_inventory_line (
                                    inventory_id,
                                    product_id,
                                    categ_id,
                                    company_id,
                                    lot_id,
                                    warehouse_id,
                                    location_id,
                                    quantity,
                                    uom_id,
                                    quantity_standard_tablet,
                                    create_date,
                                    create_uid,
                                    write_uid,
                                    write_date
                                ) SELECT 
                                                (%d) as inventory_id,
                                                product_id,
                                                categ_id,
                                                (%d) as company_id,
                                                lot_id,
                                                (%d) as warehouse_id,
                                                (%d) AS location_id,
                                                sum(ton_kho) tonkho,
                                                uom_id,
                                                (CASE 
                                    WHEN volume <>0 THEN
                                    SUM(ton_kho) * volume
                                    ELSE 
                                    SUM(ton_kho) END ) quantity_standard_tablet,
                                    now() as create_date,
                                    (%d) as create_uid,
                                    (%d) as write_uid,
                                    now() as write_date
                                      FROM(SELECT
                                        a1.product_id,
                                        (
                                            SELECT
                                                categ_id
                                            FROM
                                                product_template pt
                                            INNER JOIN product_product pp ON pt. ID = pp.product_tmpl_id
                                            WHERE
                                                pp.id = a1.product_id
                                        ) categ_id,
                                        a1.lot_id,
                                        sum(sl) ton_kho,
                                        (
                                            SELECT
                                                uom_id
                                            FROM
                                                product_template pt
                                            INNER JOIN product_product pp ON pt. ID = pp.product_tmpl_id
                                            WHERE
                                                pp. ID = a1.product_id
                                        ) uom_id,
                                            (SELECT
                                                pt.volume
                                            FROM
                                                product_template pt
                                            INNER JOIN product_product pp ON pt. ID = pp.product_tmpl_id
                                            WHERE
                                                pp. ID = a1.product_id
                                        )volume,
                                        now() AS create_date,
                                        now() AS write_date
                                    FROM
                                        (
                                      SELECT p.id product_id, l.id lot_id, -(sml.qty_done/u1.factor*u2.factor) sl
                                        FROM stock_move_line sml
                                        LEFT JOIN product_product p on sml.product_id = p.id
                                        LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                                        INNER JOIN product_product pp ON sml.product_id = pp.id 
                                        INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                                        INNER JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                                        INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                                        WHERE sml.date <= '%s'
                                        AND sml.state = 'done'
                                        AND sml.location_id = %d
                                        AND sml.location_dest_id != %d
                                        UNION ALL
                                        SELECT p.id product_id, l.id lot_id,(sml.qty_done/u1.factor*u2.factor) sl
                                        FROM stock_move_line sml
                                        LEFT JOIN product_product p on sml.product_id = p.id
                                        LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                                        INNER JOIN product_product pp ON sml.product_id = pp.id 
                                        INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                                        INNER JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                                        INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                                        WHERE sml.date <= '%s'
                                        AND sml.state = 'done'
                                        AND sml.location_id != %d
                                        AND sml.location_dest_id = %d
                                        ) a1
                                        GROUP BY a1.product_id, a1.lot_id) a
                                        WHERE a.ton_kho <> 0
                                        GROUP BY product_id,lot_id,categ_id,uom_id, volume;
                                                            """
                            self._cr.execute(sql % (
                                self.id, self.env.user.company_id.id, self.warehouse_id.id, location_id, self.env.user.id,
                                self.env.user.id, date_time_obj,
                                location_id, location_id,
                                date_time_obj, location_id, location_id))
            report_name = "rpt_stock_inventory_at_date.rptdesign"  # báo cáo tồn kho theo ngày
            param_str.update({
                '&compute_at_date': '1',
                '&date': self.date.strftime('%d/%m/%Y'),
            })
        birt_link = birt_url + report_name
        birt_link_excel = birt_url + report_name + '&__format=xlsx&__svg=true'
        return [birt_link, birt_link_excel, param_str]
    """ 
        Author: HoiHD
        Description: Xem trực tiếp báo cáo trên web
        Date: 20/05/2019 on 9:47 AM 
    """
    @api.multi
    def view_report_on_web(self):
        self.get_data_inventory()
        return {
            "type": "ir.actions.client",
            'name': 'WH Document',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': self.get_data_inventory()[0],
                'payload_data': self.get_data_inventory()[2],
            }
        }

    """
        Author: HoiHD
        Description: Xuất báo cáo ra file excel
        Date: 20/05/2019 on 9:47 AM 
    """
    @api.multi
    def export_report_to_excel(self):
        self.get_data_inventory()
        return {
            "type": "ir.actions.client",
            'name': 'WH Document',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': self.get_data_inventory()[1],
                'payload_data': self.get_data_inventory()[2],
            }
        }
    # end by HoiHD

class StockReportInventoryLine(models.TransientModel):
    _name = 'stock.report.inventory.line'

    inventory_id = fields.Many2one('stock.report.inventory.report', 'Inventory')
    product_id = fields.Many2one('product.product', 'Product')
    categ_id = fields.Many2one('product.category', 'Category')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    location_id = fields.Many2one('stock.location', 'Location')
    quantity = fields.Float('Quantity')
    quantity_standard_tablet = fields.Float('Quantity Stadard Tablet')
    uom_id = fields.Many2one('uom.uom', "Product Uom")
    company_id = fields.Many2one('res.company', 'Company')
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial')
