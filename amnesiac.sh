#!/bin/bash

for workername in george sally; do
  sudo -u $workername buildbot-worker stop /home/$workername/worker
done

sudo mkdir -p /mnt/fake-repo
(
  cd /mnt/fake-repo
  git init
  git config user.email a
  git config user.name b
  cp /vagrant/fake-wpt wpt
  git add --all .
  git commit --allow-empty -m 'f'
)

systemctl stop buildbot-master.service

rm -rf /mnt/buildmaster-db/buildbot-state.sqlite
(
  cd /home/wptdmaster
  sudo rm -r chunk-results
  sudo rm master/buildbot.tac master/twistd.log*
)
rm -rf /home/wptdmaster/master/buildbot.tac

cp /vagrant/src/scripts/* /usr/local/bin/

sudo -u wptdmaster \
  cp /vagrant/src/master/* \
    /home/wptdmaster/master/

sudo -u wptdmaster buildbot create-master /home/wptdmaster/master
sudo -u wptdmaster buildbot upgrade-master /home/wptdmaster/master

for workername in george sally; do
  sudo -u $workername buildbot-worker start /home/$workername/worker
done

systemctl start buildbot-master.service

tail -F /home/wptdmaster/master/twistd.log
