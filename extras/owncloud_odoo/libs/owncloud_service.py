# -*- coding: utf-8 -*-

import logging
import xml.etree.ElementTree as ET

_logger = logging.getLogger(__name__)

try:
    import six
    from owncloud import Client as OwncloudClient, FileInfo, ShareInfo, HTTPResponseError
    from six.moves.urllib import parse
except ImportError as e:
    _logger.error(e)
    OwncloudClient = object
    FileInfo = object
    ShareInfo = object


class FileInfo(FileInfo):
    """
    Re-write class to add methods
    """
    def get_file_id(self):
        """
        The method to get OwnCloud ID
        """
        return self.attributes.get('{http://owncloud.org/ns}fileid')

    def get_file_dict(self):
        """
        The method to retrieve essential for connector params:
         * id, file_name, url, path

        Returns:
         * dict of values
        """
        result = {
            "res_id": self.get_file_id(),
            "id": self.get_file_id(),
            "filename": self.name,
            "name": self.name,
            "path": self.path,
            "mimetype": self.file_type == "dir" and self.file_type or self.attributes.get('{DAV:}getcontenttype'),
        }
        return result


class PatchedClient(OwncloudClient):
    """
    Re-write class to extend / replace its methods

    Extra info:
     * The method 'SEARCH' for requests is not implemented (501)
    """
    _cache = []

    def list_o(self, path, depth=1, include_root=False, pair_dict=False):
        """
        Re-write method to get additional file attributes from Owncloud
        We can't inherit (super) method since no way to pass data
         1. The reason of re-writing: introduce data in proper format
         2. The first one is always the folder of request, remove it from listing

        Args:
         * path - OwnCloud path
         * depth - levels of chilrden ("infinity" is possible but not recommended)
         * include_root - whether to include a folder itself
         * pair_dict - return result as a dict of pairs id: path

        """
        if not path.endswith('/'):
            path += '/'

        headers = {}
        if isinstance(depth, int) or depth == "infinity":
            headers['Depth'] = str(depth)
        # 1
        data = """<?xml version="1.0"?>
            <d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
              <d:prop>
                    <d:getlastmodified />
                    <d:getetag />
                    <d:getcontenttype />
                    <d:resourcetype />
                    <d:getcontentlength />
                    <d:quota-available-bytes />
                    <d:quota-used-bytes />
                    <oc:fileid />
                    <oc:permissions />
                    <oc:size />
              </d:prop>
            </d:propfind>
        """
        res = self._make_dav_request(
            'PROPFIND',
            path,
            headers=headers,
            data=data,
        )
        result = None
        if pair_dict:
            result = {}
        if res:
            # 2
            if include_root:
                result_full = res
            else:
                result_full = res[1:]
            result = []
            if pair_dict:
                result = {}
            for child in result_full:
                child_file_info = child.get_file_dict()
                if pair_dict:
                    result.update({child_file_info.get("res_id"): child_file_info.get("path")})
                else:
                    if self.share_urls:
                        url_link = self.get_url(path=child_file_info.get("path"))
                    else:
                        url_link = '{}index.php/f/{}'.format(self.url, child_file_info.get("res_id"))
                    result += [{
                        "id": child_file_info.get("res_id"),
                        "res_id": child_file_info.get("res_id"),
                        "name": child_file_info.get("filename"),
                        "filename": child_file_info.get("filename"),
                        "url": url_link,
                        "webUrl": url_link,
                        "path": child_file_info.get("path"),
                        "mimetype": child_file_info.get("mimetype"),
                    }]
        return result

    def file_info_o(self, path):
        """
        Copy method file_info to get additional file attributes from Owncloud
        We can't inherit (super) method since no way to pass data
         1. The reason of re-writing: introduce data in proper format
         2. The first one is always the root, remove it from listing

        Methods:
         * get_file_dict
        """
        data = """<?xml version="1.0"?>
            <d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
              <d:prop>
                    <d:getlastmodified />
                    <d:getetag />
                    <d:getcontenttype />
                    <d:resourcetype />
                    <d:getcontentlength />
                    <d:quota-available-bytes />
                    <d:quota-used-bytes />
                    <oc:fileid />
                    <oc:permissions />
                    <oc:size />
              </d:prop>
            </d:propfind>
        """
        res = self._make_dav_request(
            'PROPFIND',
            path,
            headers={'Depth': '0'},
            data=data,
        )
        result = None
        if res:
            result_fileinfo = res[0]
            result = result_fileinfo.get_file_dict()
            if self.share_urls:
                url = self.get_url(path=result.get("path"))
            else:
                url = '{}index.php/f/{}'.format(self.url, result.get("res_id"))
            result.update({"url": url, "webUrl": url,})
        return result

    def _parse_dav_element(self, dav_response):
        """
        The method is repeated to add FileInfo methods
        It is absolutely the same as in the lib

        Return an instance of the modified FileInfo class
        """
        href = parse.unquote(
            self._strip_dav_path(dav_response.find('{DAV:}href').text)
        )
        if six.PY2:
            href = href.decode('utf-8')

        file_type = 'file'
        if href[-1] == '/':
            file_type = 'dir'

        file_attrs = {}
        attrs = dav_response.find('{DAV:}propstat')
        attrs = attrs.find('{DAV:}prop')
        for attr in attrs:
            file_attrs[attr.tag] = attr.text

        return FileInfo(href, file_type, file_attrs)

    def get_url(self, path):
        """
        The method to generate a share url if public links are turned on
        """
        existing_shares = self.get_shares(path)
        if existing_shares:
            res = existing_shares[0].get_link()
        else:
            res = self.share_file_with_link_o(path).get_link()
        return res

    def share_file_with_link_o(self, path, **kwargs):
        """
        Have own method to construct share, since library has the bug of parsing data for NextCloud
        """
        path = self._normalize_path(path)
        post_data = {
            'shareType': self.OCS_SHARE_TYPE_LINK,
            'path': self._encode_string(path),
        }        
        res = self._make_ocs_request(
            'POST',
            self.OCS_SERVICE_SHARE,
            'shares',
            data=post_data
        )
        if res.status_code == 200:
            tree = ET.fromstring(res.content)
            self._check_ocs_status(tree)
            data_el = tree.find('data')
            return ShareInfo(
                {
                    'id': data_el.find('id').text,
                    'path': path,
                    'url': data_el.find('url').text,
                }
            )
        raise HTTPResponseError(res)
