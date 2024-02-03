# Jupyter Notebooks
Full documentation: https://jupyter-docker-stacks.readthedocs.io

## Starting an ephemeral server
Click the link shown in the display to open the browser.
```bash
docker run --rm \
  -p 8888:8888 \
  -v "${PWD}":/home/jovyan/work \
  quay.io/jupyter/datascience-notebook \
  start-notebook.py --ServerApp.root_dir=/home/jovyan/work
```

To install the project, use:

```bash
pip install -e ~/work/
```
