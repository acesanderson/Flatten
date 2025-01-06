### Purpose of project

Flatten a github repo or a project directory into a text file for querying LLMs.

Base usage:
```bash
python Flatten.py https://github.com/acesanderson/Chain
```
Prints filenames + contents to stdout; you can either save (>>) or pipe to clipboard (| clip).
