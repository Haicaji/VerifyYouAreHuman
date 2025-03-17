FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制网站文件和服务器代码
COPY www/ /app/www/
COPY server/ /app/server/
COPY LICENSE /app/LICENSE
COPY README.md /app/README.md

# 安装依赖
RUN pip install flask --no-cache-dir

# 设置环境变量处理脚本
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# 暴露80端口
EXPOSE 80

# 使用入口脚本处理FLAG环境变量并启动服务器
ENTRYPOINT ["/app/docker-entrypoint.sh"]
