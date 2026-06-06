#!/bin/bash
# 408 错题管理器 — 一键部署脚本
# 在 CentOS 服务器上运行: bash deploy.sh

set -e
echo "=== 408 错题管理器 部署 ==="

# 1. 安装 Python 3.9
echo "[1/5] 安装 Python 3.9..."
yum install -y python39 python39-pip git

# 2. 创建项目目录
echo "[2/5] 创建目录..."
mkdir -p /opt/errorbook
cd /opt/errorbook

# 3. 下载代码（你需要先把代码传上来）
# 方式A：从本地上传
# scp -r D:\错题项目\services\* root@121.40.212.86:/opt/errorbook/
# 
# 方式B：从 GitHub（如果有仓库）
# git clone <你的仓库地址> .

echo "[3/5] 请先手动上传代码到 /opt/errorbook/"
echo "方式: 在本机 PowerShell 运行："
echo "  scp -r D:\错题项目\services\* root@121.40.212.86:/opt/errorbook/"
echo ""
read -p "代码上传好了按回车继续..." 

# 4. 安装 Python 依赖
echo "[4/5] 安装依赖..."
python3.9 -m venv venv
source venv/bin/activate
pip install flask paddlepaddle paddleocr

# 5. 复制 API Key 配置文件（需要从本机传）
echo "[5/5] 配置 API Key..."
echo "请确保 auth-profiles.json 已传到 /opt/errorbook/agent/"
echo "或手动设置环境变量："
echo "  export DEEPSEEK_KEY=sk-xxx"
echo "  export QWEN_KEY=sk-xxx"

# 启动服务
echo ""
echo "=== 启动服务 ==="
echo "测试运行:"
echo "  cd /opt/errorbook && source venv/bin/activate"
echo "  python ocr_server.py"
echo ""
echo "生产运行:"
echo "  pip install gunicorn"
echo "  gunicorn -w 2 -b 0.0.0.0:8901 ocr_server:app --daemon"
echo ""
echo "防火墙:"
echo "  firewall-cmd --add-port=8901/tcp --permanent"
echo "  firewall-cmd --reload"
echo ""
echo "访问: http://121.40.212.86:8901"
