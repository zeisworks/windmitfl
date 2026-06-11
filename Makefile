.PHONY: build draft verify serve clean

# Production build: skips any county whose required fields are unverified.
build:
	python3 build.py

# Draft build: renders unverified counties too (noindex, unverified fields omitted).
draft:
	python3 build.py --draft

# Research worklist: every NEEDS_VERIFICATION field across all data files.
verify:
	python3 verify.py

serve:
	python3 -m http.server 8000 --directory output

clean:
	rm -rf output
