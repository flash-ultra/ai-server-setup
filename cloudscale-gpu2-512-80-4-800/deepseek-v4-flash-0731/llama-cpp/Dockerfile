# llama.cpp for DeepSeek-V4-Flash-0731 on RTX PRO 6000 Blackwell (sm120)
#
#   docker build --build-arg LLAMA_COMMIT=$(git ls-remote \
#       https://github.com/ggml-org/llama.cpp.git HEAD | cut -f1) \
#       -t llamacpp-sm120:local .
#
# Builds for compute capability 120 only. A single-architecture build finishes in
# under two minutes on 80 cores, so there is little reason to ship a generic
# multi-arch binary here.

ARG CUDA_TAG=13.0.1-devel-ubuntu24.04
FROM nvidia/cuda:${CUDA_TAG}

RUN apt-get update && apt-get install -y --no-install-recommends \
      git cmake ninja-build build-essential libcurl4-openssl-dev ccache python3 \
    && rm -rf /var/lib/apt/lists/*

# libcuda.so.1 ships with the driver, not the toolkit. Without this symlink and the
# rpath-link below, linking fails with "undefined reference to cuMemCreate". The stub
# is link-time only — at runtime the container gets the real library from the host.
RUN ln -sf /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1

ARG LLAMA_COMMIT=master
RUN git clone https://github.com/ggml-org/llama.cpp /src \
 && cd /src \
 && git checkout ${LLAMA_COMMIT} \
 && (echo "commit:  $(git rev-parse HEAD)"; \
     echo "date:    $(git log -1 --format=%cd)"; \
     echo "subject: $(git log -1 --format=%s)") > /build-info.txt

WORKDIR /src
RUN cmake -B build -G Ninja \
      -DGGML_CUDA=ON \
      -DCMAKE_CUDA_ARCHITECTURES=120 \
      -DCMAKE_BUILD_TYPE=Release \
      -DLLAMA_CURL=ON \
      -DGGML_CUDA_FA_ALL_QUANTS=ON \
      -DLLAMA_BUILD_TESTS=OFF \
      -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath-link,/usr/local/cuda/lib64/stubs -L/usr/local/cuda/lib64/stubs" \
      -DCMAKE_SHARED_LINKER_FLAGS="-Wl,-rpath-link,/usr/local/cuda/lib64/stubs -L/usr/local/cuda/lib64/stubs" \
 && cmake -LAH build > /cmake-options.txt 2>&1 || true

RUN cd /src && cmake --build build --config Release -j$(nproc) \
 && cmake --install build --prefix /opt/llama \
 && (nvcc --version | tail -2) >> /build-info.txt \
 && (gcc --version | head -1) >> /build-info.txt \
 && echo "cuda_arch: 120" >> /build-info.txt

ENV PATH=/opt/llama/bin:$PATH
ENV LD_LIBRARY_PATH=/opt/llama/lib:/usr/local/cuda/lib64:$LD_LIBRARY_PATH
WORKDIR /opt/llama/bin

# Build identity is readable from the image:
#   docker run --rm llamacpp-sm120:local cat /build-info.txt
