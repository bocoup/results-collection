#!/bin/bash

# Running the Web Platform Tests involves mofidying the system "hosts" file.
# This file write-proetect, so supporting modification by non-root users
# requires dedicated affordances.
#
# This simple script is defined so non-root users can be granted permission
# to modify the system hosts file via `sudo`.

tee /etc/hosts
