---
id: DzqCaKjSR48BKglam9x5
name: Version management across modules and files
file_version: 1.0.1
app_version: 0.6.1-1
file_blobs:
  setup.py: 7bfd510e39ea464f79902ae3077eb62b43c82b9e
  about.py: 6fecd5c7f927fafc7d742b2f3473b556da5b37d0
---


<!-- NOTE-swimm-snippet: the lines below link your snippet to Swimm -->
### 📄 setup.py
```python
⬜ 4      
⬜ 5      from setuptools import setup
⬜ 6      
🟩 7      about = {}
🟩 8      here = os.path.abspath(os.path.dirname(__file__))
🟩 9      with open(os.path.join(here, "about.py"), "r", encoding="utf-8") as f:
🟩 10         exec(f.read(), about)
⬜ 11     
⬜ 12     with open("README.md", "r", encoding="utf-8") as f:
⬜ 13         readme = f.read()
```

<br/>

<!-- NOTE-swimm-snippet: the lines below link your snippet to Swimm -->
### 📄 about.py
```python
⬜ 5      __license__ = "MIT License"
⬜ 6      __title__ = "cdk-chalice"
⬜ 7      __url__ = "https://github.com/alexpulver/cdk-chalice"
🟩 8      __version__ = "0.9.0"
🟩 9      
```

<br/>

This file was generated by Swimm. [Click here to view it in the app](https://swimm.io/link?l=c3dpbW0lM0ElMkYlMkZyZXBvcyUyRnlxdEJRWmdtSzhqMGhRTlI3M29EJTJGZG9jcyUyRkR6cUNhS2pTUjQ4QktnbGFtOXg1).