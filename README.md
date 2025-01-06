### Purpose of project

Flatten a github repo or a project directory into a text file for querying LLMs.

Base usage:
```bash
python Flatten.py https://github.com/pypa/pip
```
Prints filenames + contents to stdout; you can either save (>>) or pipe to clipboard (| clip).
