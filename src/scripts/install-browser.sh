#!/bin/bash

set -e

if [ $1 == 'chrome' ]; then
  install_chrome $2
elif [ $1 == 'firefox' ]; then
  install_firefox $2
fi

install_chrome() {
  url=$1
  deb_archive=google-chrome.deb

  wget --quiet --output-document $deb_archive $url

  # If the environment provides an installation of Google Chrome, the
  # existing binary may take precedence over the one introduced in this
  # script. Remove any previously-existing "alternatives" prior to
  # installation in order to ensure that the new binary is installed as
  # intended.
  if update-alternatives --list google-chrome; then
    update-alternatives --remove-all google-chrome
  fi

  # Installation will fail in cases where the package has unmet dependencies.
  # When this occurs, attempt to use the system package manager to fetch the
  # required packages and retry.
  if ! dpkg --install $deb_archive; then
    apt-get install --fix-broken
    dpkg --install $deb_archive
  fi

  rm $deb_archive

  which google-chrome
}

install_firefox() {
  url=$1
  archive=firefox.tar.gz
  wget --quiet --output-document $archive $url


  echo ~/firefox/firefox
}
