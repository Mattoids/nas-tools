FROM alpine:3.17 AS Builder
RUN apk add --no-cache --virtual .build-deps \
        libffi-dev \
        gcc \
        musl-dev \
        libxml2-dev \
        libxslt-dev
RUN apk add --no-cache $(echo $(wget --no-check-certificate -qO- https://raw.githubusercontent.com/Mattoids/nas-tools/master/package_list.txt))
RUN ln -sf /usr/bin/python3 /usr/bin/python
RUN curl https://rclone.org/install.sh | bash
RUN if [ "$(uname -m)" = "x86_64" ]; then ARCH=amd64; elif [ "$(uname -m)" = "aarch64" ]; then ARCH=arm64; fi
RUN curl https://dl.min.io/client/mc/release/linux-${ARCH}/mc --create-dirs -o /usr/bin/mc
RUN chmod +x /usr/bin/mc
RUN pip install --upgrade pip setuptools wheel
RUN pip install cython
RUN pip install -r $(echo $(wget --no-check-certificate -qO- https://raw.githubusercontent.com/Mattoids/nas-tools/master/requirements.txt))
RUN apk del --purge .build-deps
RUN rm -rf /tmp/* /root/.cache /var/cache/apk/*
COPY --chmod=755 ./docker/rootfs /
FROM scratch AS APP
COPY --from=Builder / /
ENV S6_SERVICES_GRACETIME=30000 \
    S6_KILL_GRACETIME=60000 \
    S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0 \
    S6_SYNC_DISKS=1 \
    HOME="/nt" \
    TERM="xterm" \
    PATH=${PATH}:/usr/lib/chromium \
    LANG="C.UTF-8" \
    TZ="Asia/Shanghai" \
    NASTOOL_CONFIG="/config/config.yaml" \
    NASTOOL_AUTO_UPDATE=true \
    NASTOOL_CN_UPDATE=true \
    NASTOOL_VERSION=master \
    PS1="\u@\h:\w \$ " \
    REPO_URL="https://github.com/mattoids/nas-tools.git" \
    PYPI_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple" \
    ALPINE_MIRROR="mirrors.ustc.edu.cn" \
    PUID=0 \
    PGID=0 \
    UMASK=000 \
    WORKDIR="/nas-tools"
COPY . /${WORKDIR}
WORKDIR ${WORKDIR}
RUN addgroup -S nt -g 911 \
    && adduser -S nt -G nt -h ${HOME} -s /bin/bash -u 911 \
    && python_ver=$(python3 -V | awk '{print $2}') \
    && echo "${WORKDIR}/" > /usr/lib/python${python_ver%.*}/site-packages/nas-tools.pth \
    && echo 'fs.inotify.max_user_watches=5242880' >> /etc/sysctl.conf \
    && echo 'fs.inotify.max_user_instances=5242880' >> /etc/sysctl.conf \
    && echo "nt ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers \
    && cd third_party  \
    && git submodule init  \
    && git submodule update
EXPOSE 3000
VOLUME ["/config"]
ENTRYPOINT [ "/init" ]
