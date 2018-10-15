#!/bin/sh
#激活虚拟环境
source venv/bin/activate
# 创建新数据库
flask deploy
# 启动gunicorn服务器 监听5000端口
exec gunicorn -b 0.0.0.0:500 --access-logfile - --error-logfile - run:app