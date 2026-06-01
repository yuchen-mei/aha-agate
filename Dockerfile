FROM docker.io/ubuntu:20.04
LABEL description="garnet"

ARG AHA_HOME=/aha-agate
ARG AHA_REPO=https://github.com/yuchen-mei/aha-agate.git
ARG AHA_BRANCH=master
ARG AHA_COMMIT=
ENV AHA_HOME=${AHA_HOME}

# Avoid interactive apt and tzdata prompts during image build.
ENV DEBIAN_FRONTEND=noninteractive

# Install system packages used by CoreIR, Clockwork, Halide, Garnet, SAM,
# Voyager MU tests, and RTL simulation.
RUN apt-get update && \
    apt-get install -y \
        build-essential software-properties-common && \
    dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y \
        wget \
        git make gcc-9 g++-9 \
        sshfs vim tmux \
        python3 python3-dev python3-pip python3-venv \
        # Garnet
        default-jre \
        # Halide-to-Hardware
        imagemagick csh \
        libz-dev libpng-dev libjpeg-dev \
        libtinfo-dev libncurses-dev \
        # clockwork
        curl \
        # hwtypes
        libgmp-dev libmpfr-dev libmpc-dev \
        # cgra_pnr
        libigraph-dev \
        # clang
        xz-utils \
        # EDA Tools
        ksh tcsh tcl \
        dc libelf1 binutils \
        libxi6 libxrandr2 libtiff5 libmng2 \
        libjpeg62 libxft2 libxmu6 libglu1-mesa libxss1 \
        libxcb-render0 libglib2.0-0 \
        libc6-i386 \
        libncurses5 libxml2-dev \
        # sam
        graphviz \
        xxd \
        # voyager
        git-lfs \
        && \
    ln -s /usr/lib/x86_64-linux-gnu/libtiff.so.5 /usr/lib/x86_64-linux-gnu/libtiff.so.3 && \
    ln -s /usr/lib/x86_64-linux-gnu/libmng.so.2 /usr/lib/x86_64-linux-gnu/libmng.so.1 && \
    ln -fs /usr/share/zoneinfo/America/Los_Angeles /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata && \
    echo "dash dash/sh boolean false" | debconf-set-selections && \
    DEBIAN_FRONTEND=noninteractive dpkg-reconfigure dash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 100 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 100 && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 100 \
                        --slave   /usr/bin/g++ g++ /usr/bin/g++-9 && \
    pip install --no-cache-dir cmake==3.28.1 && \
    echo DONE

# Build steps depend on bash features and activation scripts.
SHELL ["/bin/bash", "--login", "-c"]


# Clone the parent branch and its recorded submodule SHAs, then create the
# AHA Python environment.
WORKDIR /
RUN --mount=type=secret,id=gtoken \
  set -euo pipefail && \
  mkdir -p "$(dirname "${AHA_HOME}")" && \
  if [ "${AHA_HOME}" != "/aha" ]; then ln -sfn ${AHA_HOME} /aha; fi && \
  export GIT_TERMINAL_PROMPT=0 && \
  if [ -s /run/secrets/gtoken ]; then \
    export GITHUB_TOKEN="$(cat /run/secrets/gtoken)" && \
    printf '%s\n' \
      '#!/bin/sh' \
      'case "$1" in' \
      '*Username*) echo x-access-token ;;' \
      '*Password*) echo "$GITHUB_TOKEN" ;;' \
      '*) echo ;;' \
      'esac' > /tmp/git-askpass && \
    chmod +x /tmp/git-askpass && \
    export GIT_ASKPASS=/tmp/git-askpass; \
  fi && \
  git clone "${AHA_REPO}" "${AHA_HOME}" && \
  cd ${AHA_HOME} && \
  if [ -n "${AHA_COMMIT}" ]; then \
    git fetch origin "${AHA_COMMIT}" && git checkout --force "${AHA_COMMIT}"; \
  else \
    git checkout --force "${AHA_BRANCH}"; \
  fi && \
  git submodule sync --recursive && \
  git submodule update --init --recursive && \
  git lfs install && \
  (git lfs pull || echo "WARNING: unable to fetch top-level Git LFS objects") && \
  git submodule foreach --recursive 'git lfs install; git lfs pull || true' && \
  rm -f /tmp/git-askpass && \
  python -m venv . && source bin/activate && \
  pip install --no-cache-dir \
    urllib3==1.26.15 \
    wheel six \
    systemrdl-compiler peakrdl-html \
    packaging \
    importlib_resources \
    Pillow \
    matplotlib \
    protobuf && \
  echo DONE


# MU and Voyager CGRA tests create their conda env at runtime through
# aha/util/map.py -> make create-env, so the image must provide a complete
# recursive Voyager checkout plus LFS objects.
RUN cd ${AHA_HOME}/voyager && \
  test -d quantized-training && \
  test -n "$(find quantized-training -mindepth 1 -maxdepth 2 -print -quit)" && \
  : CLEANUP 600 MB && \
      echo "--- DU.MODELS1" && \
      echo "delete 600MB of models; user will have to reload them manually in container" && \
      (du -sh ${AHA_HOME}/voyager/models/* || echo okay) && \
      /bin/rm -rf ${AHA_HOME}/voyager/models/* && \
      (du -sh ${AHA_HOME}/voyager/models/* || echo okay) && \
  : FINAL SIZE && \
      du -sh ${AHA_HOME}

WORKDIR ${AHA_HOME}/coreir/build
RUN cmake .. && make && make install && /bin/rm -rf src bin tests

ENV GARNET_HOME=${AHA_HOME}/garnet
ENV MFLOWGEN=${AHA_HOME}/mflowgen

# Keep the CPU torch install for flows that run in the AHA venv.
WORKDIR ${AHA_HOME}
RUN source ${AHA_HOME}/bin/activate && \
  export TMPDIR=${AHA_HOME}/tmp/torch_install && mkdir -p $TMPDIR && \
  pip install --cache-dir=$TMPDIR --build=$TMPDIR torch==1.7.1+cpu -f https://download.pytorch.org/whl/torch_stable.html && \
  echo "# Remove 700M tmp files created during install" && \
  rm -rf $TMPDIR

WORKDIR ${AHA_HOME}/clockwork
ENV COREIR_PATH=${AHA_HOME}/coreir
ENV LAKE_PATH=${AHA_HOME}/lake
RUN ./misc/install_deps_ahaflow.sh && \
    source user_settings/aha_settings.sh && \
    make all -j4 && \
    source misc/copy_cgralib.sh && \
    echo "Cleanup: 10M ntl, 440M barvinok, 390M dot-o files" && \
      rm -rf ntl* && \
      (cd ${AHA_HOME}/clockwork/barvinok-0.41; make clean) && \
      rm -rf ${AHA_HOME}/clockwork/*.o ${AHA_HOME}/clockwork/bin/*.o && \
    echo DONE

# Build Halide-to-Hardware with clang 7, then remove the large clang and
# generated Halide payloads. The entrypoint restores Halide distrib files;
# docker-bashrc restores clang only if an interactive shell needs it.
WORKDIR ${AHA_HOME}/Halide-to-Hardware
RUN \
  : CLANG-INSTALL && \
    echo "Install 1G of clang/llvm" && \
      url=http://releases.llvm.org/7.0.1/clang+llvm-7.0.1-x86_64-linux-gnu-ubuntu-18.04.tar.xz && \
      wget -nv -O ~/clang7.tar.xz $url && \
      tar -xvf ~/clang7.tar.xz --strip-components=1 -C /usr/ && \
      rm -rf ~/clang7.tar.xz && \
  : BUILD && \
    echo "Build and test Halide compiler" && \
      export COREIR_DIR=${AHA_HOME}/coreir && make -j2 && make distrib && \
  : CLEANUP && \
    echo "Cleanup: 200M lib, 400M gch, 200M distrib, 100M llvm" && \
      rm -rf lib/* && \
      rm -rf ${AHA_HOME}/Halide-to-Hardware/include/Halide.h.gch/  && \
      rm -rf ${AHA_HOME}/Halide-to-Hardware/distrib/{bin,lib}      && \
      rm -rf ${AHA_HOME}/Halide-to-Hardware/bin/build/llvm_objects && \
    echo "Cleanup: 1G clang in /usr, will be restored by bashrc" && \
      rm -rf /usr/*/{*clang*,*llvm*,*LLVM*} && \
  : DONE && \
    echo DONE

# Build SAM from the vendored source tree.
RUN echo "--- ..Sam" && cd ${AHA_HOME}/sam && make sam && \
  source ${AHA_HOME}/bin/activate && pip install --no-cache-dir scipy numpy pytest && pip install -e .

WORKDIR ${AHA_HOME}/cgra_pnr
RUN set -e && \
    # thunder
    mkdir -p thunder/build && \
    cd thunder/build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make -j placer && \
    cd ../.. && \
    \
    # cyclone
    mkdir -p cyclone/build && \
    cd cyclone/build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make -j router

# Miniconda is required by MU/Voyager test paths. The conda env itself is
# created lazily by `aha map` so regular app regressions do not pay that cost.
ENV CONDA_DIR=/opt/conda
RUN curl -sSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh \
    && bash miniconda.sh -b -p $CONDA_DIR \
    && rm miniconda.sh \
    && $CONDA_DIR/bin/conda clean -afy

ENV PATH=$CONDA_DIR/bin:$PATH

# Some Voyager C++ build scripts expect this glibc header path.
RUN mkdir -p /usr/include/sys && \
    curl -o /usr/include/sys/cdefs.h https://raw.githubusercontent.com/lattera/glibc/2.31/include/sys/cdefs.h


# Install z3 before `aha deps install`. hwtypes still requires z3 even though
# the formal-verification repositories have been removed.
#
# setup.py is included so COPY succeeds even when optional cached z3 collateral
# is not present in the Docker build context.
COPY ./setup.py z3_solver-4.16.0.0-py3-none-linux_x86_64.whl* /tmp/
COPY ./setup.py libz3.so*  /tmp/

RUN : z3 solver && \
    : Need gcc-13 to install and run z3-solver, used by hwtypes && \
    add-apt-repository ppa:ubuntu-toolchain-r/test && \
    apt update && apt install -y gcc-13 g++-13 && \
    (update-alternatives --remove-all gcc || echo okay) && \
    (update-alternatives --remove-all g++ || echo okay) && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 100 \
                        --slave   /usr/bin/g++ g++ /usr/bin/g++-13 && \
    type gcc && type cmake && gcc --version && cmake --version; \
    \
    if test -e /tmp/z3_solver-4.16.0.0-py3-none-linux_x86_64.whl; then \
        : Use cached collateral if available, saving 20m && \
        source ${AHA_HOME}/bin/activate && \
        pip install --no-cache-dir /tmp/z3_solver-4.16.0.0-py3-none-linux_x86_64.whl && \
        mv /tmp/libz3.so* ${AHA_HOME}/lib/python3.8/site-packages/z3/lib/libz3.so || exit 13; \
    else \
        : Install z3-solver from scratch && \
        cd ${AHA_HOME} && source bin/activate && \
        pip install --no-cache-dir z3-solver || exit 13; \
    fi && \
    \
    : Install runtime headers and libraries required by the z3 wheel on Ubuntu 20.04; \
    apt-get install -y libc6-dev-amd64 || apt-get install -y libc6-dev && \
    apt-get update && apt-get install -y linux-headers-generic && \
    ln -s /usr/include/asm-generic/ /usr/include/asm && \
    \
    : pythunder install fails under gcc-13, so reset the default compiler to gcc-9; \
    apt-get install -y gcc-9 g++-9 && \
    (update-alternatives --remove-all gcc || echo okay) && \
    (update-alternatives --remove-all g++ || echo okay) && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 100 \
                        --slave   /usr/bin/g++ g++ /usr/bin/g++-9 \
    || exit 13; \
    apt-get clean && rm -rf /var/lib/apt/lists/*; \
    echo z3-solver DONE

RUN : Final aha deps install && \
  cd ${AHA_HOME} && source bin/activate && \
  type gcc && type cmake && gcc --version && cmake --version && z3 --version; \
  pip install -e . && \
  aha deps install

WORKDIR ${AHA_HOME}

ENV OA_UNSUPPORTED_PLAT=linux_rhel60
ENV USER=docker

# Install the interactive shell helper: it activates the AHA venv, prepares
# module state, and restores clang when needed.
RUN \
  echo 'source "${AHA_HOME}/aha/bin/docker-bashrc"' >> /root/.bashrc && \
  echo DONE

# Leave the cloned checkout clean for interactive users. Several build steps
# rewrite tracked generated files, while the in-repo venv and editable installs
# create runtime artifacts that should exist but should not appear in status.
RUN set -euo pipefail && \
  cd "${AHA_HOME}" && \
  git reset --hard && \
  git submodule foreach --recursive 'git reset --hard || true' && \
  git -C voyager ls-files -z models | xargs -0r git -C voyager update-index --skip-worktree && \
  rm -rf voyager/models/* && \
  { \
    printf '%s\n' \
      '# Docker image-local build/runtime artifacts' \
      '.eggs/' \
      '*.egg-info/' \
      '__pycache__/' \
      '*/__pycache__/' \
      'bin/' \
      'include/' \
      'lib/' \
      'lib64' \
      'pyvenv.cfg' \
      'share/' \
      'tmp/' \
      'clockwork/bin/' \
      'ast_tools/ast_tools/immutable_ast.py'; \
  } >> .git/info/exclude && \
  git status --short && \
  test -z "$(git status --short)"

# Restore Halide distrib files before running the requested container command.
ENTRYPOINT [ "/bin/bash", "-lc", "exec \"$AHA_HOME/aha/bin/restore-halide-distrib.sh\" \"$@\"", "--" ]

# Keep cleanup in the same RUN layer as the files being created; otherwise the
# final image keeps the bytes in earlier layers.
