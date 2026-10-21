PYTHON ?= python3
NODE ?= node

.PHONY: all run run-original test verify probes clean docs docs-html docs-watch docs-check test-docs

all:
	$(PYTHON) scripts/restore_c16.py

run: all
	$(PYTHON) scripts/run_vice.py

run-original:
	$(PYTHON) scripts/run_vice.py --original

test:
	$(PYTHON) -m unittest discover -s test -p 'test_*.py' -v

verify: all
	$(PYTHON) scripts/verify_vice.py

probes: verify
	$(PYTHON) scripts/probe_gameplay_rules.py

clean:
	rm -rf build .pio
