#!/bin/bash
set -e

# Ensure required tools are installed
sudo apt-get update
sudo apt-get install -y autoconf automake libtool

# Update autoconf macros and files
autoupdate

# Add m4_pattern_allow to configure.ac if missing
if ! grep -q "m4_pattern_allow([LT_SYS_SYMBOL_USCORE])" configure.ac; then
  echo 'm4_pattern_allow([LT_SYS_SYMBOL_USCORE])' | cat - configure.ac > temp && mv temp configure.ac
fi

# Regenerate configuration scripts
autoreconf -fi

# Stage and commit changes
git add configure.ac aclocal.m4
git commit -m "Automated autoconf fixes for build errors"

echo "Autoconf corrections applied and committed."
