#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- 正在获取服务器的公共 IP 地址 ---"
PUBLIC_IP=$(curl -s ifconfig.me)

if [ -z "$PUBLIC_IP" ]; then
    echo "错误：无法获取公共 IP 地址。请检查网络连接或尝试其他服务（例如 icanhazip.com）。"
    exit 1
fi

echo "获取到的公共 IP 地址为: $PUBLIC_IP"

# 备份 docker-compose.yml
cp docker-compose.yml docker-compose.yml.bak
echo "已备份 docker-compose.yml 到 docker-compose.yml.bak"

echo "--- 正在更新 docker-compose.yml 中的 EXPECTED_MX_RECORD_HOST ---"
# 使用 sed 替换 EXPECTED_MX_RECORD_HOST 的值
# 注意：这里假设 EXPECTED_MX_RECORD_HOST 的值是双引号括起来的字符串
sed -i "s|EXPECTED_MX_RECORD_HOST: \"[^\"]*\"|EXPECTED_MX_RECORD_HOST: \"$PUBLIC_IP\"|" docker-compose.yml

# 检查 sed 命令是否成功
if [ $? -ne 0 ]; then
    echo "错误：更新 docker-compose.yml 失败。请手动检查文件。"
    exit 1
fi

echo "docker-compose.yml 已更新。"

echo "--- 正在构建并启动 Docker 服务 ---"
docker-compose up --build

echo "部署完成！"
