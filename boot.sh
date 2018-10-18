#!/bin/sh
#激活虚拟环境
source environment/bin/activate
# 创建新数据库
python manager.py deploy
# 启动gunicorn服务器 监听5000端口
exec gunicorn -b :5000 --access-logfile - --error-logfile - run:app