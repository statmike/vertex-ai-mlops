![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FTips&file=Python+Environments.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Tips/Python%20Environments.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# /Tips/Python Environment.md

You installed Python (or it was already installed), then pip installed some packages, and now run some code.  Everything is great!  

What happens when you need to use multiple versions of Python in the same environment?
>Answer: [pyenv](https://github.com/pyenv/pyenv)

What do you do when you want to install a package without having it's dependencies requirments mess up other packages?
>Answer: [virtualenv](https://virtualenv.pypa.io/en/latest/)

What do you do when you want to install different packages or package versions with the same, or different, versions of Python?
>Answer: [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) combines the concepts of both!

---

## Managing Python Versions: `pyenv`

### Install `pyenv`

First, [install pyenv](https://github.com/pyenv/pyenv-installer#install):

`curl https://pyenv.run | bash`

Then, set up your shell environment using [these instructions](https://github.com/pyenv/pyenv#set-up-your-shell-environment-for-pyenv):
My steps in this Vertex AI User Managed Workbench Enviornment which uses `bash`:

```
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
```

Listing the contents of home with `ls -a ~/` show that none of these exists: `~/.profile`, `~/.bash_profile`, `~/.bash_login`
The instruction say create `~./profile` in this situation with:

```
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
echo 'eval "$(pyenv init -)"' >> ~/.profile
```

Restart the terminal with `exec $SHELL` or close the terminal and open a new one.

Later, update pyenv with `pyenv update`.

### Use `pyenv`: list version, install more versions

List installed versions with `pyenv versions`.  Initially, only the main system Python is installed.  Check its version with `python --version`.

Install an additional python version with `pyenv install 3.10.0`

>It might be necessary to first install Python's binary dependencies.  See [Common build problems](https://github.com/pyenv/pyenv/wiki/Common-build-problems).
>This is typically done with apt:
>```
>sudo apt update; sudo apt install build-essential libssl-dev zlib1g-dev \
>libbz2-dev libreadline-dev libsqlite3-dev curl \
>libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
>```

List installed versions again with `pyenv versions` and you should now see multiple versions:
```
* system (set by /home/jupyter/.pyenv/version)
  3.10.0
```

### Use `pyenv`: set the local or global Python version

When you use Python, the currently set version is used to run your code.  Now that pyenv is installed an a new version, 3.10.0, is also installed, you can switch the default version.

The scope of the switch can be one of three:
- shell: `pyenv shell <version>`
    - a shell specific version of Python that only persist for the life of the shell
- global: `pyenv global <version>`
    - sets the default version on Python for your enviornment.  This is overridden by local and shell.
- local: `pyenv local <version>`
    - set the application (current folder and subfolder) version of Python.  This actually creates a `.profile` file in the current folder so that all Python session at this level and in subfolder use the stated version of Python.  **NOTE:** This overrides global.

To revert back to the system Python install:
`pyenv global system` and also, if you set local, `python local system`

#### Impact on Jupyter Kernel

When you choose Python as the Jupyter Kernel it will use the local Python version.  That means, at the time of starting the kernel, whatever the `pyenv local <version>` is, or if not defined the `pyenv global <version>`, will apply.  You can check this by running a cell with `!python -V` or `!pyenv versions`.

---
## Managing Python Packages: `virtualenv`

Whichever Python version is current can have multiple virtual environemnts for different packages and package version using [virtualenv](https://virtualenv.pypa.io/en/latest/). 

### Install `virtualenv`

Note that this will install `virtualenv` for the current active `pyenv` if you are using it to manage Python versions.

```
pip install virtualenv
```

### Define a `virtualenv`

This will create a folder in the local directory with the name `<name-env>`.

```
virtualenv <name-env>
```

### Activate a `virtualenv`

Once activated, the current version on Python will run with this virtual environment.  If running a Jupyter notebook, the kernel for Python will startup with the current version of Python which will include a currently activated `virtualenv`.

```
source <name-env>/bin/activate
```

### Check For Currently Activated `virtualenv`

```
echo $VIRTUAL_ENV
```

or, note the active install location for `pip` with:

```
pip -V
```

### Install Packages in `virtualenv`

```
<name-env>/bin/pip.exe install name-of-package
```

### Deactive a `virtualenv`

```
deactivate
```


---
## Managing  Python Versions and Packages Together: `pyenv-virtualenv`

The concepts above with `pyenv` and `virtualenv` can actually be used together for when you want to manage multiple virtual versions of the same Python installation by using a plugin for `pyenv` called `pyenv-virtualenv`.  Learn more about it [here](https://github.com/pyenv/pyenv-virtualenv).

### Install `pyenv-virtualenv` plugin

```
git clone https://github.com/pyenv/pyenv-virtualenv.git $(pyenv root)/plugins/pyenv-virtualenv
source ~/.bashrc
```

### Create a `pyenv-virtualenv`

```
pyenv virtualenv <python-version> <name-env>
```

### List `pyenv-virtualenv`

The `pyenv-virtualenv` environments are list like Python versions with `pyenv`:

```
pyenv versions
```

### Activate a `pyenv-virtualenv`

The scopes of `pyenv` still apply: `shell`, `local`, `global`, the syntax is even the same for activating a `pyenv-virtualenv` as it is for regular `pyenv`. 

```
pyenv <scope> <name-env>
```

### Deactivate a `pyenv-virtualenv`

This will deactivate the pyenv-virtualenv but note that the active version of Python will still be determined by `pyenv` and can be reviewed with `pyenv versions`.

```
pyenv deactivate
```

Read [more on usage](https://github.com/pyenv/pyenv-virtualenv#usage) of `pyenv-virtualenv`.