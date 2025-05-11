# Jupyter Notebooks

## Native
Installing JupyterLab and a few useful plugins.

```bash
pip install -U jupyterlab \
  ipywidgets \
  jupyterlab-execute-time jupyterlab-git \
  jupyterlab-code-formatter black isort
```

Installing a kernel.

* Using `rics kernel`
  ```bash
  rics kernel
  ```
  May also be invoked using `python -m rics kernel`. This will install the venv of the current project as a kernel,
  using sane defaults. The name will be something like `rics-py3.11 [poetry]`.


* Using `ipykernel`
  ```bash
  python -m ipykernel install --user --name NAME --display-name DISPLAY_NAME
  ```
  This will install whatever `python` refers to as a kernel.


## Dockerized
Click the link shown in the display to open the browser.
```bash
docker run --rm \
  -p 8888:8888 \
  -v "${PWD}":/home/jovyan/work \
  quay.io/jupyter/datascience-notebook \
  start-notebook.py --ServerApp.root_dir=/home/jovyan/work
```
To install the project, run:
```bash
pip install -e ~/work/
```
Full documentation: [https://jupyter-docker-stacks.readthedocs.io](https://jupyter-docker-stacks.readthedocs.io).
