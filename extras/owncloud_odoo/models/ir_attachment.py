# -*- coding: utf-8 -*-

import base64

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


def build_path(components):
    """
    The method construct path

    Args:
     * components - list of elements like 'Odoo' & 'Contacts' or 'Odoo/Contacts' & 'Agrolait'
    """
    path = u"/".join(components)
    path.replace("//", "/")
    return path

class ir_attachment(models.Model):
    """
    Re-writting the model to introduce OwnCloud specific methods

    Extra info:
     * althoug all OwnCloud method rely upon path we hack it with passing list of all pairs id -- path
       That's everywhere we do not care of pathes, but often put obsolete data to avoid excess requests
    """
    _inherit = "ir.attachment"

    cloud_key = fields.Char(string="OwnCloud ID") #just to rename the field

    @api.model
    def open_cloud_folder(self, args):
        """
        Re-write not to invoke ckeys immediately
        """
        return super(ir_attachment, self.with_context(no_ckeys=True)).open_cloud_folder(args=args)

    @api.model
    def _file_read(self, fname, bin_size=False, attach_cloud_id=False):
        """
        Re-write not to invoke ckeys immediately
        """
        return super(ir_attachment, self.with_context(no_ckeys=True))._file_read(
            fname=fname,
            bin_size=bin_size,
            attach_cloud_id=attach_cloud_id,
        )

    @api.model
    def _return_client_context(self):
        """
        The method to return necessary to client context (like session, root directory, etc.)
        Also we construct here a dict of correspondance id <--> path

        1. [IMPORTANT]
           List_o doesn't work properly with depth > 1 in OwnCloud.
           Look at the issue: https://github.com/owncloud/core/issues/28341
           However, for NextCloud it works. So, we just compare dict len vs list len
           When it is fixed in OwnCloud, it would be automatically applied here (although one excess request)

        Methods:
         * _get_client of owncloud.client
         * _find_or_create_root_directory
         * list_o of OwnCloud Client

        Returns:
         * dict
        """
        with_context_dict = super(ir_attachment, self)._return_client_context()
        client = self.env['owncloud.client']._get_client()
        if client:
            Config = self.env['ir.config_parameter'].sudo()
            share_urls = safe_eval(Config.get_param('owncloud_share_urls', "False"))
            client.share_urls = share_urls
            with_context_dict.update({"client": client,})
            if not self._context.get("no_ckeys"):
                root_key, root_path = self.with_context(
                    client=client,
                    s_logger=with_context_dict.get("s_logger")
                )._find_or_create_root_directory()
                child_ids = client.list_o(root_path, include_root=False, depth="infinity")
                ckeys = {child.get("id"): child.get("path") for child in child_ids}
                if len(child_ids) > len(ckeys):
                    # 1
                    child_ids = client.list_o(root_path, include_root=False, depth=1)
                    resulted_child_ids = []
                    for child in child_ids:
                        second_lvl_child_ids = client.list_o(child.get("path"), depth=1)
                        for second_lvl in second_lvl_child_ids:
                            thirdlevel_child_ids = client.list_o(second_lvl.get("path"), depth=1)
                            resulted_child_ids += thirdlevel_child_ids
                        resulted_child_ids += second_lvl_child_ids
                    child_ids += resulted_child_ids
                    ckeys = {child.get("id"): child.get("path") for child in child_ids}
                ckeys.update({root_key: root_path})
                with_context_dict.update({
                    "ckeys": ckeys,
                })
        else:
            with_context_dict.get("s_logger").error(u"OwnCloud Services are not available")
            raise UserError(u"OwnCloud Services are not available")
        return with_context_dict

    @api.model
    def _find_or_create_root_directory(self):
        """
        Method to return root directory name and id

        Returns:
         * key, root_path - key and path in client
         * False if failed

        Methods:
         * remove_illegal_characters
         * file_info_o of OwnCloud Client
         * mkdir of OwnCloud Client
        """
        client = self._context.get("client")
        Config = self.env['ir.config_parameter'].sudo()
        root_dir = Config.get_param('owncloud_root_dir', 'Odoo')
        try:
            #in try, since the folder might be removed in meanwhile
            result = client.file_info_o(root_dir)
            res = result.get("res_id"), result.get("path")
        except:
            if self._context.get("first_create"):
                # For a sudden case root dir contains illegal characters
                root_dir = self.remove_illegal_characters(root_dir)
                Config.set_param('owncloud_root_dir', root_dir)
            else:
                # in the first create it is not an error (when confirm credentials)
                self._context.get("s_logger").warning(
                    u"The root directory  '{}' has been removed from OwnCloud. Creating a new one".format(root_dir)
                )
            try:
                client.mkdir(root_dir)
                result = client.file_info_o(root_dir)
                res = result.get("res_id"), result.get("path")
                self._context.get("s_logger").debug(u"The root directory '{}' is created in OwnCloud".format(root_dir))
            except Exception as error:
                res = False, False
                self._context.get("s_logger").error(
                    u"The root directory '{}' can't be created in OwnCloud. Reason: {}".format(root_dir, error)
                )
        return res

    @api.model
    def _create_folder(self, folder_name, parent_folder_key, parent_folder_path):
        """
        Method to create folder in clouds

        Args:
         * folder_name - name of created folder
         * parent_folder_key - ID of parent folder in client
         * parent_folder_path - path of parent folder

        Methods:
         * build_path - global method
         * mkdir of OwnCloud Client
         * file_info_o of OwnCloud FileInfo

        Returns:
         * key, path or False if failed

        Extra info:
         * here we can't use folder_id as sync.model / sync.object, since as a parent 'root' might serves
        """
        try:
            client = self._context.get("client")
            ckeys = self._context.get("ckeys")
            parent_folder_path = ckeys.get(parent_folder_key)
            path = build_path([parent_folder_path, folder_name])
            client.mkdir(path)
            result = client.file_info_o(path)
            res = result.get("res_id"), result.get("path")
            ckeys.update({result.get("res_id"): result.get("path")})
            ctx = self.env.context.copy()
            ctx.update({"ckeys": ckeys})
            self.env.context = ctx
            self._context.get("s_logger").debug(u"The folder {} is created in OwnCloud".format(folder_name))
        except Exception as error:
            res = False, False
            self._context.get("s_logger").error(
                u"The folder {} can't be created in OwnCloud. Reason: {}".format(folder_name, error)
            )
        return res

    @api.model
    def _get_folder(self, folder_id):
        """
        Method to get folder in clouds
        * This method should be firstly triggered without ckeys to avoid slowdowns. If failed then with ckeys

        Methods:
         * file_info_o of OwnCloud Client
         * _return_client_context

        Args:
         * folder_id - sync.model or sync.object
         * False if failed

        Returns:
         * dict of values including 'url'
        """
        ckeys = self._context.get("ckeys")
        try:
            client = self._context.get("client")
            path = ckeys and ckeys.get(folder_id.key) or folder_id.path
            res = client.file_info_o(path)
        except Exception as error:
            if not ckeys:
                ctx = self._context.copy()
                ctx.update({"no_ckeys": False})
                new_ctx = self.with_context(ctx)._return_client_context()
                ctx.update(new_ctx)
                res = self.with_context(ctx)._get_folder(folder_id=folder_id)
            else:
                res = False
                self._context.get("s_logger").error(
                    u"The folder {} can't be found in OwnCloud. Reason: {}".format(folder_id.name, error)
                )
        return res

    @api.model
    def _update_folder(self, folder_id, new_folder_name):
        """
        Method to update folder in clouds
         1. Depending on folder_id model parents are different
         2. Move by path basically is the same as rename
         3. Update ckeys of this folder and all children till the 2nd level

        Args:
         * folder_id - sync.model or sync.object object (only such folders are updated)
         * new_folder_name - new name of folder

        Methods:
         * _find_or_create_root_directory
         * build_path - global method
         * move of OwnCloud Client

        Returns:
         * key, path or False, False if failed

        Extra info:
         * We do not use 'copy', since their children would have different ids
        """
        try:
            client = self._context.get("client")
            ckeys = self._context.get("ckeys")
            old_path = ckeys.get(folder_id.key)
            # 1
            parent_folder_path = False
            if hasattr(folder_id, "sync_model_id"):
                parent_folder_path = ckeys.get(folder_id.sync_model_id.key)
            else:
                parent_folder_key, parent_folder_path = self._find_or_create_root_directory()

            new_path = build_path([parent_folder_path, new_folder_name])
            # 2
            client.move(old_path, new_path)
            res = folder_id.key, new_path
            # 3
            children_dict = client.list_o(new_path, include_root=True, pair_dict=True)
            if hasattr(folder_id, "sync_model_id"):
                resulted_dict = {}
                for cckey, ccvalue in children_dict.items():
                    resulted_dict.update(client.list_o(ccvalue, include_root=True, pair_dict=True))
                children_dict.update(resulted_dict)
            ckeys.update(children_dict)
            ctx = self.env.context.copy()
            ctx.update({"ckeys": ckeys})
            self.env.context = ctx
            self._context.get("s_logger").debug(
                u"The folder {} is updated in OwnCloud to {}".format(folder_id.name, new_folder_name)
            )
        except Exception as error:
            res = False, False
            self._context.get("s_logger").error(
                u"The folder {} can't be updated in OwnCloud to {}. Reason: {}".format(
                    folder_id.name,
                    new_folder_name,
                    error,
                )
            )
        return res

    @api.model
    def _move_folder(self, folder_id, new_parent_key, new_parent_path):
        """
        Method to move folder in clouds to a different parent
         1. Key remains the same after moving
         2. Update ckeys of this folder and all its children till the 2nd level

        Args:
         * folder_id - sync.model or sync.object object (only such folders are moved)
         * new_parent_key - new parent folder key
         * new_parent_path - new parent folder path

        Methods:
         * move of OwnCloud Client
         * list_o of OwnCloud Client
         * build_path - global method

        Returns:
         * key, path or False, False if failed
        """
        try:
            client = self._context.get("client")
            ckeys = self._context.get("ckeys")
            folder_path = ckeys.get(folder_id.key)
            new_parent_path = ckeys.get(new_parent_key)
            new_path = build_path([new_parent_path, folder_id.name])
            client.move(folder_path, new_path)
            # 1
            res = folder_id.key, folder_id.path
            # 2
            children_dict = client.list_o(new_parent_path, include_root=True, pair_dict=True)
            if hasattr(folder_id, "sync_model_id"):
                resulted_dict = {}
                for cckey, ccvalue in children_dict.items():
                    level_second_ids = client.list_o(ccvalue, include_root=True, pair_dict=True)
                    resulted_dict.update(level_second_ids)
                children_dict.update(resulted_dict)
            ckeys.update(children_dict)
            ctx = self.env.context.copy()
            ctx.update({"ckeys": ckeys})
            self.env.context = ctx
            self._context.get("s_logger").debug(
                u"The folder {} is moved in OwnCloud to {}".format(
                    folder_id.name,
                    new_parent_path,
                )
            )
        except Exception as error:
            res = False, False
            self._context.get("s_logger").error(
                u"The folder {} can't be moved in OwnCloud to {}. Reason: {}".format(
                    folder_id.name,
                    new_parent_path,
                    error,
                )
            )
        return res

    @api.model
    def _remove_folder(self, folder_id):
        """
        Method to delete folder in clouds

        Args:
         * folder_id - sync.model or sync.object object (only such folders are removed)

        Methods:
         * delete of OwnCloud Client

        Returns:
         * True or False if failed

        Extra info:
         * Folder with changed path is not considered as deleted since we reconcile folders before
        """
        try:
            client = self._context.get("client")
            ckeys = self._context.get("ckeys")
            folder_path = ckeys.get(folder_id.key)
            if folder_path:
                result = client.delete(folder_path)
                self._context.get("s_logger").debug(u"The folder {} is deleted from OwnCloud".format(folder_id.name,))
            else:
                self._context.get("s_logger").warning(
                    u"The folder {} is not deleted from OwnCloud since it has been already deleted before".format(
                        folder_id.name,
                    )
                )
            res = True
        except Exception as error:
            if hasattr(error, "status_code") and error.status_code == 404:
                # 1
                res = True
                self._context.get("s_logger").warning(
                    u"The folder {} is not deleted from OwnCloud since it has been already deleted before".format(
                        folder_id.name,
                    )
                )
            else:
                res = False
                self._context.get("s_logger").error(
                    u"The folder {} can't be deleted from OwnCloud. Reason: {}".format(folder_id.name, error)
                )
        return res

    @api.model
    def _return_child_items(self, folder_id, key=False, path=False):
        """
        Method to return child items of this folder
         1. If folder was removed, all its children were removed as well

        Args:
         * folder_id - sync.model or sync.object object
         * key - key of a folder (used if no folder) - for the case of root
         * path -  path of a folder (used if no folder) - for the case of root

        Methods:
         * list_o of OwnCloud Instance

        Returns:
         * list of of child dicts including name, id, webUrl, path
         * None if error
        """
        try:
            client = self._context.get("client")
            ckeys = self._context.get("ckeys")
            key = folder_id and folder_id.key or key
            path = ckeys.get(key)
            if path:
                res = client.list_o(path)
            else:
                res = []
        except Exception as error:
            if hasattr(error, "status_code") and error.status_code == 404:
                # 1
                res = []
            else:
                res = None
                self._context.get("s_logger").error(
                    u"Failed to find a folder {} in OwnCloud. Reason: {}".format(
                        folder_id and folder_id.name or path, error, error
                    )
                )
        return res

    def _send_attachment_to_cloud(self, folder_id):
        """
        Method to send attachment to cloud
         0. Make file unique
         1. The method put_file returns bool, thus we need to get File Info
         2. Update ckeys with newly created attachment

        Args:
         * folder_id - sync.object or sync.model object - both might have attachments. The first - stand-alone ones

        Methods:
         * _normalize_name
         * build_path - global method
         * put_file of OwnCloud instance
         * file_info_o of OwnCloud instance
         * get_file_dict of OwnCloud FileInfo
         * _full_path

        Returns:
         * dict of res_id, url, filename, path
         * False if method failed

        Extra info:
         * Expected Singleton
        """
        self.ensure_one()
        res = False
        attachment_name = self.name
        try:
            client = self._context.get("client")
            ckeys = self._context.get("ckeys")
            folder_path = ckeys.get(folder_id.key)
            attachment_name = self._normalize_name()
            # 0
            itera = 1
            core_name = attachment_name
            children = client.list_o(folder_path)
            stop = True
            while stop:
                for cckey in children:
                    if cckey.get("name") == attachment_name:
                        attachment_name = self.name = u"({}) {}".format(itera, core_name)
                        itera += 1
                        break
                else:
                    stop = False
            self.name = attachment_name
            new_file_path = build_path([folder_path, attachment_name])

            local_path = self._full_path(self.store_fname)
            upload = client.put_file(new_file_path, local_path)
            if upload:
                # 1
                res = client.file_info_o(new_file_path)
                # 2
                ckeys.update({res.get("res_id"): res.get("path")})
                ctx = self.env.context.copy()
                ctx.update({"ckeys": ckeys})
                self.env.context = ctx
                self._context.get("s_logger").debug(
                    u"The file {} is uploaded in OwnCloud to {}".format(attachment_name, folder_path)
                )
        except Exception as error:
            res = False
            self._context.get("s_logger").error(
                u"The file {} ({}) can't be uploaded to OwnCloud. Reason: {}".format(attachment_name, self.id, error)
            )
        return res

    def _upload_attachment_from_cloud(self):
        """
        Method to upload attachment from cloud
         * This method should be firstly triggered without ckeys to avoid slowdowns. If failed then with ckeys

        Methods:
         * get_file_contents of OwnCloud Instance
         * b64encode of base64
         * _return_client_context

        Returns:
         * Binary File
         * False if method failed

        Extra info:
         * Expected Singleton
        """
        self.ensure_one()
        res = False
        ckeys = self._context.get("ckeys")
        try:
            client = self._context.get("client")
            cloud_path = ckeys and ckeys.get(self.cloud_key) or self.cloud_path
            result = client.get_file_contents(cloud_path)
            res = base64.b64encode(result)
        except Exception as error:
            if not ckeys:
                ctx = self._context.copy()
                ctx.update({"no_ckeys": False})
                new_ctx = self.with_context(ctx)._return_client_context()
                ctx.update(new_ctx)
                res = self.with_context(ctx)._upload_attachment_from_cloud()
            else:
                res = False
                self._context.get("s_logger").error(
                    u"Failed to download a file {} ({}) from OwnCloud. Reason: {}".format(self.name, self.id, error,)
                )
        return res

    def _move_attachment(self, folder_id):
        """
        Method an item to a different parent (Used only for stand alone attachments to move between models)
         0. Make name unique

        Args:
         * folder_id - sync.model or sync.object object (although sync.object is not a case)

        Methods:
         * file_info_o of OwnCloud Client
         * move of OwnCloud Client
         * build_path - global method
         * _normalize_name

        Returns:
         * key, path or False, False if failed

        Extra info:
         * Expected Singleton
        """
        self.ensure_one()
        attachment_name = self.name
        try:
            client = self._context.get("client")
            ckeys = self._context.get("ckeys")
            cloud_path = ckeys.get(self.cloud_key)
            old_data = client.file_info_o(cloud_path)
            attachment_name = old_data.get("filename")
            folder_path = ckeys.get(folder_id.key)
            # 0
            itera = 1
            core_name = attachment_name
            children = client.list_o(folder_path)
            stop = True
            while stop:
                for cckey in children:
                    if cckey.get("name") == attachment_name:
                        attachment_name = self.name = u"({}) {}".format(itera, core_name)
                        itera += 1
                        break
                else:
                    stop = False
            self.name = attachment_name
            new_path = build_path([folder_path, attachment_name])
            client.move(cloud_path, new_path)
            new_data = client.file_info_o(new_path)
            res = self.cloud_key, new_data.get("path")
            ckeys.update({
                self.cloud_key: new_data.get("path")
            })
            ctx = self.env.context.copy()
            ctx.update({"ckeys": ckeys})
            self.env.context = ctx
            self._context.get("s_logger").debug(
                u"The file {} is moved in OwnCloud to {}".format(
                    attachment_name,
                    folder_path,
                )
            )
        except Exception as error:
            res = False, False
            self._context.get("s_logger").error(
                u"The file {} can't be moved in OwnCloud to {}. Reason: {}".format(
                    attachment_name,
                    folder_id.path,
                    error,
                )
            )
        return res

    def _remove_attachment_from_cloud(self):
        """
        The method to remove linked file from a cloud storage
         1. If 404, file is already deleted form Clouds, so we do not need to do anything here

        Methods:
         * delete of OwnCloud Client

        Returns:
         * res - char of 3 possible values
           ** "not_synced" - it wasn't a sync attachment
           ** "success"
           ** "failure"

        Extra info:
         * Expected Singleton
        """
        self.ensure_one()
        try:
            # 1
            if self.cloud_key:
                client = self._context.get("client")
                ckeys = self._context.get("ckeys")
                cloud_path = ckeys.get(self.cloud_key)
                if cloud_path:
                    result = client.delete(cloud_path)
                    self._context.get("s_logger").debug(
                        u"The file {} ({}) is deleted from OwnCloud".format(self.name, self.id,)
                    )
                else:
                    self._context.get("s_logger").warning(
                        u"The file {} ({}) is not deleted from OwnCloud, since it has been removed already".format(
                            self.name,
                            self.id,
                        )
                    )
                res = "success"
            else:
                res = "not_synced"
        except Exception as error:
            if hasattr(error, "status_code") and error.status_code == 404:
                # 1
                res = "success"
                self._context.get("s_logger").warning(
                    u"The file {} ({}) is not deleted from OwnCloud, since it has been removed already".format(
                        self.name,
                        self.id,
                    )
                )
            else:
                res = "failure"
                self._context.get("s_logger").error(
                    u"The file {} ({}) can't be deleted from OwnCloud. Reason: {}".format(self.name, self.id, error)
                )
        return res
