import requests
import json
import os
import re


class GROWI:
    api_url = "%s://%s/_api/%s"

    def __init__(self, access_token, ip_addr, cookie="", proto="https", verify=True):
        self.access_token = access_token
        self.ip_addr = ip_addr
        self.cookie = cookie
        self.proto = proto
        self.verify = verify

    def get(self, api, params=None, headers=None, use_cookie=False):
        if not params:
            params = {}
        if not headers:
            headers = {}
        url = self.api_url % (self.proto, self.ip_addr, api)
        if use_cookie and self.cookie:
            headers["Cookie"] = self.cookie
        else:
            params["access_token"] = self.access_token

        res = requests.get(url, params=params, headers=headers, verify=self.verify)
        return res

    def post(
        self, api, data, headers=None, files=None, use_data=False, use_cookie=False
    ):
        if not headers:
            headers = {}
        if not files:
            files = {}
        url = self.api_url % (self.proto, self.ip_addr, api)
        if use_cookie and self.cookie:
            headers["Cookie"] = self.cookie
            csrf = self.get_csrf("/")
            data["_csrf"] = csrf
        else:
            data["access_token"] = self.access_token

        if use_data:
            res = requests.post(
                url, data=data, headers=headers, files=files, verify=self.verify
            )
        else:
            res = requests.post(
                url, json=data, headers=headers, files=files, verify=self.verify
            )
        return res

    def put(self, api, data, headers=None):
        if not headers:
            headers = {}
        url = self.api_url % (self.proto, self.ip_addr, api)
        data["access_token"] = self.access_token
        res = requests.put(url, data=data, headers=headers, verify=self.verify)
        return res

    def delete(self, api, params=None):
        if not params:
            params = {}
        url = self.api_url % (self.proto, self.ip_addr, api)
        params["access_token"] = self.access_token
        res = requests.delete(url, params=params, verify=self.verify)
        return res

    def get_csrf(self, page_path):
        url = "%s://%s%s" % (self.proto, self.ip_addr, page_path)
        res = requests.get(url, headers={"Cookie": self.cookie}, verify=self.verify)

        start = res.text.find('data-csrftoken="')
        if start < 0:
            return ""
        start += len('data-csrftoken="')
        end = res.text[start:].find('"')
        if end < 0:
            return ""
        end = start + end

        csrf = res.text[start:end]
        return csrf

    def get_page(self, page_path, use_cookie=False):
        res = self.get("pages.get", params={"path": page_path}, use_cookie=use_cookie)
        return res.json()

    # grant
    #   1: Public
    #   2: Anyone with the link
    #   4: Private
    #   5: Group
    def create_page(
        self, page_path, page_body, grant=4, group_name="", use_cookie=False
    ):
        data = {"path": page_path, "body": page_body}
        if grant == 5:
            # May create pages that no one can access
            group_id = ""
            res_groups = self.list_groups(use_cookie=use_cookie)
            for i in res_groups["userGroupRelations"]:
                related_group = i["relatedGroup"]
                if related_group["name"] == group_name:
                    group_id = related_group["_id"]
            if not group_id:
                return {"ok": False}
            data["grantUserGroupId"] = group_id
        data["grant"] = grant
        res = self.post("pages.create", data, use_cookie=use_cookie)
        return res.json()

    def update_page(
        self, page_path, page_body, grant=4, group_name="", use_cookie=False
    ):
        page_json = self.get_page(page_path, use_cookie=use_cookie)
        page_id = page_json["page"]["_id"]
        revision_id = page_json["page"]["revision"]["_id"]

        data = {"page_id": page_id, "revision_id": revision_id, "body": page_body}

        data["grant"] = grant
        if grant == 5:
            # May create pages that no one can access
            group_id = ""
            res_groups = self.list_groups(use_cookie=use_cookie)
            for i in res_groups["userGroupRelations"]:
                related_group = i["relatedGroup"]
                if related_group["name"] == group_name:
                    group_id = related_group["_id"]
            if not group_id:
                return {"ok": False}
            data["grantUserGroupId"] = group_id
        res = self.post("pages.update", data, use_cookie=use_cookie)
        return res.json()

    def delete_page(self, page_path, recursive=True, complete=False, use_cookie=False):
        if not use_cookie or not self.cookie:
            return {"ok": False}
        page_json = self.get_page(page_path)

        page_id = page_json["page"]["_id"]
        revision_id = page_json["page"]["revision"]["_id"]
        csrf = self.get_csrf(page_path)
        if not csrf:
            return {"ok": False}

        data = {
            "page_id": page_id,
            "revision_id": revision_id,
            "recursively": recursive,
            "_csrf": csrf,
        }
        if complete:
            data["completely"] = complete
        res = self.post("pages.remove", data, use_cookie=True)

        return res.json()

    def get_attachments(self, attachment_id, use_cookie=False):
        if not use_cookie or not self.cookie:
            return None
        url = "%s://%s/download/%s" % (self.proto, self.ip_addr, attachment_id)
        res = requests.get(url, headers={"Cookie": self.cookie}, verify=self.verify)
        return res.content

    def send_attachments(self, page_path, file_path, content_type="*/*"):
        params = {"fileSize": os.path.getsize(file_path)}
        res = self.get("attachments.limit", params=params)
        if not res.json()["isUploadable"]:
            return {"ok": False}

        page_json = self.get_page(page_path)
        page_id = page_json["page"]["_id"]

        data = {"page_id": page_id}
        files = {
            "file": (os.path.basename(file_path), open(file_path, "rb"), content_type)
        }
        res = self.post("attachments.add", data, files=files, use_data=True)
        return res.json()

    def delete_attachments(self, attachment_id):
        data = {"attachment_id": attachment_id}
        res = self.post("attachments.remove", data)
        return res.json()

    def list_pages(self, page_path):
        res = self.get("pages.list", params={"path": page_path})
        return res.json()

    def list_users(self):
        res = self.get("users.list")
        return res.json()

    def list_groups(self, use_cookie=False):
        res = self.get("me/user-group-relations", use_cookie=use_cookie)
        return res.json()

    def create_markdown_page(self, page_path, md_path, relative_image_path, grant=4):
        self.create_page(page_path, "markdown", grant=grant)

        image_list = []

        image_dir = os.path.join(os.path.dirname(md_path), relative_image_path)
        if os.path.exists(image_dir):
            for image_name in os.listdir(image_dir):
                upload_json = self.send_attachments(
                    page_path, os.path.join(image_dir, image_name)
                )
                image_list.append(
                    [
                        os.path.join(relative_image_path, image_name),
                        upload_json["attachment"]["filePathProxied"],
                    ]
                )

        f = open(md_path, "r", encoding="utf-8")
        md_data = f.read()
        f.close()

        for i in image_list:
            md_data = md_data.replace(i[0], i[1])

        return self.update_page(page_path, md_data, grant=grant)

    def download_markdown_page(self, page_path, target_path="testmd/"):
        page_json = self.get_page(page_path)
        page_body = page_json["page"]["revision"]["body"]

        image_dir = os.path.join(target_path, "img")
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        image_list = []
        for attachment_id in re.findall("/attachment/([0-9a-f]*)", page_body, re.S):
            attachment_data = self.get_attachments(attachment_id, use_cookie=True)
            if not attachment_data:
                continue
            image_list.append(
                ["/attachment/" + attachment_id, "img/attachment_" + attachment_id]
            )
            with open(
                os.path.join(image_dir, "attachment_" + attachment_id), "wb"
            ) as f:
                f.write(attachment_data)

        for i in image_list:
            page_body = page_body.replace(i[0], i[1])

        with open(
            os.path.join(target_path, os.path.basename(page_path) + ".md"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(page_body)

        return page_json


class Knowledge:
    api_url = "%s://%s/api/%s"

    def __init__(self, access_token, ip_addr, cookie="", proto="https", verify=True):
        self.access_token = access_token
        self.ip_addr = ip_addr
        self.cookie = cookie
        self.proto = proto
        self.verify = verify

    def get(self, api, params=None):
        if not params:
            params = {}
        url = self.api_url % (self.proto, self.ip_addr, api)
        params["private_token"] = self.access_token
        res = requests.get(url, params=params, verify=self.verify)
        return res

    def post(self, api, json_data, headers=None):
        if not headers:
            headers = {}
        url = self.api_url % (self.proto, self.ip_addr, api)
        headers["PRIVATE-TOKEN"] = self.access_token
        res = requests.post(url, json=json_data, headers=headers, verify=self.verify)
        return res

    def put(self, api, json_data, headers=None):
        if not headers:
            headers = {}
        url = self.api_url % (self.proto, self.ip_addr, api)
        headers["PRIVATE-TOKEN"] = self.access_token
        res = requests.put(url, json=json_data, headers=headers, verify=self.verify)
        return res

    def delete(self, api, params=None):
        if not params:
            params = {}
        url = self.api_url % (self.proto, self.ip_addr, api)
        params["private_token"] = self.access_token
        res = requests.delete(url, params=params, verify=self.verify)
        return res

    def get_page(self, page_id):
        res = self.get("knowledges/" + str(page_id))
        return res.json()

    def create_json_page_data(
        self, page_title, page_body, groups=None, users=None, grant=1
    ):
        if not groups:
            groups = []
        if not users:
            users = []
        json_data = {
            "template": "knowledge",
            "title": page_title,
            "content": page_body,
            "publicFlag": grant,
        }

        viewer_groups = []
        viewer_users = []
        for gid in groups:
            viewer_groups.append({"id": gid})
        for uid in users:
            viewer_users.append({"id": uid})

        if len(viewer_groups) > 0 or len(viewer_users) > 0:
            json_data["viewers"] = {}

        if len(viewer_groups) > 0:
            json_data["viewers"]["groups"] = viewer_groups
        if len(viewer_users) > 0:
            json_data["viewers"]["users"] = viewer_users

        return json_data

    # publicFlag
    #   0 Public
    #   1 Private
    #   2 Protect
    def create_page(self, page_title, page_body, groups=None, users=None, grant=1):
        if not groups:
            groups = []
        if not users:
            users = []
        json_data = self.create_json_page_data(
            page_title, page_body, groups=groups, users=users, grant=grant
        )
        res = self.post("knowledges", json_data)
        return res.json()

    def update_page(
        self, page_id, page_title, page_body, groups=None, users=None, grant=1
    ):
        if not groups:
            groups = []
        if not users:
            users = []
        json_data = self.create_json_page_data(
            page_title, page_body, groups=groups, users=users, grant=grant
        )
        res = self.put("knowledges/" + str(page_id), json_data)
        return res.json()

    def delete_page(self, page_id):
        res = self.delete("knowledges/" + str(page_id))
        return res.json()

    def get_attachments(self, attachment_id):
        res = self.get("attachments/" + str(attachment_id))
        return res.content

    def send_attachments(
        self, page_id, file_path, content_type="text/plain", use_cookie=False
    ):
        if not use_cookie or not self.cookie:
            return {"msg": "failed"}
        url = "%s://%s/protect.file/upload" % (self.proto, self.ip_addr)
        files = {
            "files[]": (
                os.path.basename(file_path),
                open(file_path, "rb"),
                content_type,
            )
        }
        res = requests.post(
            url, files=files, headers={"Cookie": self.cookie}, verify=self.verify
        )
        # Link to page fails
        return res.json()

    def delete_attachments(self, attachment_id, use_cookie=False):
        if not use_cookie or not self.cookie:
            return {"msg": "failed: %s" % attachment_id}
        url = "%s://%s/protect.file/delete/%d" % (
            self.proto,
            self.ip_addr,
            attachment_id,
        )
        res = requests.delete(url, headers={"Cookie": self.cookie}, verify=self.verify)
        return res.json()

    def list_pages(self, offset=0):
        params = {"offset": offset}
        res = self.get("knowledges", params=params)
        return res.json()

    def list_users(self):
        res = self.get("users")
        return res.json()

    def list_groups(self):
        res = self.get("groups")
        return res.json()

    def create_markdown_page(self, page_title, md_path, relative_image_path, grant=1):
        created_json = self.create_page(page_title, "# markdown", grant=grant)

        image_list = []

        image_dir = os.path.join(os.path.dirname(md_path), relative_image_path)
        if os.path.exists(image_dir):
            for image_name in os.listdir(image_dir):
                upload_json = self.send_attachments(
                    created_json["id"],
                    os.path.join(image_dir, image_name),
                    use_cookie=True,
                )
                image_list.append(
                    [
                        os.path.join(relative_image_path, image_name),
                        upload_json["files"][0]["url"],
                    ]
                )

        f = open(md_path, "r", encoding="utf-8")
        md_data = f.read()
        f.close()

        for i in image_list:
            md_data = md_data.replace(i[0], i[1])

        self.update_page(created_json["id"], page_title, md_data, grant=grant)
        return created_json

    def download_markdown_page(self, page_id, target_path="testmd/"):
        page_json = self.get_page(page_id)
        content = page_json["content"]

        image_dir = os.path.join(target_path, "img")
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        image_list = []
        for attachment in page_json["attachments"]:
            image_list.append(
                [
                    "/open.file/download?fileNo=" + str(attachment["fileNo"]),
                    "img/" + attachment["fileName"],
                ]
            )
            with open(
                os.path.join(target_path, "img", attachment["fileName"]), "wb"
            ) as f:
                f.write(self.get_attachments(attachment["fileNo"]))
        for attachment in re.findall(
            "/open.file/download\?fileNo=([0-9]*)", content, re.S
        ):
            if not attachment:
                continue
            image_list.append(
                [
                    "/open.file/download?fileNo=" + attachment,
                    "img/attachment_" + attachment,
                ]
            )
            with open(
                os.path.join(target_path, "img", "attachment_" + attachment), "wb"
            ) as f:
                f.write(self.get_attachments(int(attachment)))

        for i in image_list:
            content = content.replace(i[0], i[1])
        with open(
            os.path.join(target_path, page_json["title"] + ".md"), "w", encoding="utf-8"
        ) as f:
            f.write(content)

        return page_json
