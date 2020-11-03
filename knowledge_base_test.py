import knowledge_base_automation
import requests
import json
import os
import re


print("GROWI")
access_token = "***"
ip_addr = "***"
cookie = ""

g = knowledge_base_automation.GROWI(access_token, ip_addr, cookie=cookie, proto="http")


res = g.create_page("/test/testmd1", "# Autotest2\nautotest", grant=4)
print("create_page")
print(res)
print()

res = g.update_page("/test/testmd1", "# Auto Test\nThis is test\n\nrewrite.", grant=1)
print("update_page")
print(res)
print()

res = g.get_page("/test/testmd1")
print("get_page")
print(res)
print()

res = g.delete_page("/test/testmd1", complete=True, use_cookie=True)
print("delete_page")
print(res)
print()

res = g.send_attachments(
    "/Sandbox", "test/img/testpic.JPG", content_type="image/jpg"
)
print("send_attachments")
print(res)
print()
attachment_id = res["attachment"]["id"]

res = g.get_attachments(attachment_id, use_cookie=True)
print("get_attachments")
print(res)
print()

res = g.delete_attachments(attachment_id)
print("delete_attachments")
print(res)
print()

res = g.list_pages("/")
print("list_pages")
print(res)
print()

res = g.list_users()
print("list_users")
print(res)
print()

res = g.list_groups(use_cookie=True)
print("list_groups")
print(res)
print()

res = g.create_markdown_page("/test/testmd2", "test/test.md", "img/")
print("create_markdown_page")
print(res)
print()

res = g.download_markdown_page("/test/testmd2")
print("download_markdown_page")
print(res)
print()
res = g.delete_page("/test/testmd2", complete=True, use_cookie=True)


print("Knowledge")
access_token = "***"
ip_addr = "***"
cookie = ""

g = knowledge_base_automation.Knowledge(
    access_token, ip_addr, cookie=cookie, proto="http"
)


res = g.create_page("test", "# test\ntest\n\ntest")
print("create_page")
print(res)
print()
page_id = res["id"]

reg = g.update_page(page_id, "test", "# test\n\ntest\ntest", grant=0)
print("update_page")
print(res)
print()

res = g.get_page(page_id)
print("get_page")
print(res)
print()

res = g.delete_page(page_id)
print("delete_page")
print(res)
print()

res = g.send_attachments(1, "test/img/testpic.JPG", use_cookie=True)
print("send_attachments")
print(res)
print()
attachment_id = 9999
if "files" in res:
    attachment_id = res["files"][0]["fileNo"]

res = g.get_attachments(attachment_id)
print("get_attachment")
print(res)
print()

res = g.delete_attachments(attachment_id, use_cookie=True)
print("delete_attachments")
print(res)
print()

res = g.list_pages()
print("list_pages")
print(res)
print()

res = g.list_users()
print("list_users")
print(res)
print()

res = g.list_groups()
print("list_groups")
print(res)
print()

res = g.create_markdown_page("testmd", "test/test.md", "img/")
print("create_markdown_page")
print(res)
print()
page_id = res["id"]

res = g.download_markdown_page(page_id)
print("download_markdown_page")
print(res)
print()
res = g.delete_page(page_id)
