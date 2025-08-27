.PHONY: setup main main_no_proxy distclean

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
