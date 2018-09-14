#!/bin/bash

# This script ensures that the "Enable Remote Automation" feature of Apple
# Safari is enabled. If it is not enabled, it attempts to do so using Apple's
# UI scripting language. If this fails, the script exits with a non-zero exit
# code.
#
# While the `safaridriver` binary offers an `--enable` flag [1], that feature
# alone is not sufficient to enable remote automation in fully-automated
# contexts.
#
# [1]  https://developer.apple.com/documentation/webkit/testing_with_webdriver_in_safari

set -e

if [ $1 == "stable" ]; then
  browser_name="Safari"
  safaridriver_binary="/usr/bin/safaridriver"
else
  browser_name="Safari Technology Preview"
  safaridriver_binary="/Applications/Safari Technology Preview.app/Contents/MacOS/safaridriver"
fi

# Create a session using a body which satisfies both the Selenium JSON Wire
# protocol (for Safari 11.1 and earlier) and the W3C WebDriver protocol (for
# Safari 12 and later).
create_session() {
  curl \
    -X POST \
    --verbose \
    --data '{"capabilities":{},"desiredCapabilities":{}}' \
    --fail \
    http://localhost:9876/session
}

is_automation_enabled() {
  "$safaridriver_binary" --port 9876 &
  stp_pid=$!

  # Pause until safaridriver's HTTP server is confirmed to be available.
  # Although querying the `/status` endpoint would be the most method,
  # safaridriver for Safari version 11.1 and earlier does not support it [1].
  # Instead, send a GET request to the `/session` endpoint, as a response code
  # of 405 will reliably indicate that either implementation is ready.
  while true ; do
    status_code=$(curl \
        --silent \
        --output /dev/null \
        --write-out '%{http_code}' \
        http://localhost:9876/session \
      || true)
    echo $status_code
    if [ "$status_code" == "405" ]; then
      break
    fi

    if ! kill -0 $stp_pid > /dev/null 2>&1; then
      return 1
    fi
  done

  create_session >&2
  result=$?

  kill -9 $stp_pid >&2
  wait $stp_pid >&2 2> /dev/null

  return $result
}

toggle_automation() {
  echo Toggling automation in Safari

  osascript - <<SCRIPT
  activate application "$browser_name"

  tell application "System Events"
      set ready to false

      repeat while not ready
          repeat with this_process in every process
              if name of this_process as string is "$browser_name" then
                  set ready to true
              end if
          end repeat
      end repeat

      -- If Apple offers a version of Safari Technology Preview which is newer than
      -- the one under test, the browser will create a modal dialog shortly after
      -- opening. The following block pauses execution until this prompt is expected
      -- to be available. This delay represents an unavoidable race condition as
      -- there is no deterministic method to verify that the prompt will *not* be
      -- displayed.
      tell process "$browser_name"
          log "Waiting for upgrade prompt..."
          delay 2

          repeat with current_window in every window
              if exists button "Not Now" of current_window then
                  log "Found upgrade prompt. Dismissing."
                  click button "Not Now" of current_window
                  exit repeat
              end if
          end repeat

          click menu item "Allow Remote Automation" of menu "Develop" of menu bar item "Develop" of menu bar 1
      end tell
  end tell

  tell application "$browser_name" to quit
SCRIPT
}

if ! is_automation_enabled; then
  echo Automation not enabled. Attempting to enable. >&2
  toggle_automation >&2

  # This command has been found to function as expected only *after* automation
  # has been enabled via the Safari user interface.
  "$safaridriver_binary" --enable >&2
fi

if ! is_automation_enabled; then
  echo Unable to enable automation >&2
  exit 1
fi

echo $safaridriver_binary
