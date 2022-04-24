# (PoC) 'Arkive' multi-provider archival API

A simple API to quickly and easily archive an url to multiple providers.

## 0.0.1 PoC Milestone requirements:
- DONE ~user is able to submit a website by e.g. navigating to `arkive.ml/https://www.theonion.com/the-onion-guide-to-tipping-1848821007`~
- DONE ~submitted urls are saved to an sqlite db with the original url and the archived url~
- DONE ~API returns the archived url in a json response~
- DONE ~remove any URL schemas like `http://` .. etc to avoid duplicates in DB~
- DONE ~working archive.org provider implemented~


## Planned features
- TODO [#A] use [freeze-dry](https://github.com/WebMemex/freeze-dry) to save a single file copy of the page to `$freezedry_dir`
- TODO first just store url, then add archive urls to record later
- TODO add more providers
