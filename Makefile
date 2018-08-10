# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

SHELL := /bin/bash

all: lint test

.PHONY: lint-ansible
lint-ansible:
	cd provisioning/configuration && \
		ansible-playbook --syntax-check provision.yml

.PHONY: lint-python
lint-python: .deps
	pycodestyle .

.PHONY: lint
lint: lint-python lint-ansible

.PHONY: test
test: .deps
	python -m unittest discover -p '*_test.py'

.deps: requirements.txt
	pip install -r requirements.txt
	touch .deps

provisioning/infrastructure/.initialized:
	cd provisioning/infrastructure && terraform init

.PHONY: deploy
deploy: provisioning/infrastructure/.initialized
	cd provisioning/infrastructure && \
		terraform apply
	cd provisioning/configuration && \
		ansible-playbook -i inventory/production provision.yml
