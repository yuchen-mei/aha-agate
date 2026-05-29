# 10/17/2023
# If we put most-likely-to change submodules LAST in Dockerfile, we can
# maximize cache usage and minimize average build time.  A histogram of
# most-recent 256 submodule changes came up with this list.
#
#       ..<others w lower frequency occluded>..
#       6 kratos <kratos was responsible for 6 of the last 256 changes>
#       8 gemstone
#       8 Halide-to-Hardware
#       8 MetaMapper
#      16 canal
#      16 clockwork
#      16 sam
#      35 lake
#      36 archipelago
#      85 garnet
#      ..<garnet is the submodule that changed the most>..

FROM docker.io/ubuntu:20.04
LABEL description="garnet"

ARG AHA_HOME=/aha-agate
ENV AHA_HOME=${AHA_HOME}

# Prevents e.g. "Please select geographic area" during "apt-git install build-essential"
ENV DEBIAN_FRONTEND=noninteractive

# 1GB maybe
RUN apt-get update && \
    apt-get install -y \
        build-essential software-properties-common && \
    # add-apt-repository -y ppa:ubuntu-toolchain-r/test && \
    # add-apt-repository -y ppa:zeehio/libxp && \
    dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y \
        wget \
        git make gcc-9 g++-9 \
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
        # libxp6 \
        libxi6 libxrandr2 libtiff5 libmng2 \
        libjpeg62 libxft2 libxmu6 libglu1-mesa libxss1 \
        libxcb-render0 libglib2.0-0 \
        libc6-i386 \
        libncurses5 libxml2-dev \
        # sam
        graphviz \
        xxd \
        # pono
        time \
        m4 \
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
    pip install cmake==3.28.1 && \
    echo DONE

# Switch shell to bash
SHELL ["/bin/bash", "--login", "-c"]


# Create the repo root directory and prep a python environment.
# Don't copy the repo (yet) else cannot cache subsequent layers...
WORKDIR /
RUN mkdir -p ${AHA_HOME} && \
  if [ "${AHA_HOME}" != "/aha" ]; then ln -sfn ${AHA_HOME} /aha; fi && \
  cd ${AHA_HOME} && python -m venv . && source bin/activate && \
  pip install urllib3==1.26.15 && \
  pip install wheel six && \
  pip install systemrdl-compiler peakrdl-html && \
  pip install packaging && \
  pip install importlib_resources && \
  pip install Pillow && \
  pip install matplotlib && \
  pip install protobuf && \
  echo DONE


# Put the problem child here up front so that it can fail quickly :(
# Voyager 1 - clone voyager

# Use token provided by docker-build `--secrets` to clone voyager
RUN --mount=type=secret,id=gtoken \
  cd ${AHA_HOME} && \
  git clone https://$(cat /run/secrets/gtoken)@github.com:/StanfordAHA/voyager.git voyager && \
  cd ${AHA_HOME}/voyager && \
  mkdir -p ${AHA_HOME}/.git/modules && \
  mv .git/ ${AHA_HOME}/.git/modules/voyager/ && \
  ln -s ${AHA_HOME}/.git/modules/voyager/ .git && \
  : GIT LFS although maybe this does not really do anything && \
      git lfs install && git lfs pull && \
  : CLEANUP1 800 MB && \
      echo "# cleanup: delete 800MB of git history; will be restored by bashrc/restore-dotgit" && \
      du -sh ${AHA_HOME}/.git && \
      /bin/rm -rf ${AHA_HOME}/.git/modules/voyager/ && \
      du -sh ${AHA_HOME}/.git && \
  : CLEANUP2 600 MB && \
      echo "--- DU.MODELS1" && \
      echo "delete 600MB of models; user will have to reload them manually in container" && \
      (du -sh ${AHA_HOME}/voyager/models/* || echo okay) && \
      /bin/rm -rf ${AHA_HOME}/voyager/models/* && \
      (du -sh ${AHA_HOME}/voyager/models/* || echo okay) && \
  : FINAL SIZE && \
      du -sh ${AHA_HOME}

# Pono
WORKDIR ${AHA_HOME}
COPY ./pono ${AHA_HOME}/pono
COPY ./aha/bin/setup-smt-switch.sh ${AHA_HOME}/pono/contrib/
RUN mkdir -p ${AHA_HOME}/contrib/pono-hack
ADD ./aha/bin/pono-hack ${AHA_HOME}/pono/contrib/pono-hack
WORKDIR ${AHA_HOME}/pono
# Note must pip install Cython *outside of* aha venv else get tp_print errors later :o
RUN \
     ls -l ${AHA_HOME}/pono/contrib/pono-hack/ && \
 : SETUP && \
     pip install Cython==0.29 pytest toml scikit-build==0.13.0 && \
 : FLEX && \
     apt-get update && apt-get install -y flex && \
 : BISON && \
     echo "# Cannot use standard dist bison 3.5, must have 3.7 or better :(" && \
     ./contrib/setup-bison.sh                                     && \
     echo "# bison cleanup ${AHA_HOME}/pono 77M => 48M"                  && \
     (cd ${AHA_HOME}/pono/deps/bison; make clean; /bin/rm -rf src tests) && \
 : SMT-SWITCH && \
     ./contrib/pono-hack/pono-hack.sh --install && \
     ./contrib/setup-smt-switch.sh --python && \
     ./contrib/pono-hack/pono-hack.sh --uninstall && \
     :                                                 && \
     echo "# cleanup: 1.3GB smt-switch build tests"    && \
     /bin/rm -rf ${AHA_HOME}/pono/deps/smt-switch/build/tests && \
     :                                                           && \
     echo "# cleanup: 700M smt-switch deps (cvc5,bitwuzla,btor)" && \
     /bin/rm -rf ${AHA_HOME}/pono/deps/smt-switch/deps                  && \
     :                                                                 && \
     echo "# cleanup: 200M intermediate builds of cvc5,bitwuzla,btor"  && \
     /bin/rm -rf ${AHA_HOME}/pono/deps/smt-switch/build/{cvc5,bitwuzla,btor} && \
 : BTOR2TOOLS && \
    ./contrib/setup-btor2tools.sh && \
  : PIP INSTALL && \
     cd ${AHA_HOME}/pono && ./configure.sh --python && \
     cd ${AHA_HOME}/pono/build && make -j4 && pip install -e ./python && \
     cd ${AHA_HOME} && \
       source ${AHA_HOME}/bin/activate && \
       pip install -e ./pono/deps/smt-switch/build/python && \
       pip install -e pono/build/python/

# CoreIR
WORKDIR ${AHA_HOME}
COPY ./coreir ${AHA_HOME}/coreir
WORKDIR ${AHA_HOME}/coreir/build
RUN cmake .. && make && make install && /bin/rm -rf src bin tests

# Lake
COPY ./BufferMapping ${AHA_HOME}/BufferMapping
WORKDIR ${AHA_HOME}/BufferMapping/cfunc
RUN export COREIR_DIR=${AHA_HOME}/coreir && make lib

# mflowgen
ENV GARNET_HOME=${AHA_HOME}/garnet
ENV MFLOWGEN=${AHA_HOME}/mflowgen

# Install torch (need big tmp folder)
WORKDIR ${AHA_HOME}
RUN source ${AHA_HOME}/bin/activate && \
  export TMPDIR=${AHA_HOME}/tmp/torch_install && mkdir -p $TMPDIR && \
  pip install --cache-dir=$TMPDIR --build=$TMPDIR torch==1.7.1+cpu -f https://download.pytorch.org/whl/torch_stable.html && \
  echo "# Remove 700M tmp files created during install" && \
  rm -rf $TMPDIR

# clockwork
COPY clockwork ${AHA_HOME}/clockwork
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

# Halide-install step, below, modified to delete 1G of clang when finished.
# Clang will be restored by way of .bashrc (aha/bin/docker-bashrc).

# Halide-to-Hardware - Step 32/65 ish - requires clang
COPY ./Halide-to-Hardware ${AHA_HOME}/Halide-to-Hardware
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

# 10MB (COPY) + 210 MB (RUN) maybe
# Sam - build sam from the vendored source tree
COPY ./sam ${AHA_HOME}/sam
RUN echo "--- ..Sam" && cd ${AHA_HOME}/sam && make sam && \
  source ${AHA_HOME}/bin/activate && pip install scipy numpy pytest && pip install -e .

# cgra_pnr
COPY ./cgra_pnr ${AHA_HOME}/cgra_pnr
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

# Install Miniconda, needed by voyager
ENV CONDA_DIR=/opt/conda
RUN curl -sSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh \
    && bash miniconda.sh -b -p $CONDA_DIR \
    && rm miniconda.sh \
    && $CONDA_DIR/bin/conda clean -afy

# Make conda globally available
ENV PATH=$CONDA_DIR/bin:$PATH

# # Voyager 0 - voyager misc
# RUN echo "--- ..Voyager step 0"

# Install additional dependencies for building C++ code
RUN mkdir -p /usr/include/sys && \
    curl -o /usr/include/sys/cdefs.h https://raw.githubusercontent.com/lattera/glibc/2.31/include/sys/cdefs.h


# FIXME
# Voyager 1 temporarily moved to beginning of file for debugging, see above
# If we don't see git clone voyager errors before say, a month from now (Oct 16), can move it back maybe

# Voyager 2 - setup voyager
# Bring in local changes on top of base clone
COPY ./voyager ${AHA_HOME}/voyager

# Cannot do 'git lfs' now that we have delete voyager git history
# User will have to do this manually in the container when/if desired
# 
# bashrc is going to have to do this maybe, in the future...
# RUN echo "--- ..Voyager step 2"
# WORKDIR ${AHA_HOME}/voyager
# RUN git lfs install
# RUN cd ${AHA_HOME}/voyager && git lfs pull
# RUN echo "--- DU.MODELS2" && (du -sh ${AHA_HOME}/voyager/models/* || echo okay)

# RUN cd ${AHA_HOME}/voyager
# RUN source ${AHA_HOME}/bin/activate && conda env create -p .conda-env -f environment.yml && \
#     export ORIGINAL_PATH="$PATH" && conda init && eval "$(conda shell.bash hook)" && \
#     conda activate ${AHA_HOME}/voyager/.conda-env && \
#     cd ${AHA_HOME}/voyager/quantized-training && pip install -r requirements.txt && pip install -e . && \
#     cd ${AHA_HOME}/voyager && pip install quantized-training && \
#     source env.sh && \
#     conda deactivate && export PATH="$ORIGINAL_PATH"

# ------------------------------------------------------------------------------
# Final pip installs: AHA Tools etc.

# Note kratos is slow but stable; maybe it should be installed much earlier in dockerfile

# For "aha deps install"; copy all the modules that not yet been copied
COPY ./archipelago ${AHA_HOME}/archipelago
COPY ./ast_tools ${AHA_HOME}/ast_tools
COPY ./canal ${AHA_HOME}/canal
COPY ./cosa ${AHA_HOME}/cosa
COPY ./fault ${AHA_HOME}/fault
COPY ./garnet ${AHA_HOME}/garnet
COPY ./gemstone ${AHA_HOME}/gemstone
COPY ./hwtypes ${AHA_HOME}/hwtypes
COPY ./kratos ${AHA_HOME}/kratos
COPY ./lake ${AHA_HOME}/lake
COPY ./lassen ${AHA_HOME}/lassen
COPY ./magma ${AHA_HOME}/magma
COPY ./mantle ${AHA_HOME}/mantle
COPY ./MetaMapper ${AHA_HOME}/MetaMapper
COPY ./mflowgen ${AHA_HOME}/mflowgen
COPY ./peak ${AHA_HOME}/peak
COPY ./peak_generator ${AHA_HOME}/peak_generator
COPY ./pycoreir ${AHA_HOME}/pycoreir
COPY ./Lego_v0 ${AHA_HOME}/Lego_v0

# Install aha tools ${AHA_HOME}/aha/
COPY ./setup.py ${AHA_HOME}/setup.py
COPY ./aha ${AHA_HOME}/aha

# Need z3-solver b/c hwtypes :(

# Find and copy cached z3-solver wheel collateral if available.
# Including known file (setup.py) prevents COPY error when/if cache file don't exist
COPY ./setup.py z3_solver-4.16.0.0-py3-none-linux_x86_64.whl* /tmp/
COPY ./setup.py libz3.so*  /tmp/

# Install z3 solver, this is kind of a mess isnt it
# FIXME can remove cachebuster in future cleanups
RUN : z3 solver && echo temp-cachebuster && \
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
        pip install /tmp/z3_solver-4.16.0.0-py3-none-linux_x86_64.whl && \
        mv /tmp/libz3.so* ${AHA_HOME}/lib/python3.8/site-packages/z3/lib/libz3.so || exit 13; \
    else \
        : Install z3-solver from scratch && \
        cd ${AHA_HOME} && source bin/activate && \
        pip install z3-solver || exit 13; \
    fi && \
    \
    : This installs necessary updates for libstdc++.so.6 maybe, needed by z3 maybe; \
    apt-get install -y libc6-dev-amd64 || apt-get install -y libc6-dev && \
    apt-get update && apt-get install -y linux-headers-generic && \
    ln -s /usr/include/asm-generic/ /usr/include/asm && \
    \
    : pythunder install breaks during final 'aha deps install' if use gcc-13; \
    : So reset back to gcc-9 again; \
    apt-get install -y gcc-9 g++-9 && \
    (update-alternatives --remove-all gcc || echo okay) && \
    (update-alternatives --remove-all g++ || echo okay) && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 100 \
                        --slave   /usr/bin/g++ g++ /usr/bin/g++-9 \
    || exit 13; \
    echo z3-solver DONE

RUN : Final aha deps install && \
  cd ${AHA_HOME} && source bin/activate && \
  type gcc && type cmake && gcc --version && cmake --version && z3 --version; \
  pip install -e . && \
  aha deps install

# This should go as late in Docker file as possible; it brings
# in EVERYTHING. Anything from here on down CANNOT BE CACHED.
WORKDIR ${AHA_HOME}
COPY . ${AHA_HOME}

ENV OA_UNSUPPORTED_PLAT=linux_rhel60
ENV USER=docker

# Add startup instructions to existing /root/.bashrc
# 1. Create a /root/.modules so as to avoid this warning on startup:
#    "+(0):WARN:0: Directory '/root/.modules' not found"
# 2. Tell user how to restore gch headers.
#
# Also: Final dotfile cleanup, just in case
RUN \
  echo 'source "${AHA_HOME}/aha/bin/docker-bashrc"' >> /root/.bashrc && \
  /bin/rm -rf ${AHA_HOME}/.git/modules/{clockwork,Halide-to-Hardware,voyager} && \
  echo DONE

# Restore halide distrib files on every container startup
ENTRYPOINT [ "/bin/bash", "-lc", "exec \"$AHA_HOME/aha/bin/restore-halide-distrib.sh\" \"$@\"", "--" ]

# Cleanup / image-size-reduction notes:
#
# - cannot delete `clockwork/barvinok` directory entirely because
#   regression tests use e.g. `barvinok-0.41/isl/isl_ast_build_expr.h`
#
# - if you don't delete files in the same layer (RUN command) where
#   they were created, you don't get any space savings in the image.
#
# - cannot do "make clean" in `${AHA_HOME}/pono/deps/smt-switch/build`,
#   because it deletes `smt-switch/build/python`, which is where
#   smt-switch is pip-installed :(
#   This should probably be an issue or a FIXME in pono or something.
