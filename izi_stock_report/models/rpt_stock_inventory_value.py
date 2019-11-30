# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import except_orm, ValidationError
import odoo.tools.config as config


class StockReportInventoryValue(models.TransientModel):
    _name = 'stock.report.inventory.value'

    name = fields.Char(default='Báo cáo giá trị hàng tồn')
    all = fields.Boolean('All')
    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse')
    view_location_id = fields.Many2one('stock.location', 'View Location', related='warehouse_id.view_location_id', store=False)
    location_ids = fields.Many2many('stock.location', string='Locations')
    inventory_line = fields.One2many('stock.report.inventory.value.line','inventory_id', 'Lines')

    def open_table(self):
        self.ensure_one()
        # if self.all == True:
        #     warehouse_ids = self.env['stock.warehouse'].search([('x_studio_users_ids','=', self.env.user.id)])
        #     if len(warehouse_ids) < 1:
        #         raise except_orm(_('Thông báo'),_('Bạn không được phân quyền kho'))
        #     if len(warehouse_ids) == 1:
        #         for warehouse_id in warehouse_ids:
        #             _warehouse_ids = warehouse_id.id
        #     else:
        #         wh_ids = []
        #         for warehouse_id in warehouse_ids:
        #             wh_ids.append(warehouse_id.id)
        #         _warehouse_ids = tuple(wh_ids)
        # else:
        #     if len(self.warehouse_id) == 1:
        #         for warehouse_id in self.warehouse_id:
        #             _warehouse_ids = warehouse_id.id
        #     else:
        #         warehouse_ids = []
        #         for warehouse_id in self.warehouse_id:
        #             warehouse_ids.append(warehouse_id.id)
        #         _warehouse_ids = tuple(warehouse_ids)
        # Description: Xóa bản ghi cũ trước khi tạo ra 1 bản ghi mới giống hệt, để giúp đỡ đầy database
        # Author: Hợi HD
        # Date: 09/04/2019
        self._cr.execute('''DELETE FROM stock_report_inventory_value_line WHERE inventory_id = %s''', (self.id-1,))
        #end HoiHD
        list_location = []
        if len(self.location_ids) >=1:
            for location_parent in self.location_ids:
                list_location.append(location_parent.id)
        else:
            obj_location= self.env['stock.location'].search([('branch_id', '=', self.warehouse_id.branch_id.id), ('active', '=', 't')])
            if len(obj_location) >=1:
                for i in obj_location:
                    list_location.append(i.id)
        if len(list_location) >=1:
            for location in list_location:
                locations = self._list_location(location, [location])
                if len(locations)>=1:
                    for location in locations:
                        sql = '''
                            INSERT INTO stock_report_inventory_value_line(
                                inventory_id, 
                                product_id, 
                                categ_id, 
                                company_id, 
                                lot_id, 
                                warehouse_id, 
                                location_id, 
                                quantity, 
                                uom_id, 
                                create_date, 
                                create_uid, 
                                write_uid, 
                                write_date, total_value)
                            SELECT 
                                (%d) AS inventory_id, 
                                pp.id AS product_id, 
                                pt.categ_id AS categ_id,
                                co.id AS company_id, 
                                spl.id AS lot_id, 
                                sw.id AS warehouse_id, 
                                d.id AS location_id,
                                SUM(quantity) AS quantity, 
                                u.id AS uom_id, 
                                now() AS create_date,
                                (%d) AS create_uid, 
                                (%d) AS write_uid, 
                                now() AS write_date,
                                (CASE 
                                    WHEN((
                                        SELECT ir_p.value_text
                                        FROM ir_property ir_p
                                        WHERE ir_p.name = 'property_cost_method'
                                            AND ir_p.company_id = co.id
                                         AND ir_p.res_id = concat('product.category,', pt.categ_id)) <> 'fifo')
                                    THEN (( SELECT ir_p.value_float
                                            FROM ir_property ir_p
                                            WHERE ir_p.name = 'standard_price'
                                                AND ir_p.company_id = co.id
                                                AND ir_p.res_id = concat('product.product,', pp.id)) * sum(quantity))
                                    ELSE
                                     (SELECT sum(sm.remaining_value)
                                        FROM stock_move sm
                                        WHERE sm.location_dest_id = d.id
                                            AND sm.product_id = pp.id
                                        GROUP BY sm.product_id)
                                END) AS total_value
                            FROM stock_quant quant
                                JOIN product_product pp ON quant.product_id = pp.id
                                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                JOIN uom_uom u ON u.id = pt.uom_id
                                LEFT JOIN stock_production_lot spl ON spl.id = quant.lot_id
                                INNER JOIN stock_location d ON quant.location_id = d.id
                                INNER JOIN stock_warehouse sw ON d.location_id = sw.view_location_id
                                INNER JOIN res_company co ON sw.company_id = co.id
                                AND d.id = %d
                            GROUP BY pp.id, co.id, spl.id, sw.id, u.id, pt.categ_id, d.id
                            ORDER BY pp.id
                        '''

                        # print(sql % (self.id, self.env.user.id, self.env.user.id, location))
                        self._cr.execute(sql % (self.id, self.env.user.id, self.env.user.id, location))

        pivot_view_id = self.env.ref('izi_stock_report.view_inventory_value_report_pivot').id

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'pivot',
            'name': _('Inventory value report'),
            'res_id': False,
            'res_model': 'stock.report.inventory.value.line',
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
        Description: - Lấy dữ liệu từ bảng tạm ra.
                     - Trả về 1 list gồm:
                        + Các param
                        + 1 đường link để xem trực tiếp trên web
                        + 1 đường link để xuất ra file excel
        Date: 8/4/2019
    """
    @api.multi
    def get_data_inventory_value(self):
        self.ensure_one()
        # Description: Xóa bản ghi cũ đi, để đỡ bị đầy database khi ấn nút
        self._cr.execute('''DELETE FROM stock_report_inventory_value_line WHERE inventory_id = %s''', (self.id-1,))

        list_location = []
        if len(self.location_ids) >=1:
            for location_parent in self.location_ids:
                list_location.append(location_parent.id)
        else:
            obj_location= self.env['stock.location'].search([('branch_id', '=', self.warehouse_id.branch_id.id), ('active', '=', 't')])
            if len(obj_location) >=1:
                for i in obj_location:
                    list_location.append(i.id)
        if len(list_location) >=1:
            for location in list_location:
                locations = self._list_location(location, [location])
                if len(locations)>=1:
                    for location in locations:
                        sql = '''
                                INSERT INTO stock_report_inventory_value_line(
                                    inventory_id, 
                                    product_id, 
                                    categ_id, 
                                    company_id, 
                                    lot_id,
                                    warehouse_id, 
                                    location_id, 
                                    quantity, 
                                    uom_id, 
                                    create_date, 
                                    create_uid, 
                                    write_uid, 
                                    write_date, 
                                    total_value)
                                SELECT 
                                    (%d) AS inventory_id, 
                                    pp.id AS product_id, 
                                    pt.categ_id AS categ_id,
                                    co.id AS company_id, 
                                    spl.id AS lot_id, 
                                    sw.id AS warehouse_id, 
                                    d.id AS location_id,
                                    SUM(quantity) AS quantity, 
                                    u.id AS uom_id, 
                                    now() AS create_date,
                                    (%d) AS create_uid, 
                                    (%d) AS write_uid, 
                                    now() AS write_date,
                                    (CASE 
                                        WHEN((
                                            SELECT ir_p.value_text
                                            FROM ir_property ir_p
                                            WHERE ir_p.name = 'property_cost_method'
                                                AND ir_p.company_id = co.id
                                                AND ir_p.res_id = concat('product.category,', pt.categ_id)) <> 'fifo')
                                        THEN (( SELECT ir_p.value_float
                                                FROM ir_property ir_p
                                                WHERE ir_p.name = 'standard_price'
                                                    AND ir_p.company_id = co.id
                                                    AND ir_p.res_id = concat('product.product,', pp.id)) * sum(quantity))
                                        ELSE
                                         (SELECT sum(sm.remaining_value)
                                            FROM stock_move sm
                                            WHERE sm.location_dest_id = d.id
                                                AND sm.product_id = pp.id
                                            GROUP BY sm.product_id)
                                    END) AS total_value
                                FROM stock_quant quant
                                    JOIN product_product pp ON quant.product_id = pp.id
                                    JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                    JOIN uom_uom u ON u.id = pt.uom_id
                                    LEFT JOIN stock_production_lot spl ON spl.id = quant.lot_id
                                    INNER JOIN stock_location d ON quant.location_id = d.id
                                    INNER JOIN stock_warehouse sw ON d.location_id = sw.view_location_id
                                    INNER JOIN res_company co ON sw.company_id = co.id
                                    AND d.id = %d
                                GROUP BY pp.id, co.id, spl.id, sw.id, u.id, pt.categ_id, d.id
                                ORDER BY pp.id
                        '''
                        self._cr.execute(sql % (self.id, self.env.user.id, self.env.user.id, location))

        birt_datasource = config['birt_datasource'] or '0'
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise ValidationError("You must config birt_url in file config")
        if birt_datasource == '0':
            raise ValidationError("You must config birt_datasource in file config")

        report_name = "rpt_stock_inventory_value.rptdesign"

        # cho toan bo id cua location vao trong 1 string ngan cach boi dau phay
        location = '0'
        if len(self.location_ids) != 0:
            for line in self.location_ids:
                location += ',' + str(line.id)

        # Truyền params nên có dấu & đằng trước key để truyền thẳng giá trị vào đường link birt
        params = {
            '&database_url': birt_datasource + self.pool._db.dsn['database'],
            '&location_id': location,
            '&warehouse_id': str(self.warehouse_id.id),
        }
        birt_link = birt_url + report_name
        birt_link_excel = birt_url + report_name + '&__format=xlsx'
        return [birt_link, birt_link_excel, params]

    """
        Author: HoiHD
        Description: Xuất báo cáo và xem trên web
        Date: 20/05/2019 on 9:46 AM
    """
    @api.multi
    def view_report_on_web(self):
        self.get_data_inventory_value()
        return {
            "type": "ir.actions.client",
            'name': 'WH Document',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': self.get_data_inventory_value()[0],
                'payload_data': self.get_data_inventory_value()[2],
            }
        }

    """ 
        Author: HoiHD
        Description: Xuất báo cáo ra file excel
        Date: 20/05/2019 on 9:46 AM
    """
    @api.multi
    def export_report_to_excel(self):
        self.get_data_inventory_value()
        return {
            "type": "ir.actions.client",
            'name': 'WH Document',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': self.get_data_inventory_value()[1],
                'payload_data': self.get_data_inventory_value()[2],
            }
        }
    # end by HoiHD


class StockReportInventoryValueLine(models.TransientModel):
    _name = 'stock.report.inventory.value.line'

    inventory_id = fields.Many2one('stock.report.inventory.value','Inventory')
    product_id = fields.Many2one('product.product','Product')
    categ_id = fields.Many2one('product.category','Category')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    location_id = fields.Many2one('stock.location', 'Location')
    quantity = fields.Float('Quantity')
    total_value = fields.Float('Value total')
    uom_id = fields.Many2one('uom.uom', "Product Uom")
    company_id = fields.Many2one('res.company', 'Company')
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial')