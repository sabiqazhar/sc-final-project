# Final Project Team Zeus

Final Project BE X AI

## Pre-work

- Make sure you already install wsl 2 (if you are using windows), docker and docker-compose

## Clone repository

In your Visual Studio Code

```
cd <base_folder_path>
git clone https://gitlab.com/tristanpratama7/final-project.git
```

## Python installation

To install python 3.9, [follow this instruction](https://linuxhint.com/install-python-ubuntu-22-04/).

After completing the installation, check that Python is already installed by running

```
which python3.9
```

Then, you need to install [pip](https://pypi.org/project/pip/) which will be used to install other useful Python packages

```
sudo apt install python3.9-distutils
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.9 get-pip.py

# clean up the installation file
rm get-pip.py
```

Finally, check that the pip is installed by running

```
which pip3.9
```

## Virtual environment

After installing Python, **enable virtual environment** to _isolate your working environment_ as you might use different set of Python packages and versions for other projects.

First, run the following

```
sudo apt-get install python3-venv
python3.9 -m pip install virtualenv
```

Then choose **a name for your environment**. For instance, if the environment name is `startup-campus` then run the following

```
cd <working_folder_path>
python3.9 -m venv final-project
```

To start using your new environment, run the following command

```
source <environment_name>/bin/activate
cd to root_folder
pip3.9 install -r requirements.txt
```

If it's successfull, you will see `[environment_name]` on the left side

Make sure that you are using this environment when you are working on your locally.

To stop using virtual environment, just run

```
deactivate
```

and check that the prefix `[environment_name]` is now gone as well.

## Testing

To test locally, go to the relative path

```
cd app
```

then run

```
python3.9 tester.py
```

you will be able to see details regarding the performance of your code and overall test for this project.
