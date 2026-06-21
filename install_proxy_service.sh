#!/bin/bash
# 一键安装 ima 代理为 macOS 系统服务（LaunchAgent）
# 安装后自动后台运行，开机自启

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLIST_NAME="com.yoyo.imaproxy"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
LOG_DIR="$HOME/Library/Logs"
mkdir -p "$LOG_DIR"

echo "🔧 安装 ima 代理服务..."

# 1. 先停掉旧的
launchctl unload "$PLIST_PATH" 2>/dev/null || true

# 2. 写 plist
cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>${SCRIPT_DIR}/ima_proxy.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/ima-proxy.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/ima-proxy.err</string>
    <key>WorkingDirectory</key>
    <string>${SCRIPT_DIR}</string>
</dict>
</plist>
EOF

# 3. 注册并启动
launchctl load -w "$PLIST_PATH"
sleep 1

# 4. 验证
if curl -s --max-time 2 http://localhost:8765/health > /dev/null; then
    echo "✅ 服务已启动并通过健康检查"
    echo "   健康端点: http://localhost:8765/health"
    echo "   日志:     ${LOG_DIR}/ima-proxy.log"
else
    echo "⚠️  服务已注册，但健康检查未通过。请查看日志:"
    echo "   tail -f ${LOG_DIR}/ima-proxy.err"
fi
