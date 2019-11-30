odoo.define('izi_birt_page.BirtViewerAction', function (require) {
    "use strict";
    var core = require('web.core');
    var Widget = require('web.Widget');
    var AbstractAction = require('web.AbstractAction');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var BirtPage = AbstractAction.extend(ControlPanelMixin, {
        template: "BirtPageWidget",
        init: function (parent, options) {
            this.new_link = null; // new
            this.birt_link = options.context.birt_link;
            this.payload_data = options.context.payload_data;
            this.target = options.target;
            if (!this.birt_link) {
                this.birt_link = localStorage['birt_link'] || '404';
            }
            else
                localStorage['birt_link'] = this.birt_link;
            if (options.context.options) {
                this.display_options = options.context.options;
            }
            return this._super(parent, options);
        },
        start: function () {
            this.render_options();
        },
        render_options: function () {
            if (this.target !== 'new'){ return; }

            function post(path, params, method) {
                method = method || "post";
                var form = document.createElement("form");
                form.setAttribute("method", method);
                form.setAttribute("action", path);
                form.setAttribute("target", "_blank");
                for (var key in params) {
                    if (params.hasOwnProperty(key)) {
                        var hiddenField = document.createElement("input");
                        hiddenField.setAttribute("type", "hidden");
                        hiddenField.setAttribute("name", key);
                        hiddenField.setAttribute("value", params[key]);
                        form.appendChild(hiddenField);
                    }
                }
                document.body.appendChild(form);
                form.submit();
            }
            if (this.payload_data) {
                // new
                post(this.birt_link, this.payload_data);
            }
            else {
                // new
                post(this.birt_link, {});
            }
        }
    });
    core.action_registry.add('BirtViewerAction', BirtPage);
});

