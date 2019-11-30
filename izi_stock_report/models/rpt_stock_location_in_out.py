# -*- coding: utf-8 -*-
__author__ = 'HoiHD edited'
import odoo.tools.config as config
from odoo import models, fields, api, exceptions
from datetime import date
from calendar import monthrange


class RPTStockLocationInOut(models.TransientModel):
    _name = 'rpt.stock.location.in.out'
    _description = 'Báo cáo tồn kho'

    name = fields.Char(string='Báo cáo tồn kho')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    view_location_id = fields.Many2one('stock.location', 'View Location', related='warehouse_id.view_location_id', store=False)
    location_ids = fields.Many2many('stock.location', string='Locations')
    from_date = fields.Date('From date',
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    to_date = fields.Date('To date',
                          default=lambda self: fields.Date.to_string(date.today().replace(day=monthrange(date.today().year, date.today().month)[1])))
    line_ids = fields.One2many('rpt.stock.location.in.out.line', 'in_out_inventory_id', string='Lines')
    is_export_excel = fields.Boolean(default=False, string='Export to Excel')

    def _general_date(self):
        self.ensure_one()
        # Xoá dữ liệu cũ
        self._cr.execute('''delete from rpt_stock_location_in_out_line''')
        if self.from_date > self.to_date:
            raise exceptions.ValidationError('Bạn đang chọn điều kiện ngày không đúng!')
        date_time_from_str = self.from_date.strftime('%d/%m/%Y')
        date_time_to_str = self.to_date.strftime('%d/%m/%Y')
        date_time_from = "'" + date_time_from_str + "'"
        date_time_to = "'" + date_time_to_str + "'"
        obj_in_out_line = self.env['rpt.stock.location.in.out.line']
        if len(self.location_ids) >=1:
            for location_id in self.location_ids:
                sql = '''
                     SELECT
                            location_id,
                            product_id,
                            lot_id,
                            uom_id,
                            SUM (tondau) tondau,
                            SUM (xuatkho) xuatkho,
                            SUM (nhapkho) nhapkho,
                            SUM (toncuoi) toncuoi
                            FROM
                            (
                                -- tồn kho đầu kỳ 
                                SELECT
                                    location_id,
                                    product_id,
                                    lot_id,
                                    uom_id,
                                    SUM (nhapkho) - SUM (xuatkho) tondau,
                                    0 xuatkho,
                                    0 nhapkho,
                                    0 toncuoi
                                FROM
                                    (
                                        SELECT
                                            d. ID location_id,
                                            C . ID product_id,
                                            e. ID lot_id,
                                            f. ID uom_id,
                                            SUM (qty_done) xuatkho,
                                            0 nhapkho
                                        FROM
                                            stock_move_line A
                                        LEFT JOIN stock_move b ON b. ID = A .move_id
                                        LEFT JOIN product_product C ON C . ID = A .product_id
                                        LEFT JOIN stock_location d ON d. ID = A .location_id
                                        LEFT JOIN stock_production_lot e ON e. ID = A .lot_id
                                        LEFT JOIN uom_uom f ON f. ID = A .product_uom_id
                                        WHERE
                                            d. ID = %s and b.state = 'done' and C.active = 't'
                                        AND to_date(to_char(A.DATE + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') < to_date(''' + str(date_time_from) + ''','dd/mm/yyyy') 
                                        GROUP BY
                                            d. ID,
                                            C . ID,
                                            e. ID,
                                            f. ID
                                        UNION ALL
                                            SELECT
                                                d. ID location_id,
                                                C . ID product_id,
                                                e. ID lot_id,
                                                f. ID uom_id,
                                                0 xuatkho,
                                                SUM (qty_done) nhapkho
                                            FROM
                                                stock_move_line A
                                            LEFT JOIN stock_move b ON b. ID = A .move_id
                                            LEFT JOIN product_product C ON C . ID = A .product_id
                                            LEFT JOIN stock_location d ON d. ID = A .location_dest_id
                                            LEFT JOIN stock_production_lot e ON e. ID = A .lot_id
                                            LEFT JOIN uom_uom f ON f. ID = A .product_uom_id
                                            WHERE
                                                d. ID = %s and b.state = 'done' and C.active = 't'
                                            AND to_date(to_char(A.DATE + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') < to_date(''' + str(date_time_from) + ''','dd/mm/yyyy')
                                            GROUP BY
                                                d. ID,
                                                C . ID,
                                                e. ID,
                                                f. ID
                                    ) bang
                                GROUP BY
                                    location_id,
                                    product_id,
                                    lot_id,
                                    uom_id
                                UNION ALL
                                    --  xuất nhập kho trong kỳ
                                    SELECT
                                        location_id,
                                        product_id,
                                        lot_id,
                                        uom_id,
                                        0 tondau,
                                        SUM (xuatkho) xuatkho,
                                        SUM (nhapkho) nhapkho,
                                        0 toncuoi
                                    FROM
                                        (
                                            SELECT
                                                d. ID location_id,
                                                C . ID product_id,
                                                e. ID lot_id,
                                                f. ID uom_id,
                                                SUM (qty_done) xuatkho,
                                                0 nhapkho
                                            FROM
                                                stock_move_line A
                                            LEFT JOIN stock_move b ON b. ID = A .move_id
                                            LEFT JOIN product_product C ON C . ID = A .product_id
                                            LEFT JOIN stock_location d ON d. ID = A .location_id
                                            LEFT JOIN stock_production_lot e ON e. ID = A .lot_id
                                            LEFT JOIN uom_uom f ON f. ID = A .product_uom_id
                                            WHERE
                                                d. ID = %s and b.state = 'done' and C.active = 't'
                                            AND to_date(to_char(A.DATE + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') >= to_date(''' + str(date_time_from) + ''','dd/mm/yyyy')
                                            AND to_date(to_char(A.DATE + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date(''' + str(date_time_to) + ''','dd/mm/yyyy')
                                            GROUP BY
                                                d. ID,
                                                C . ID,
                                                e. ID,
                                                f. ID
                                            UNION ALL
                                                SELECT
                                                    d. ID location_id,
                                                    C . ID product_id,
                                                    e. ID lot_id,
                                                    f. ID uom_id,
                                                    0 xuatkho,
                                                    SUM (qty_done) nhapkho
                                                FROM
                                                    stock_move_line A
                                                LEFT JOIN stock_move b ON b. ID = A .move_id
                                                LEFT JOIN product_product C ON C . ID = A .product_id
                                                LEFT JOIN stock_location d ON d. ID = A .location_dest_id
                                                LEFT JOIN stock_production_lot e ON e. ID = A .lot_id
                                                LEFT JOIN uom_uom f ON f. ID = A .product_uom_id
                                                WHERE
                                                    d. ID = %s and b.state = 'done' and C.active = 't'
                                                AND to_date(to_char(A.DATE + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') >= to_date(''' + str(date_time_from) + ''','dd/mm/yyyy')
                                                AND to_date(to_char(A.DATE + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date(''' + str(date_time_to) + ''','dd/mm/yyyy')
                                                GROUP BY
                                                    d. ID,
                                                    C . ID,
                                                    e. ID,
                                                    f. ID
                                        ) bang
                                    GROUP BY
                                        location_id,
                                        product_id,
                                        lot_id,
                                        uom_id
                            
                                    UNION ALL
                                        -- tồn cuối kỳ
                                        SELECT
                                            location_id,
                                            product_id,
                                            lot_id,
                                            uom_id,
                                            0 tondau,
                                            0 xuatkho,
                                            0 nhapkho,
                                            SUM (nhapkho) - SUM (xuatkho) toncuoi
                                        FROM
                                            (
                                                SELECT
                                                    d. ID location_id,
                                                    C . ID product_id,
                                                    e. ID lot_id,
                                                    f. ID uom_id,
                                                    SUM (qty_done) xuatkho,
                                                    0 nhapkho
                                                FROM
                                                    stock_move_line A
                                                LEFT JOIN stock_move b ON b. ID = A .move_id
                                                LEFT JOIN product_product C ON C . ID = A .product_id
                                                LEFT JOIN stock_location d ON d. ID = A .location_id
                                                LEFT JOIN stock_production_lot e ON e. ID = A .lot_id
                                                LEFT JOIN uom_uom f ON f. ID = A .product_uom_id
                                                WHERE
                                                    d. ID =%s and b.state = 'done' and C.active = 't'
                                                AND to_date(to_char(A.DATE + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date(''' + str(date_time_to) + ''','dd/mm/yyyy')
                                                GROUP BY
                                                    d. ID,
                                                    C . ID ,
                                                    e. ID,
                                                    f. ID
                                                UNION ALL
                                                    SELECT
                                                        d. ID location_id,
                                                        C . ID product_id,
                                                        e. ID lot_id,
                                                        f. ID uom_id,
                                                        0 xuatkho,
                                                        SUM (qty_done) nhapkho
                                                    FROM
                                                        stock_move_line A
                                                    LEFT JOIN stock_move b ON b. ID = A .move_id
                                                    LEFT JOIN product_product C ON C . ID = A .product_id
                                                    LEFT JOIN stock_location d ON d. ID = A .location_dest_id
                                                    LEFT JOIN stock_production_lot e ON e. ID = A .lot_id
                                                    LEFT JOIN uom_uom f ON f. ID = A .product_uom_id
                                                    WHERE
                                                        d. ID = %s and b.state = 'done' and C.active = 't'
                                                    AND to_date(to_char(A.DATE + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date(''' + str(date_time_to) + ''','dd/mm/yyyy')
                                                    GROUP BY
                                                        d. ID,
                                                        C . ID,
                                                        e. ID,
                                                        f. ID
                                            ) bang
                                        GROUP BY
                                            location_id,
                                            product_id,
                                            lot_id,
                                            uom_id
                            ) bang_tong_hop
                            GROUP BY
                            location_id,
                            product_id,
                            lot_id,
                            uom_id
                            ORDER BY
                            location_id,
                            product_id
                                         '''
                self._cr.execute(sql, (location_id.id, location_id.id,
                                       location_id.id, location_id.id,
                                       location_id.id, location_id.id))
                lists = self._cr.dictfetchall()

                if len(lists) >= 1:
                    for i in lists:
                        obj_in_out_line.create({
                            'in_out_inventory_id': self.id,
                            'location_id': i['location_id'] and i['location_id'] or False,
                            'product_id': i['product_id'] and i['product_id'] or False,
                            'opening_location': i['tondau'] and i['tondau'] or False,
                            'closing_location': i['toncuoi'] and i['toncuoi'] or False,
                            'out_location': i['xuatkho'] and i['xuatkho'] or False,
                            'in_location': i['nhapkho'] and i['nhapkho'] or False,
                            'uom_id': i['uom_id'] and i['uom_id'] or False,
                            'lot_id': i['lot_id'] and i['lot_id'] or False,
                        })

    def _birt_name_param(self):
        name = 'KHO: '
        if self.location_ids:
            for loc in self.location_ids:
                name = name + str(loc.x_code) + ' - '
        else:
            name = 'KHO: ' + self.warehouse_id.name

        date_from = self.from_date.strftime('%d/%m/%Y')
        date_to = self.to_date.strftime('%d/%m/%Y')
        param_str = {
            '&from_date': date_from,
            '&to_date': date_to,
            '&name': name,
        }
        return param_str


    @api.multi
    def action_export_report(self):
        self._general_date()
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("Chưa cấu hình birt_url!")
        name = 'KHO: '
        if self.location_ids:
            for loc in self.location_ids:
                name = name + str(loc.x_code) + ' - '
        else:
            name = 'KHO: ' + self.warehouse_id.name

        report_name = "rpt_stock_location_in_out.rptdesign"
        param_str = {
            '&from_date': self.from_date.strftime('%d/%m/%Y'),
            '&to_date': self.to_date.strftime('%d/%m/%Y'),
            '&name': name
        }
        birt_link = birt_url + report_name
        if self.is_export_excel:
            birt_link += '&__format=xlsx'
        return {
            "type": "ir.actions.client",
            'name': 'Báo cáo tồn kho',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }


class RPTStockLocationInOutLine(models.TransientModel):
    _name = 'rpt.stock.location.in.out.line'

    in_out_inventory_id = fields.Many2one('rpt.stock.location.in.out','In/Out Location')
    location_id = fields.Many2one('stock.location', 'Location')
    product_id = fields.Many2one('product.product', string='Product')
    lot_id = fields.Many2one('stock.production.lot', string='Lot')
    uom_id = fields.Many2one('uom.uom', string='uom')
    opening_location = fields.Float('Opening Location', default=0)
    closing_location = fields.Float('Closing location',default=0)
    out_location = fields.Float('Out location',default=0)
    in_location = fields.Float('In location',default=0)
