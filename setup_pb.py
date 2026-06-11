#!/usr/bin/env python3
# PocketBase 初始化脚本
# 为 AI WebApp 作品集创建 tools 集合（公开读写）
# 用法: python setup_pb.py

import sys
import json
import urllib.request
import urllib.error

PB_URL = "http://1.15.178.127:8090"


def request(method, path, data=None, headers=None):
    url = f"{PB_URL}{path}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {"raw": str(e)}


def main():
    print("=" * 50)
    print("PocketBase 初始化脚本")
    print(f"目标: {PB_URL}")
    print("=" * 50)
    print()
    print("请输入你在 PocketBase 管理后台 /_/ 创建的超级管理员账号")

    email = input("邮箱: ").strip()
    password = input("密码: ")
    print()

    # 1. 登录 superuser (PocketBase v0.22+ 端点)
    print("[1/4] 正在登录 superuser 账号...")
    status, data = request(
        "POST",
        "/api/collections/_superusers/auth-with-password",
        {"identity": email, "password": password},
    )
    if status != 200:
        print(f"   登录失败: {data}")
        sys.exit(1)
    token = data["token"]
    print("   OK")
    print()

    auth = {"Authorization": token}

    # 2. 检查是否已有 tools
    print("[2/4] 检查现有 collection...")
    status, data = request("GET", "/api/collections", headers=auth)
    if status != 200:
        print(f"   失败: {data}")
        sys.exit(1)
    existing = next((c for c in data.get("items", []) if c["name"] == "tools"), None)
    if existing:
        print(f"   已存在 'tools' (id={existing['id']})")
        choice = input("   删除并重建? (y/N): ").strip().lower()
        if choice == "y":
            s, _ = request("DELETE", f"/api/collections/{existing['id']}", headers=auth)
            if s != 204:
                print(f"   删除失败: {s}")
                sys.exit(1)
            print("   已删除旧 collection")
        else:
            print("   跳过创建，直接验证 API...")
            print()
            verify()
            return
    print()

    # 3. 创建 tools collection
    print("[3/4] 创建 'tools' collection（公开读写）...")
    payload = {
        "name": "tools",
        "type": "base",
        "schema": [
            {
                "name": "name",
                "type": "text",
                "required": True,
                "options": {"min": 1, "max": 200, "pattern": ""},
            },
            {
                "name": "url",
                "type": "url",
                "required": True,
                "options": {"exceptDomains": [], "onlyDomains": []},
            },
            {
                "name": "description",
                "type": "text",
                "required": False,
                "options": {"min": 0, "max": 1000, "pattern": ""},
            },
        ],
        "listRule": "",
        "viewRule": "",
        "createRule": "",
        "updateRule": "",
        "deleteRule": "",
    }
    status, data = request("POST", "/api/collections", payload, headers=auth)
    if status not in (200, 201):
        print(f"   失败: {data}")
        sys.exit(1)
    print(f"   OK (id={data.get('id')})")
    print()

    # 4. 验证
    verify()


def verify():
    print("[4/4] 测试 API（无需登录）...")
    status, data = request("GET", "/api/collections/tools/records")
    if status == 200:
        print(f"   OK: {json.dumps(data, ensure_ascii=False)[:120]}")
    else:
        print(f"   状态 {status}: {data}")
    print()
    print("=" * 50)
    print("完成！")
    print(f"你的 API 地址: {PB_URL}/api/collections/tools/records")
    print("现在告诉 AI 助手 'PocketBase 已就绪' 即可改前端。")
    print("=" * 50)


if __name__ == "__main__":
    main()
