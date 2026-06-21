#!/usr/bin/env python3
"""
ima 知识库本地代理 — Personal Dashboard for Yoyo
将浏览器的请求转发到 ima API，解决 CORS 限制。

启动方式: python3 ima_proxy.py
默认端口: 8765
"""
import json, http.server, urllib.request, urllib.error, ssl, sys, os

IMA_API_BASE = "https://ima.qq.com"
PORT = 8765

class ImaProxy(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json({})

    def _resolve_path(self, path):
        """根据自定义路径路由到正确的 ima API base path"""
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(path)
        params = parse_qs(parsed.query)

        # 自定义端点 → 真实 ima API 路径
        if path.startswith("/agent-interface/knowledge-bases") or path.startswith("/agent-interface/knowledge-list"):
            if "knowledge_base_id" in params:
                kb_id = params["knowledge_base_id"][0]
                return f"https://ima.qq.com/openapi/wiki/v1/get_knowledge_list?knowledge_base_id={kb_id}&cursor=&limit=50", "GET", "enrich_notes"
            else:
                return "https://ima.qq.com/openapi/wiki/v1/search_knowledge_base?query=&cursor=&limit=20", "GET", None
        if path.startswith("/agent-interface/note-content"):
            note_id = params.get("note_id", [""])[0]
            # 0=纯文本 1=Markdown(不支持) 2=JSON(保留结构)
            return f"https://ima.qq.com/openapi/note/v1/get_doc_content?note_id={note_id}&target_content_format=2", "GET", None

        # 默认透传
        return f"{IMA_API_BASE}{parsed.path}?{parsed.query}", "GET", None

    def _enrich_note(self, client_id, api_key, media_id, ctx):
        """为 note 类型条目补全 notebook_id（get_media_info 接口）"""
        url = f"https://ima.qq.com/openapi/wiki/v1/get_media_info?media_id={media_id}"
        req = urllib.request.Request(url)
        req.add_header("ima-openapi-clientid", client_id)
        req.add_header("ima-openapi-apikey", api_key)
        try:
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                d = json.loads(resp.read().decode("utf-8"))
                if d.get("code") == 0 and d.get("data", {}).get("notebook_ext_info"):
                    return d["data"]["notebook_ext_info"].get("notebook_id")
        except Exception:
            pass
        return None

    def do_GET(self):
        if self.path == "/health":
            return self._send_json({"ok": True, "service": "ima-proxy", "version": "1.1"})

        # 本地文件服务 - 体重数据
        if self.path == "/local/weight":
            try:
                import os
                weight_file = os.path.expanduser("~/MyNote/weight.json")
                if not os.path.exists(weight_file):
                    return self._send_json([])
                with open(weight_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # CORS
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                return self._send_json({"error": f"读取失败: {str(e)}"}, 500)
            return

        # 转发到 ima API
        client_id = self.headers.get("X-Ima-Client-Id", "")
        api_key   = self.headers.get("X-Ima-Api-Key", "")

        if not client_id or not api_key:
            return self._send_json({"error": "缺少凭证，请在页面输入 Client ID 和 API Key"}, 401)

        url, method, post_hook = self._resolve_path(self.path)
        req = urllib.request.Request(url, method=method)
        # ima OpenAPI 要求的 header 名称
        req.add_header("ima-openapi-clientid", client_id)
        req.add_header("ima-openapi-apikey", api_key)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")

        try:
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # 后处理：为笔记条目补全 notebook_id
            if post_hook == "enrich_notes" and data.get("code") == 0:
                inner = data.get("data", {})
                items = inner.get("knowledge_list", [])
                for item in items:
                    if item.get("media_type") == 11 and not item.get("notebook_id"):
                        nb_id = self._enrich_note(client_id, api_key, item.get("media_id", ""), ctx)
                        if nb_id:
                            item["notebook_id"] = nb_id
            self._send_json(data)
        except urllib.error.HTTPError as e:
            self._send_json({"error": f"ima API 错误: {e.code}", "detail": e.reason}, e.code)
        except Exception as e:
            self._send_json({"error": f"请求失败: {str(e)}"}, 502)

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        client_id = self.headers.get("X-Ima-Client-Id", "")
        api_key   = self.headers.get("X-Ima-Api-Key", "")

        if not client_id or not api_key:
            return self._send_json({"error": "缺少凭证"}, 401)

        url = f"{IMA_API_BASE}{self.path}"
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("ima-openapi-clientid", client_id)
        req.add_header("ima-openapi-apikey", api_key)
        req.add_header("Accept", "application/json")

        try:
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._send_json(data)
        except urllib.error.HTTPError as e:
            self._send_json({"error": f"ima API 错误: {e.code}", "detail": e.reason}, e.code)
        except Exception as e:
            self._send_json({"error": f"请求失败: {str(e)}"}, 502)

    def log_message(self, format, *args):
        print(f"[ima-proxy] {args[0]}")


if __name__ == "__main__":
    print(f"🚀 ima 知识库代理已启动 → http://localhost:{PORT}")
    print(f"   在 Dashboard 的 ima 卡片中输入 Client ID 和 API Key 即可连接")
    print(f"   获取凭证: https://ima.qq.com/agent-interface")
    server = http.server.HTTPServer(("127.0.0.1", PORT), ImaProxy)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 已关闭")
        server.shutdown()
