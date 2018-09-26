#!/bin/bash

# source:
# https://www.jamf.com/jamf-nation/discussions/22170/script-to-disable-pop-up-blocker-in-safari

defaults write com.apple.Safari com.apple.Safari.ContentPageGroupIdentifier.WebKit2JavaScriptCanOpenWindowsAutomatically 1
