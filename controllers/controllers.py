# -*- coding: utf-8 -*-
# from odoo import http


# class RodCooperativa(http.Controller):
#     @http.route('/rod_cooperativa/rod_cooperativa', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rod_cooperativa/rod_cooperativa/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rod_cooperativa.listing', {
#             'root': '/rod_cooperativa/rod_cooperativa',
#             'objects': http.request.env['rod_cooperativa.rod_cooperativa'].search([]),
#         })

#     @http.route('/rod_cooperativa/rod_cooperativa/objects/<model("rod_cooperativa.rod_cooperativa"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rod_cooperativa.object', {
#             'object': obj
#         })
