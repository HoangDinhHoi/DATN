
odoo.define('izi_message_dialog.ActionManager', function (require) {
    "use strict";

    var ActionManager = require('web.ActionManager');

    ActionManager.include({

        _executeActionInDialog: function(action, options){
            options['izi_dialog'] = action.context.izi_dialog;
            options['izi_type'] = action.context.izi_type;
            options['izi_show_close_button'] = action.context.izi_show_close_button;
            return this._super(action, options);
        }

    });

});