.PHONY: setup main main_no_proxy distclean load_config_rooted_phone load_config_jailed_phone load_config_2461 config_enable_trainer config_disable_trainer

setup:
	brew install python pipx jq
	pipx install poetry
	pipx run poetry install

main:
	pipx run poetry run main

main_no_proxy:
	pipx run poetry run main --no_proxy

distclean:
	-pipx run poetry env remove python
	-git clean -dfx

load_config_rooted_phone:
	mkdir -p tmp
	jq --indent 4 ".use_su = true | .use_gadget = false" conf/config.json > tmp/config.json
	mv tmp/config.json conf/config.json

load_config_jailed_phone:
	mkdir -p tmp
	jq --indent 4 ".use_su = false | .use_gadget = true" conf/config.json > tmp/config.json
	mv tmp/config.json conf/config.json

load_config_2461:
	mkdir -p tmp
	jq --indent 4 ".use_su = false | .use_gadget = false" conf/config.json > tmp/config.json
	mv tmp/config.json conf/config.json

config_enable_trainer:
	mkdir -p tmp
	jq --indent 4 ".enable_trainer = true" conf/config.json > tmp/config.json
	mv tmp/config.json conf/config.json

config_disable_trainer:
	mkdir -p tmp
	jq --indent 4 ".enable_trainer = false" conf/config.json > tmp/config.json
	mv tmp/config.json conf/config.json
