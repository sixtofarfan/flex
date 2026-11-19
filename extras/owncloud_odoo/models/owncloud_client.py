# -*- coding: utf-8 -*-

import logging

from odoo import models

from ..libs.owncloud_service import PatchedClient as OwncloudClient

_logger = logging.getLogger(__name__)


class owncloud_client(models.AbstractModel):
    """
    The wrapper model for Python OwnCloud library. It is used only for authentication purposes
    All sync methods are done within ir.attachment model, which directly apply to Client API
    """
    _name = "owncloud.client"
    _description = "OwnCloud Client"

    def _get_client(self):
        """
        Method to return instance of wrapped OwnCloud Instance

        Returns:
         * OwnCloud instance if initiated
         * False otherwise
        """
        Config = self.env['ir.config_parameter'].sudo()
        url = Config.get_param('owncloud_url', '')
        login = Config.get_param('owncloud_login', '')
        password = Config.get_param('owncloud_password', '')
        try:
            res = OwncloudClient(url)
            res.login(login, password)
        except Exception as error:
            res = False
            _logger.error(u"OwnCloud can't be initiated. Reason: {}".format(error))
        return res
