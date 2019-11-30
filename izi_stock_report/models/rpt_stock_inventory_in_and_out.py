# -*- coding: utf-8 -*-

import odoo.tools.config as config
from odoo import models, fields, api,_
import datetime
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
from xlwt.Utils import rowcol_to_cell
from xlwt import Formula
from datetime import timedelta, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT


class StockReportIOInventoryReport(models.TransientModel):
    _name = 'stock.report.io.inventory.report'

    name = fields.Char(string='General Account of Input - Output - Inventory')
    all = fields.Boolean('All')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    view_location_id = fields.Many2one('stock.location', 'View Location', related='warehouse_id.view_location_id', store=False)
    location_ids = fields.Many2many('stock.location', string='Locations')

    from_date = fields.Date('From date', default=lambda self: fields.Date.today())
    to_date = fields.Date('To date',   default=lambda self: fields.Date.today())
    get_product_transaction = fields.Boolean('Get only product with the transaction', default=False)
    by_day = fields.Boolean('By date', default=False)

    # @api.multi
    # def action_print(self):
    #     self.open_table()
    #     wb = xlwt.Workbook(encoding="UTF-8")
    #     date_str = str(datetime.today().date())
    #     obj_location = self.env['stock.report.io.inventory.report.line'].search([])
    #     list = []
    #     for line in obj_location:
    #         if line.location_id not in list:
    #             list.append(line.location_id)
    #     editable = xlwt.easyxf("protection: cell_locked false;")
    #     ws = wb.add_sheet("Xuất nhập tồn")
    #     style = xlwt.XFStyle()
    #     style.num_format_str = '#,##0'
    #     ws.col(0).width = 10 * 250
    #     ws.col(1).width = 10 * 380
    #     ws.col(2).width = 10 * 1000
    #     ws.col(3).width = 3000
    #     ws.col(4).width = 3000
    #     ws.col(5).width = 10 * 250
    #     ws.write(0, 0, u'STT')
    #     ws.write(0, 1, u'Mã SP')
    #     ws.write(0, 2, u"Tên SP")
    #     ws.write(0, 3, u"Tên Lô")
    #     ws.write(0, 4, u"Đơn vị")
    #     ws.write(0, 5, u"Giá bán")
    #
    #     style_numb = xlwt.easyxf('align: horiz right;', num_format_str='#,#')
    #
    #     # Lấy dữ liệu
    #     line_ids = self.env['stock.report.io.inventory.report.line'].search([
    #         ('in_out_inventory_id', '=', self.id),
    #     ])
    #     # Đưa dữ liệu Kho - SL vào dict để lấy số lượng tồn theo kho
    #     invent_dict = {}
    #     new_invent_list = []
    #     for line in line_ids:
    #         pid = '%s' % line.product_id.id
    #         loc_id = '%s' % line.location_id.id
    #         if pid not in invent_dict:
    #             new_invent_list.append(line)
    #             invent_dict[pid] = {
    #                 loc_id: {
    #                     'opening_stock': 0,
    #                     'closing_stock': 0,
    #                     'in_inventory': 0,
    #                     'out_inventory': 0
    #                 }
    #             }
    #         if loc_id not in invent_dict[pid]:
    #             invent_dict[pid][loc_id] = {
    #                 'opening_stock': 0,
    #                 'closing_stock': 0,
    #                 'in_inventory': 0,
    #                 'out_inventory': 0
    #             }
    #         invent_dict[pid][loc_id]['opening_stock'] += line.opening_stock
    #         invent_dict[pid][loc_id]['closing_stock'] += line.closing_stock
    #         invent_dict[pid][loc_id]['in_inventory'] += line.in_inventory
    #         invent_dict[pid][loc_id]['out_inventory'] += line.out_inventory
    #
    #     # Tên kho
    #     ws.write_merge(0, 0, 6, len(list) * 4 + 5, self.warehouse_id.name)
    #     # Chỉ mục cột đầu tiên tách dữ liệu giữa các kho
    #     wh_col_index = 6
    #     wh_col_current = wh_col_index
    #     wh_step = 4
    #     # Cột cho mỗi kho cần xuất
    #     for location in list:
    #         ws.write_merge(1, 1, wh_col_current, wh_col_current + wh_step - 1, location.name)
    #         ws.write(2, wh_col_current, u"SL tồn đầu kỳ")
    #         ws.write(3, wh_col_current, Formula("SUM(%s:%s)" % (
    #         rowcol_to_cell(4, wh_col_current), rowcol_to_cell(len(new_invent_list) + 3, wh_col_current))),
    #                  style=style_numb)
    #         ws.write(2, wh_col_current + 1, u"SL nhập trong kỳ")
    #         ws.write(3, wh_col_current + 1, Formula("SUM(%s:%s)" % (
    #         rowcol_to_cell(4, wh_col_current + 1), rowcol_to_cell(len(new_invent_list) + 3, wh_col_current + 1))),
    #                  style=style_numb)
    #         ws.write(2, wh_col_current + 3, u"SL xuất trong kỳ")
    #         ws.write(3, wh_col_current + 3, Formula("SUM(%s:%s)" % (
    #         rowcol_to_cell(4, wh_col_current + 3), rowcol_to_cell(len(new_invent_list) + 3, wh_col_current + 2))),
    #                  style=style_numb)
    #         ws.write(2, wh_col_current + 2, u"SL tồn cuối kỳ")
    #         ws.write(3, wh_col_current + 2, Formula("SUM(%s:%s)" % (
    #             rowcol_to_cell(4, wh_col_current + 2), rowcol_to_cell(len(new_invent_list) + 3, wh_col_current + 3))),
    #                  style=style_numb)
    #
    #         wh_col_current += wh_step
    #
    #     ws.write_merge(3, 3, 0, 5, u"Tổng")
    #
    #     index = 4
    #     for line in new_invent_list:
    #         pid = '%s' % line.product_id.id
    #         ws.write(index, 0, index - 3, editable)
    #         ws.write(index, 1, line.product_id.default_code, editable)
    #         ws.write(index, 2, line.product_id.name, editable)
    #         ws.write(index, 3, line.lot_id.name or '', editable)
    #         ws.write(index, 4, line.uom_id.name, editable)
    #         ws.write(index, 5, line.product_id.lst_price, style=style)
    #         # Đổ dữ liệu trên từng kho
    #         wh_col_index_current = 6
    #         for location in list:
    #             loc_id = '%s' % location.id
    #             if loc_id in invent_dict[pid]:
    #                 ws.write(index, wh_col_index_current, invent_dict[pid][loc_id]['opening_stock'], style_numb)
    #                 ws.write(index, wh_col_index_current + 1, invent_dict[pid][loc_id]['in_inventory'], style_numb)
    #                 ws.write(index, wh_col_index_current + 2, invent_dict[pid][loc_id]['out_inventory'], style_numb)
    #                 ws.write(index, wh_col_index_current + 3, invent_dict[pid][loc_id]['closing_stock'], style_numb)
    #             wh_col_index_current += wh_step
    #         index += 1
    #
    #     stream = stringIOModule.BytesIO()
    #     wb.save(stream)
    #     xls = stream.getvalue()
    #     vals = {
    #         'name': date_str + '.xls',
    #         'datas': base64.b64encode(xls),
    #         'datas_fname': date_str + '.xls',
    #         'type': 'binary',
    #         'res_model': 'stock.report.io.inventory.report',
    #         'res_id': self.id,
    #     }
    #     file_xls = self.env['ir.attachment'].create(vals)
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': '/web/content/' + str(file_xls.id) + '?download=true',
    #         'target': 'new',
    #     }

    def open_table(self):
        self.ensure_one()
        # Xoá bản ghi báo cáo cũ đã xuất ở phiếu xuất hiện tại
        self._cr.execute('''delete from stock_report_io_inventory_report_line where in_out_inventory_id=%s''', (self.id-1,))
        if self.from_date > self.to_date:
            raise except_orm(_('Thông báo'), _('Bạn đang chọn điều kiện ngày không đúng.'))
        date_time_from_str = self.from_date.strftime(DEFAULT_SERVER_DATE_FORMAT + ' 23:59:59')
        date_time_from = datetime.strptime(date_time_from_str, DEFAULT_SERVER_DATETIME_FORMAT)
        date_time_to_str = self.to_date.strftime(DEFAULT_SERVER_DATE_FORMAT + ' 23:59:59')
        date_time_to = datetime.strptime(date_time_to_str, DEFAULT_SERVER_DATETIME_FORMAT)

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
                for location_id in locations:
                    sql = """
                        INSERT INTO stock_report_io_inventory_report_line(
                          in_out_inventory_id, warehouse_id, location_id, 
                          create_date, create_uid, write_uid, 
                          write_date, product_id, lot_id,uom_id, opening_stock, 
                          out_inventory, in_inventory, closing_stock
                        ) 
                        SELECT 
                          (%d) as in_out_inventory_id, 
                          (%d) as warehouse_id, 
                          (%d) as location_id, 
                          now() as create_date, 
                          (%d) as create_uid, 
                          (%d) as write_uid, 
                          now() as write_date, 
                          (
                            CASE WHEN(dau_ky.product_id is not null) THEN dau_ky.product_id WHEN(xuat_kho.product_id is not null) THEN xuat_kho.product_id ELSE nhap_kho.product_id END
                          ) product_id, 
                          (
                            CASE WHEN(dau_ky.product_id is not null) THEN dau_ky.lot_id WHEN(xuat_kho.product_id is not null) THEN xuat_kho.lot_id ELSE nhap_kho.lot_id END
                          ) lot_id, 
                          (
                            CASE WHEN(dau_ky.product_id is not null) THEN dau_ky.uom_id WHEN(xuat_kho.product_id is not null) THEN xuat_kho.uom_id ELSE nhap_kho.uom_id END
                          ) uom_id
                          ,
                          (
                            case when(dau_ky.ton_kho_dau_ky is null) then 0 else dau_ky.ton_kho_dau_ky end
                          ) dau_ky, 
                          (
                            case when(xuat_kho.quantity is null) then 0 else xuat_kho.quantity end
                          ) xuat, 
                          (
                            case when(nhap_kho.quantity is null) then 0 else nhap_kho.quantity end
                          ) nhap, 
                          (
                            (
                              case when(dau_ky.ton_kho_dau_ky is null) then 0 else dau_ky.ton_kho_dau_ky end
                            ) - (
                              case when(xuat_kho.quantity is null) then 0 else xuat_kho.quantity end
                            ) + (
                              case when(nhap_kho.quantity is null) then 0 else nhap_kho.quantity end
                            )
                          ) cuoi_ky -----Hien Thi
                        FROM 
                          ---Bang
                          (
                            SELECT 
                              product_id, 
                              lot_id, 
                              uom_id,
                              sum(ton_kho_dau_ky) ton_kho_dau_ky 
                            FROM 
                              (
                                SELECT 
                                  (
                                    CASE WHEN(xuat_kho.product_id is not null) THEN xuat_kho.product_id ELSE nhap_kho.product_id END
                                  ) product_id,
                                  (
                                    CASE WHEN(xuat_kho.product_id is not null) THEN xuat_kho.lot_id ELSE nhap_kho.lot_id END
                                  ) lot_id, 
                                  (
                                    CASE WHEN(xuat_kho.product_id is not null) THEN xuat_kho.uom_id ELSE nhap_kho.uom_id END
                                  ) uom_id,
                                  (
                                    - (
                                      case when (xuat_kho.quantity is null) then 0 else xuat_kho.quantity end
                                    ) + (
                                      case when (nhap_kho.quantity is null) then 0 else nhap_kho.quantity end
                                    )
                                  ) ton_kho_dau_ky 
                                FROM 
                                (
                                    select 
                                      sm.product_id product_id, 
                                      sum(sm.product_qty) quantity, 
                                      sml.lot_id lot_id,
                                      pt.uom_id
                                    from 
                                      stock_move_line sml
                                      left join stock_move sm on sm.id = sml.move_id
                                      inner join product_product pp on pp.id = sml.product_id
                                      inner join product_template pt on pt.id = pp.product_tmpl_id 
                                    where 
                                      sm.date + INTERVAL '7 hour' <= '%s' 
                                      and sml.location_id = %d 
                                      and sm.state = 'done' 
                                    GROUP BY 
                                      sm.product_id, 
                                      sml.lot_id,pt.uom_id
                                  ) xuat_kho FULL
                                  OUTER JOIN (
                                    select 
                                      sm.product_id product_id, 
                                      sum(sm.product_qty) quantity, 
                                      sml.lot_id lot_id , pt.uom_id
                                    from 
                                      stock_move_line sml
                                      left join stock_move sm on sm.id = sml.move_id 
                                      inner join product_product pp on pp.id = sml.product_id
                                      inner join product_template pt on pt.id = pp.product_tmpl_id 
                                    where 
                                      sm.date + INTERVAL '7 hour' <= '%s' 
                                      and sml.location_dest_id = %d 
                                      and sm.state = 'done' 
                                    GROUP BY 
                                      sm.product_id, 
                                      sml.lot_id, pt.uom_id
                                  ) nhap_kho ON xuat_kho.product_id = nhap_kho.product_id
                              ) a 
                            GROUP BY 
                              product_id, 
                              lot_id, uom_id
                          ) dau_ky FULL 
                          OUTER JOIN ---XuatKho
                          (
                            select 
                              sm.product_id product_id, 
                              sum(sm.product_qty) quantity,
                              sml.lot_id lot_id,
                              pt.uom_id uom_id
                            from 
                              stock_move_line sml 
                              left join stock_move sm on sm.id = sml.move_id 
                              inner join product_product pp on pp.id = sml.product_id
                              inner join product_template pt on pt.id = pp.product_tmpl_id 
                            where 
                              sm.date + INTERVAL '7 hour' > '%s' 
                              and sm.date + INTERVAL '7 hour' <= '%s' 
                              AND sml.location_id = %d 
                              and sm.state = 'done' 
                            GROUP BY 
                              sm.product_id, 
                              sml.lot_id, pt.uom_id
                          ) xuat_kho ON dau_ky.lot_id = xuat_kho.lot_id FULL 
                          OUTER JOIN ---Nhap Kho
                          (
                            select 
                              sm.product_id product_id, 
                              sum(sm.product_qty) quantity, pt.uom_id,
                              sml.lot_id lot_id 
                            from 
                              stock_move_line sml 
                              left join stock_move sm on sm.id = sml.move_id
                              inner join product_product pp on pp.id = sml.product_id
                              inner join product_template pt on pt.id = pp.product_tmpl_id  
                            where 
                              sm.date + INTERVAL '7 hour' > '%s' 
                              and sm.date + INTERVAL '7 hour' <= '%s' 
                              AND sml.location_dest_id = %d 
                              and sm.state = 'done' 
                            GROUP BY 
                              sm.product_id, 
                              sml.lot_id, pt.uom_id
                          ) nhap_kho ON dau_ky.lot_id = nhap_kho.lot_id
                         """
                    print(sql % (self.id, self.warehouse_id.id, location_id, self.env.user.id, self.env.user.id,
                                            date_time_from, location_id,
                                            date_time_from, location_id,
                                            date_time_from, date_time_to,
                                            location_id, date_time_from, date_time_to, location_id))
                    self._cr.execute(sql % (self.id, self.warehouse_id.id, location_id, self.env.user.id, self.env.user.id,
                                            date_time_from, location_id,
                                            date_time_from, location_id,
                                            date_time_from, date_time_to,location_id,
                                            date_time_from, date_time_to,location_id))

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'pivot',
            'name': _('General Account of Input - Output - Inventory'),
            'res_id': False,
            'res_model': 'stock.report.io.inventory.report.line',
            'views': [(self.env.ref('izi_stock_report.stock_report_io_inventory_report_pivot').id, 'pivot')],
            'context': dict(self.env.context),
            'domain': [('in_out_inventory_id', '=', self.id)],
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
        Description: - Lấy ra dữ liệu xuất nhập tồn rồi đổ vào bảng tạm
                     - Hàm trả về 1 list gồm:
                            + các param
                            + 1 đường link để view on web
                            + 1 đường link để xuất báo cáo ra file excel
        Date: 20/05/2019 on 9:21 AM
    """
    @api.multi
    def get_data_inventory_in_and_out(self):
        self.ensure_one()
        # Xoá bản ghi báo cáo cũ đã xuất ở phiếu xuất hiện tại
        self._cr.execute('''delete from stock_report_io_inventory_report_line where in_out_inventory_id=%s''', (self.id-1,))
        if self.from_date > self.to_date:
            raise except_orm(_('Thông báo'), _('Bạn đang chọn điều kiện ngày không đúng.'))
        date_time_from_str = self.from_date.strftime(DEFAULT_SERVER_DATE_FORMAT + ' 23:59:59')
        date_time_from = datetime.strptime(date_time_from_str, DEFAULT_SERVER_DATETIME_FORMAT)
        date_time_to_str = self.to_date.strftime(DEFAULT_SERVER_DATE_FORMAT + ' 23:59:59')
        date_time_to = datetime.strptime(date_time_to_str, DEFAULT_SERVER_DATETIME_FORMAT)
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
                for location_id in locations:
                    sql = """
                                INSERT INTO stock_report_io_inventory_report_line(
                                  in_out_inventory_id, warehouse_id, location_id, 
                                  create_date, create_uid, write_uid, 
                                  write_date, product_id, lot_id,uom_id, opening_stock, 
                                  out_inventory, in_inventory, closing_stock
                                ) 
                                SELECT 
                                  (%d) as in_out_inventory_id, 
                                  (%d) as warehouse_id, 
                                  (%d) as location_id, 
                                  now() as create_date, 
                                  (%d) as create_uid, 
                                  (%d) as write_uid, 
                                  now() as write_date, 
                                  (
                                    CASE WHEN(dau_ky.product_id is not null) THEN dau_ky.product_id WHEN(xuat_kho.product_id is not null) THEN xuat_kho.product_id ELSE nhap_kho.product_id END
                                  ) product_id, 
                                  (
                                    CASE WHEN(dau_ky.product_id is not null) THEN dau_ky.lot_id WHEN(xuat_kho.product_id is not null) THEN xuat_kho.lot_id ELSE nhap_kho.lot_id END
                                  ) lot_id, 
                                  (
                                    CASE WHEN(dau_ky.product_id is not null) THEN dau_ky.uom_id WHEN(xuat_kho.product_id is not null) THEN xuat_kho.uom_id ELSE nhap_kho.uom_id END
                                  ) uom_id
                                  ,
                                  (
                                    case when(dau_ky.ton_kho_dau_ky is null) then 0 else dau_ky.ton_kho_dau_ky end
                                  ) dau_ky, 
                                  (
                                    case when(xuat_kho.quantity is null) then 0 else xuat_kho.quantity end
                                  ) xuat, 
                                  (
                                    case when(nhap_kho.quantity is null) then 0 else nhap_kho.quantity end
                                  ) nhap, 
                                  (
                                    (
                                      case when(dau_ky.ton_kho_dau_ky is null) then 0 else dau_ky.ton_kho_dau_ky end
                                    ) - (
                                      case when(xuat_kho.quantity is null) then 0 else xuat_kho.quantity end
                                    ) + (
                                      case when(nhap_kho.quantity is null) then 0 else nhap_kho.quantity end
                                    )
                                  ) cuoi_ky -----Hien Thi
                                FROM 
                                  ---Bang
                                  (
                                    SELECT 
                                      product_id, 
                                      lot_id, 
                                      uom_id,
                                      sum(ton_kho_dau_ky) ton_kho_dau_ky 
                                    FROM 
                                      (
                                        SELECT 
                                          (
                                            CASE WHEN(xuat_kho.product_id is not null) THEN xuat_kho.product_id ELSE nhap_kho.product_id END
                                          ) product_id,
                                          (
                                            CASE WHEN(xuat_kho.product_id is not null) THEN xuat_kho.lot_id ELSE nhap_kho.lot_id END
                                          ) lot_id, 
                                          (
                                            CASE WHEN(xuat_kho.product_id is not null) THEN xuat_kho.uom_id ELSE nhap_kho.uom_id END
                                          ) uom_id,
                                          (
                                            - (
                                              case when (xuat_kho.quantity is null) then 0 else xuat_kho.quantity end
                                            ) + (
                                              case when (nhap_kho.quantity is null) then 0 else nhap_kho.quantity end
                                            )
                                          ) ton_kho_dau_ky 
                                        FROM 
                                        (
                                            select 
                                              sm.product_id product_id, 
                                              sum(sm.product_qty) quantity, 
                                              sml.lot_id lot_id,
                                              pt.uom_id
                                            from 
                                              stock_move_line sml
                                              left join stock_move sm on sm.id = sml.move_id
                                              inner join product_product pp on pp.id = sml.product_id
                                              inner join product_template pt on pt.id = pp.product_tmpl_id 
                                            where 
                                              sm.date + INTERVAL '7 hour' <= '%s' 
                                              and sml.location_id = %d 
                                              and sm.state = 'done' 
                                            GROUP BY 
                                              sm.product_id, 
                                              sml.lot_id,pt.uom_id
                                          ) xuat_kho FULL
                                          OUTER JOIN (
                                            select 
                                              sm.product_id product_id, 
                                              sum(sm.product_qty) quantity, 
                                              sml.lot_id lot_id , pt.uom_id
                                            from 
                                              stock_move_line sml
                                              left join stock_move sm on sm.id = sml.move_id 
                                              inner join product_product pp on pp.id = sml.product_id
                                              inner join product_template pt on pt.id = pp.product_tmpl_id 
                                            where 
                                              sm.date + INTERVAL '7 hour' <= '%s' 
                                              and sml.location_dest_id = %d 
                                              and sm.state = 'done' 
                                            GROUP BY 
                                              sm.product_id, 
                                              sml.lot_id, pt.uom_id
                                          ) nhap_kho ON xuat_kho.product_id = nhap_kho.product_id
                                      ) a 
                                    GROUP BY 
                                      product_id, 
                                      lot_id, uom_id
                                  ) dau_ky FULL 
                                  OUTER JOIN ---XuatKho
                                  (
                                    select 
                                      sm.product_id product_id, 
                                      sum(sm.product_qty) quantity,
                                      sml.lot_id lot_id,
                                      pt.uom_id uom_id
                                    from 
                                      stock_move_line sml 
                                      left join stock_move sm on sm.id = sml.move_id 
                                      inner join product_product pp on pp.id = sml.product_id
                                      inner join product_template pt on pt.id = pp.product_tmpl_id 
                                    where 
                                      sm.date + INTERVAL '7 hour' > '%s' 
                                      and sm.date + INTERVAL '7 hour' <= '%s' 
                                      AND sml.location_id = %d 
                                      and sm.state = 'done' 
                                    GROUP BY 
                                      sm.product_id, 
                                      sml.lot_id, pt.uom_id
                                  ) xuat_kho ON dau_ky.lot_id = xuat_kho.lot_id FULL 
                                  OUTER JOIN ---Nhap Kho
                                  (
                                    select 
                                      sm.product_id product_id, 
                                      sum(sm.product_qty) quantity, pt.uom_id,
                                      sml.lot_id lot_id 
                                    from 
                                      stock_move_line sml 
                                      left join stock_move sm on sm.id = sml.move_id
                                      inner join product_product pp on pp.id = sml.product_id
                                      inner join product_template pt on pt.id = pp.product_tmpl_id  
                                    where 
                                      sm.date + INTERVAL '7 hour' > '%s' 
                                      and sm.date + INTERVAL '7 hour' <= '%s' 
                                      AND sml.location_dest_id = %d 
                                      and sm.state = 'done' 
                                    GROUP BY 
                                      sm.product_id, 
                                      sml.lot_id, pt.uom_id
                                  ) nhap_kho ON dau_ky.lot_id = nhap_kho.lot_id
                                 """
                    self._cr.execute(sql % (self.id, self.warehouse_id.id, location_id, self.env.user.id, self.env.user.id,
                                            date_time_from, location_id,
                                            date_time_from, location_id,
                                            date_time_from, date_time_to, location_id,
                                            date_time_from, date_time_to, location_id))

        birt_datasource = config['birt_datasource'] or '0'
        db_user = config['db_user'] or '0'
        db_password = config['db_password'] or '0'
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise ValidationError("You must config birt_url in file config")
        if birt_datasource == '0':
            raise ValidationError("You must config birt_datasource in file config")

        report_name = "rpt_stock_inventory_in_and_out.rptdesign"

        # cho toan bo id cua location vao trong 1 string ngan cach boi dau phay
        location = '0'
        if len(self.location_ids) != 0:
            for line in self.location_ids:
                location += ',' + str(line.id)

        param_str = {
            '&database_url': birt_datasource + self.pool._db.dsn['database'],
            '&db_user': db_user,
            '&db_password': db_password,
            '&location_id': location,
            '&warehouse_id': str(self.warehouse_id.id),
            '&from_date': self.from_date.strftime("%d/%m/%Y"),
            '&to_date': self.to_date.strftime("%d/%m/%Y")
        }
        birt_link = birt_url + report_name
        birt_link_excel = birt_url + report_name + '&__format=xlsx'
        return [birt_link, birt_link_excel, param_str]

    """
        Author: HoiHD
        Description: Xuất báo cáo và xem trên web
        Date: 20/05/2019 on 9:46 AM
    """
    @api.multi
    def view_report_on_web(self):
        self.get_data_inventory_in_and_out()
        return {
            "type": "ir.actions.client",
            'name': 'WH Document',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': self.get_data_inventory_in_and_out()[0],
                'payload_data': self.get_data_inventory_in_and_out()[2],
            }
        }

    """ 
        Author: HoiHD
        Description: Xuất báo cáo ra file excel
        Date: 20/05/2019 on 9:46 AM
    """
    @api.multi
    def export_report_to_excel(self):
        self.get_data_inventory_in_and_out()
        return {
            "type": "ir.actions.client",
            'name': 'WH Document',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': self.get_data_inventory_in_and_out()[1],
                'payload_data': self.get_data_inventory_in_and_out()[2],
            }
        }
    # end Hợi HD


class StockReportIOInventoryReportLine(models.TransientModel):
    _name = 'stock.report.io.inventory.report.line'

    in_out_inventory_id = fields.Many2one('stock.report.io.inventory.report','In out inventory')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    location_id = fields.Many2one('stock.location', 'Location')
    product_id = fields.Many2one('product.product', string='Product')
    uom_id = fields.Many2one('uom.uom', string='Uom')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial')
    opening_stock = fields.Float('Opening stock', default=0)
    closing_stock = fields.Float('Closing stock',default=0)
    purchase_quantity = fields.Float('Purchase quantity',default=0)
    sale_quantity = fields.Float('Sale quantity',default=0)
    sale_refund = fields.Float('Sale refund',default=0)
    purchase_refund = fields.Float('Purchare refund',default=0)
    out_transfer = fields.Float('Out transfer',default=0)
    in_transfer = fields.Float('In transfer',default=0)
    out_inventory = fields.Float('Out inventory',default=0)
    in_inventory = fields.Float('In inventory',default=0)
