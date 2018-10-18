# 指定一个容器映像，在其基础上构建当前映像 名称：标签（版本、平台）
FROM python:3.6-alpine
# 设置环境变量
ENV FLASK_APP run.py
ENV FLASK_CONFIG docker
# 执行命令， 创建用户
RUN adduser -D ulysses
# 选择以那个身份运行容器及命令， 默认root
USER ulysses
# 指定应用所在顶层目录
WORKDIR /home/ulysses

# 从本地文件系统中把文件复制到容器的文件系统中
COPY requirements requirements
# 创建虚拟环境
RUN python -m venv environment
RUN environment/bin/pip install --user -r requirements/docker.txt

COPY app app
COPY migrations migrations
COPY run.py config.py manager.py boot.sh ./

# run-time configuration，启动容器后Docker会把这个端口映射到真实端口
EXPOSE 5000
# 指定启动容器时如何运行应用
ENTRYPOINT ["./boot.sh"]
