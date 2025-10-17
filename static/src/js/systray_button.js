/** @odoo-module **/

import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
import core from 'web.core';
import rpc from 'web.rpc';

const qweb = core.qweb;

const MySystrayButton = Widget.extend({
    template: 'rod_cooperativa.MySystrayButton',
    events: {
        'click .o_my_systray_button': '_onClick',
    },
    // --- Nuevo: usa sintaxis clásica (evita async/arrow aquí) ---
    init: function () {
        this._super.apply(this, arguments);
        this.counter = 0;
        this._tRefresh = null;
    },
    // --- Nuevo: usa sintaxis clásica y _super.apply ---
    start: function () {
        var self = this;
        // refresco inicial
        this._refreshCounter();
        // refresco periódico (60s). Puedes ajustar o quitar esto.
        this._tRefresh = window.setInterval(function () {
            self._refreshCounter();
        }, 5000);

        return this._super.apply(this, arguments);
    },
    // --- Nuevo: limpia el intervalo de forma segura ---
    destroy: function () {
        if (this._tRefresh) {
            clearInterval(this._tRefresh);
        }
        return this._super.apply(this, arguments);
    },

    _refreshCounter: function () {
        var self = this;
        return rpc.query({
            model: 'loan.payment',                 // <- ajusta si tu acción usa otro modelo
            method: 'search_count',
            args: [[['state', '=', 'not_discounted']]], // <- dominio de tu acción
        }).then(function (count) {
            self.counter = count || 0;
            var $b = self.$('.o_notification_counter');
            console.log("Contador actualizado a:", self.counter);
            if (self.counter > 0) {
                $b.text(self.counter).show();
            } else {
                $b.text('').hide();
            }
        }).guardedCatch(function () {
            // silencioso para no romper systray si el conteo falla
        });
    },

    _onClick(ev) {
        ev.preventDefault();
        this.do_action('rod_cooperativa.action_loan_payments_not_discounted', {
            clear_breadcrumbs: false,  // deja el rastro de navegación
        });
    },
});

// Registrar el widget para que aparezca en el systray (a la derecha)
SystrayMenu.Items.push(MySystrayButton);

export default MySystrayButton;
