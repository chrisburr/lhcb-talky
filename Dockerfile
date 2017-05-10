FROM nginx

MAINTAINER christopher.burr@cern.ch

RUN apt-get update \
    && apt-get install -y curl bzip2 gcc binutils git \
    && rm -rf /var/lib/apt/lists/*
RUN curl https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh > miniconda.sh && \
    bash miniconda.sh -b -p /opt/miniconda && \
    rm miniconda.sh
ENV PATH "/opt/miniconda/bin:$PATH"
RUN conda install --yes flask sqlalchemy pcre
RUN pip install flask-admin colorlog bcrypt flask-mail uwsgi flask_wtf flask_sqlalchemy flask_security
RUN git clone https://github.com/chrisburr/lhcb-talky.git /lhcb-talky
COPY nginx.conf /etc/nginx/nginx.conf

# For testing we require
RUN echo 'backend : Agg   # use wxpython with antigrain (agg) rendering' > matplotlibrc
RUN conda install --yes matplotlib
RUN pip install lipsum

EXPOSE 80
CMD chown -R nginx /lhcb-talky && chgrp -R nginx /lhcb-talky && \
    cd /lhcb-talky && nginx && \
    uwsgi -s /tmp/talky.sock --manage-script-name --mount /=talky:app \
    --uid=nginx --gid=nginx --chown-socket=nginx:nginx
