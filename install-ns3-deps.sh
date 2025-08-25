#!/bin/bash
# install-ns3-deps.sh
# Instala dependências para compilar o ns-3 com bindings Python no Ubuntu (22.04/24.04)

set -euo pipefail

if ! command -v sudo >/dev/null 2>&1; then
  echo "Este script requer 'sudo'. Instale/ative sudo e tente novamente."
  exit 1
fi

echo "[*] Atualizando índices do apt..."
sudo apt update -y

echo "[*] Instalando dependências do ns-3..."
sudo apt install -y \
  build-essential \
  cmake \
  g++ \
  gcc \
  pkg-config \
  python3 \
  python3-dev \
  python3-pip \
  python3-setuptools \
  python3-numpy \
  python3-pybind11 \
  git \
  ninja-build \
  qtbase5-dev \
  qtchooser \
  qt5-qmake \
  qtbase5-dev-tools \
  mercurial \
  uncrustify \
  openmpi-bin \
  openmpi-common \
  openmpi-doc \
  libopenmpi-dev \
  autoconf \
  automake \
  libtool \
  libsqlite3-dev \
  libxml2-dev \
  libgtk-3-dev \
  libboost-all-dev \
  gsl-bin \
  libgsl-dev \
  libgslcblas0 \
  libpcap-dev \
  libxerces-c-dev \
  ccache \
  clang \
  valgrind \
  doxygen \
  graphviz

echo "[✓] Dependências instaladas com sucesso."
echo
echo "Dicas:"
echo "  • Para compilar o ns-3 com Python bindings:"
echo "      ./ns3 configure --enable-python --enable-examples --enable-tests"
echo "      ./ns3 build"
echo
