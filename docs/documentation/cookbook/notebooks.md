# Jupyter Notebooks
Full documentation: https://jupyter-docker-stacks.readthedocs.io

## Native
Installing JupyterLab and a few useful plugins.

```bash
pip install -U jupyterlab jupyterlab-execute-time jupyterlab-git ipywidgets
```

Installing a kernel.

```bash
python -m ipykernel install --user --name NAME --display-name DISPLAY_NAME
```

## Dockerized
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
