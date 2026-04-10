# Match the ROS2 image family as closely as possible while keeping Ubuntu 20.04
# for ROS1 Noetic compatibility.
FROM nvcr.io/nvidia/pytorch:23.04-py3

ARG CURL_INSECURE=0

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    ca-certificates \
    build-essential \
    cmake \
    curl \
    git \
    gnupg2 \
    nano \
    vim \
    iputils-ping \
    net-tools \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libosmesa6-dev \
    locales \
    lsb-release \
    python3-dev \
    python3-setuptools \
    software-properties-common \
    tmux \
    wget && \
    locale-gen en_US en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    python -m pip install --upgrade pip

RUN pip install \
    h5py \
    hydra-core \
    imageio \
    matplotlib \
    meshcat \
    objaverse==0.1.7 \
    opencv-python \
    pickle5 \
    python-fcl \
    qpsolvers[clarabel] \
    scene-synthesizer[recommend] \
    scikit-learn \
    scipy \
    tensorboard \
    trimesh==4.5.3 \
    webdataset \
    yourdfpy==0.0.56

RUN pip install pyrender==0.1.45 pyglet==2.1.6 && \
    pip install PyOpenGL==3.1.5

RUN pip install diffusers==0.11.1 timm==1.0.15 huggingface-hub==0.25.2
RUN pip install torchvision
RUN pip install addict yapf==0.40.1 tensorboardx sharedarray torch-geometric
RUN pip install torch-cluster -f https://data.pyg.org/whl/torch-2.1.0+cu121.html
RUN pip install torch-scatter -f https://data.pyg.org/whl/torch-2.1.0+cu121.html
RUN pip install spconv-cu120

WORKDIR /code

COPY pointnet2_ops /code/pointnet2_ops
RUN pip install ./pointnet2_ops --no-build-isolation

RUN /bin/bash -lc ' \
    CURL_FLAGS="-s"; \
    if [ "$CURL_INSECURE" = "1" ]; then CURL_FLAGS="$CURL_FLAGS -k"; fi; \
    curl $CURL_FLAGS https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt-get update && apt-get install -y git-lfs && \
    rm -rf /var/lib/apt/lists/*'

RUN mkdir -p /install && \
    cd /install && \
    git clone --recursive -j8 https://github.com/hjwdzh/Manifold.git && \
    mkdir -p /install/Manifold/build && \
    cd /install/Manifold/build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make -j"$(nproc)"

ENV PATH="${PATH}:/install/Manifold/build/"

RUN /bin/bash -lc ' \
    if [ "$CURL_INSECURE" = "1" ]; then \
      echo "deb [trusted=yes] http://packages.ros.org/ros/ubuntu focal main" \
      > /etc/apt/sources.list.d/ros1.list; \
    else \
      curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc \
      | gpg --dearmor -o /usr/share/keyrings/ros1-archive-keyring.gpg && \
      echo "deb [signed-by=/usr/share/keyrings/ros1-archive-keyring.gpg] http://packages.ros.org/ros/ubuntu focal main" \
      > /etc/apt/sources.list.d/ros1.list; \
    fi'

RUN apt-get update && apt-get install -y \
    ros-noetic-desktop-full \
    python3-catkin-tools \
    python3-rosdep \
    python3-rosinstall \
    python3-rosinstall-generator \
    python3-vcstool && \
    rm -rf /var/lib/apt/lists/*

RUN rosdep init || true

RUN echo "source /opt/ros/noetic/setup.bash" >> /root/.bashrc
RUN echo "export PS1='\[\e[1;36m\]\u@\h\[\e[0m\]:\[\e[1;34m\]\w\[\e[0m\]\$ '" >> /root/.bashrc

WORKDIR /code
