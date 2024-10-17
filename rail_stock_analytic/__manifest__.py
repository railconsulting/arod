
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Cuentas analiticas en stock",
    "summary": "Agrega lineas de distribucion analitica en las entregas",
    "version": "16.0.1.1.0",
    "author": "Rail/ Kevin Lopez",
    "website": "https://www.rail.com.mx",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": ["stock_account", "analytic"],
    "data": [
        "views/stock_move_views.xml",
        "views/stock_scrap_views.xml",
        "views/stock_move_line_views.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
}
