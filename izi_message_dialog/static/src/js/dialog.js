odoo.define('izi_message_dialog.dialog', function(require) {
    "use strict";

    var Dialog = require('web.Dialog');

    Dialog.include({
        izi_dialog: false,
        izi_type: 'info',
        init: function (parent, options) {
            this.izi_dialog = options.izi_dialog || this.izi_dialog;
            this.izi_type = options.izi_type || this.izi_type;
            this.izi_show_close_button = options.izi_show_close_button || this.izi_show_close_button;
            this._super.apply(this, arguments);
        },
        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if(self.izi_dialog == true){
                    self.$modal.find(".modal-header").addClass("modal-header--" + self.izi_type);
                    $(self.renderModalIconType(self.izi_type)).insertBefore(self.$modal.find(".modal-title"));
                    self.$modal.find(".modal-footer").remove();
                }
                if(self.izi_show_close_button){
                    self.$modal.find(".modal-header button.close").css({'visibility': 'hidden'});
                }
            });
        },
        renderModalIconType: function(type){
            switch (type) {
                case 'warning':
                    return '<p class="modal-icon"><i class="fas fa-exclamation-triangle"></i></p>';
                case 'error':
                    return '<p class="modal-icon"><i class="fas fa-exclamation-circle"></i></p>';
                default:
                    return '<p class="modal-icon"><i class="fas fa-info-circle"></i></p>';
            }
        }

    })

});