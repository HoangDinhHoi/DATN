odoo.define('widget_enter.widget', function(require) {
"use strict";

var core = require('web.core');
var AbstractField = require('web.AbstractField');
var basicFields = require('web.basic_fields');
var registry = require('web.field_registry');

var qweb = core.qweb;
var limit_enter_press = false;
var EnterToAction = basicFields.FieldChar.extend({
    _renderEdit: function () {
        var def = this._super.apply(this, arguments);
        var self = this;
        if (this.attrs.modifiers.action_element_class.length) {
            setTimeout(function(){
                var target = $(self.attrs.modifiers.action_element_class);
                self.$input.on('keypress', function(e){
                    if(e.which == 13) {
                        if (!limit_enter_press) {
                            limit_enter_press = true;
                            target.click();
                            setTimeout(function(){
                                limit_enter_press = false;
                            }, 2000);
                        }
                    }
                });
            }, 1000);
        }
        return def;
    },
});

registry.add('enter2action', EnterToAction);

});
