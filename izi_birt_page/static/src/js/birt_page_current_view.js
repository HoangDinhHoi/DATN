// Hợi HD: Hiển thị birt view thẳng trên popup
// Chú ý: Toàn bộ key của dict truyền vào cần có dấu & đằng trước và
// value của key đó phải là string
// trong return của file .py, thay đổi 'tag': 'BirtViewerActionCurrent'
odoo.define('izi_birt_page.BirtViewerActionCurrent', function (require) {
    "use strict";
    var core = require('web.core');
    var Widget = require('web.Widget');
    var AbstractAction = require('web.AbstractAction');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var BirtPage = AbstractAction.extend(ControlPanelMixin, {
        template: "BirtPageWidgetCurrent",
        init: function (parent, options) {
            this.birt_link = options.context.birt_link;
            this.payload_data = options.context.payload_data;

            // lấy đường link này để truyền thẳng vào trong iframe
            for(var key in this.payload_data){
                this.birt_link += (key + '=' + this.payload_data[key]);
            }

            this.target = options.target;
            if (!this.birt_link) {
                this.birt_link = localStorage['birt_link'] || '404';
            }
            else
                localStorage['birt_link'] = this.birt_link;
            return this._super(parent, options);
        },
        start: function () {
            // Dãn kích thước màn hình bao ngoài
            this.$el.css({height:"100%", width: "100%", margin: "auto", border: 0});
            // set 100 miliseconds để gọi hàm render, truyền vào tham số this
            this.intervalId = setInterval(this.render_options, 100, this);
        },
        // hàm render truyền vào tham số parent tương ứng với tham số this bên trên
        render_options: function (parent) {
            // kiểm tra xem có popup được bung ra không,
            if (parent.target !== 'self'){
                // xóa việc kiểm tra
                clearInterval(parent.intervalId);
                return; }

            // var modalForm = $('.modal-dialog.modal-lg');
            // // kiểm tra xem có popup bung ra không
            // if(!modalForm.length){
            //     return;
            // }
            // // nếu thấy popup được bung ra thì xóa việc kiểm tra
            // clearInterval(parent.intervalId);
            // // set kích thước của popup
            // modalForm.css({
            //     "transition": 'all 1s linear',
            //     "width": "100%",
            //     "max-width": "100%",
            //     "height": "100%",
            //     "max-height": "100%",
            // });
            //
            // $('.modal-content').css({
            //     "width": "100%",
            //     "max-width": "100%",
            //     "height": "100%",
            //     "max-height": "100%",
            // });
        }
    });
    core.action_registry.add('BirtViewerActionCurrent', BirtPage);
});

