# `english_event_extractor`

This package also uses the following paper and its corresponding C++ source package: JEE

Joint Extraction of Events and Entities within a Document Context (NAACL-HLT 2016)

Yang and Mitchell Carnegie Mellon University

https://www.aclweb.org/anthology/N16-1033
https://github.com/bishanyang/EventEntityExtractor

It was trained on ACE05.


## Setup
### Using Docker
```
docker pull ciaochiaociao/event_en:0.2
git clone https://github.com/ciaochiaociao/english_event_extractor.git <repo_dir>
docker run -d --rm --name event_en -v <repo_dir>:/workspace/event_en -w /workspace/event_en -p 5012:5000 ciaochiaociao/event_en:0.2 python3 -m event_extractor.server
```
