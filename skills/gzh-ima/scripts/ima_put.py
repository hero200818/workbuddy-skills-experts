#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ima_put.py — 把本地文件传到 ima 知识库的 COS 桶（供 add_knowledge 入库）

背景：ima 入库三步 = create_media(MCP) → 上传 COS(本脚本) → add_knowledge(MCP)。
本脚本只做第 2 步（COS PUT 上传），第 1、3 步用 MCP 工具。

用法：
  1) 调 MCP create_media，把返回的整段 JSON 存成 cred.json
     （含 media_id 与 cos_credential；也可以只存 cos_credential 对象）
  2) python3 ima_put.py cred.json 本地文件.md [--ct text/markdown]
  3) 拿脚本打印的 media_id 去调 add_knowledge

⚠️ cred.json 含临时密钥，上传完立刻删掉，不要入库、不要提交。

签名要点（错一步就 403 SignatureDoesNotMatch）：
  SignKey     = HMAC-SHA1(secret_key, key_time)
  HttpString  = method\\nuri\\nparams\\nheaders\\n
  StringToSign= "sha1\\n" + key_time + "\\n" + SHA1(HttpString) + "\\n"   ← 必须多这一层
  Signature   = HMAC-SHA1(SignKey, StringToSign)
"""
import argparse
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

CT_BY_EXT = {
    ".md": "text/markdown", ".markdown": "text/markdown",
    ".txt": "text/plain", ".html": "text/html", ".htm": "text/html",
    ".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg", ".webp": "image/webp", ".csv": "text/csv",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def _hmac_hex(key, msg):
    if isinstance(key, str):
        key = key.encode("utf-8")
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha1).hexdigest()


def _enc(s):
    return urllib.parse.quote(s, safe="-_.~")


def build_auth(cred):
    host = f"{cred['bucket_name']}.cos.{cred['region']}.myqcloud.com"
    path = "/" + cred["cos_key"].lstrip("/")
    key_time = f"{cred['start_time']};{cred['expired_time']}"
    token = cred["token"]

    header_list = "host;x-cos-security-token"
    enc_headers = f"host={_enc(host)}&x-cos-security-token={_enc(token)}"
    http_string = f"put\n{urllib.parse.quote(path, safe='/-_.~')}\n\n{enc_headers}\n"
    string_to_sign = (
        f"sha1\n{key_time}\n{hashlib.sha1(http_string.encode('utf-8')).hexdigest()}\n"
    )
    sign_key = _hmac_hex(cred["secret_key"], key_time)
    signature = _hmac_hex(sign_key, string_to_sign)

    auth = (
        "q-sign-algorithm=sha1"
        f"&q-ak={cred['secret_id']}"
        f"&q-sign-time={key_time}"
        f"&q-key-time={key_time}"
        f"&q-header-list={header_list}"
        "&q-url-param-list="
        f"&q-signature={signature}"
    )
    url = f"https://{host}{urllib.parse.quote(path, safe='/-_.~')}"
    return url, auth, token


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cred", help="create_media 返回的 JSON 文件")
    ap.add_argument("file", help="要上传的本地文件")
    ap.add_argument("--ct", help="Content-Type，默认按扩展名推断")
    args = ap.parse_args()

    raw = json.load(open(args.cred, encoding="utf-8"))
    cred = raw.get("cos_credential", raw)
    media_id = raw.get("media_id", "")
    ct = args.ct or CT_BY_EXT.get(os.path.splitext(args.file)[1].lower())
    if not ct:
        sys.exit(f"✗ 未知扩展名，请用 --ct 指定 MIME：{args.file}")

    data = open(args.file, "rb").read()
    if raw.get("file_size") and int(raw["file_size"]) != len(data):
        print(f"⚠️ 文件大小与 create_media 申报不一致（{len(data)} vs {raw['file_size']}）")

    url, auth, token = build_auth(cred)
    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("Authorization", auth)
    req.add_header("x-cos-security-token", token)
    req.add_header("Content-Type", ct)
    req.add_header("Content-Length", str(len(data)))

    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            print(f"✓ 上传成功 {r.status}  {len(data)} bytes  {os.path.basename(args.file)}")
    except urllib.error.HTTPError as e:
        print(f"✗ 上传失败 {e.code}: {e.read()[:400].decode('utf-8', 'ignore')}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 上传异常 {type(e).__name__}: {e}")
        sys.exit(1)

    if media_id:
        print(f"→ 下一步 add_knowledge media_id={media_id}")
    print("→ 入库完记得删掉凭证文件")


if __name__ == "__main__":
    main()
