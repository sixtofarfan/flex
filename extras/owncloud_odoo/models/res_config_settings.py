# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


PARAMS = [
    ("owncloud_url", str, ""),
    ("owncloud_login", str, ""),
    ("owncloud_password", str, ""),
    ("owncloud_root_dir", str, "Odoo"),
    ("owncloud_share_urls", safe_eval, "False"),
]


class res_config_settings(models.TransientModel):
    _inherit = "res.config.settings"

    owncloud_url = fields.Char(string="Url")
    owncloud_login = fields.Char(string="Login")
    owncloud_password = fields.Char(string="Password")
    owncloud_root_dir = fields.Char(string="Root Directory")
    owncloud_share_urls = fields.Boolean(
        string="Use Public URLs",
        help="""
            By default all links from Odoo to OwnCloud / NextCloud are internal. Only real users may access them
            and then generate a share urls for others.
            If this option is checked, links will become 'shared', meaning that everybody will be access those files
            by links. Although they would be hardly known by external users, there is a slight  chance that they become
            available as a result of some user actions. Besides, sharing links generation is not fast and might make
            a sync process slower.
        """,
    )

    @api.model
    def get_values(self):
        """
        Overwrite to add new system params
        """
        Config = self.env['ir.config_parameter'].sudo()
        res = super(res_config_settings, self).get_values()
        values = {}
        for field_name, getter, default in PARAMS:
            values[field_name] = getter(str(Config.get_param(field_name, default)))
        res.update(**values)
        return res

    def set_values(self):
        """
        Overwrite to add new system params
        """
        Config = self.env['ir.config_parameter'].sudo()
        super(res_config_settings, self).set_values()
        for field_name, getter, default in PARAMS:
            value = getattr(self, field_name, default)
            Config.set_param(field_name, value)

    def action_login_owncloud(self):
        """
        The method to authenticate to OwnCloud

        Methods:
         * _return_client_context of ir.attachment (it initiates OwnCloud Client)
         * action_confirm_owncloud

        Returns:
         * Updated config page if test is fine

        Raises:
         * UserError if test doesn't work

        Extra info:
         * We use _return_client_context of ir.attachment instead of a direct _get_client to pass certain ctx like
           s_logger
        """
        self.set_values()
        owncloud_ctx = self.env['ir.attachment'].with_context(no_ckeys=True)._return_client_context()
        if owncloud_ctx.get("client"):
            ctx = self._context.copy()
            ctx.update(owncloud_ctx)
            self.with_context(ctx).action_confirm_owncloud()
        else:
            raise UserError(_(u"Can't authenticate to OwnCloud! Please check your OwnCloud credentials!"))

    def action_confirm_owncloud(self):
        """
        The method to write a new state

        Methods:
         * _find_or_create_root_directory

        Returns:
         * Updated configs
        """
        self.env['ir.config_parameter'].set_param('cloud_client_state', 'confirmed')
        self.env["ir.attachment"].with_context(first_create=True)._find_or_create_root_directory()

    def action_reset(self):
        """
        The method to remove all data and objects related to owncloud

        Methods:
         * action_reset
        """
        super(res_config_settings, self).action_reset()
        params, _, _ = zip(*PARAMS)
        self._cr.execute('DELETE FROM ir_config_parameter WHERE key IN %s', (params,))
