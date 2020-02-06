# python-pmc-pubone-client

## Install

### Regular use _(assuming that you've already published your package on NCBI Artifactory PyPI)_:

```sh
pip install pmc-pubone-client  # or add it to your requirements file
```

### For development:

Before you run scripts from misc/ folder make sure you 
installed pipenv independently of your virtual environments, 
for example you may want to consider using `pipx` 
to install various python package/scripts in kind 
of `standalone` mode.

```sh
git clone ssh://git@bitbucket.be-md.ncbi.nlm.nih.gov:9418/pmc/python-pmc-pubone-client.git
cd python-pmc-pubone-client
misc/run_pipenv_init.sh 
misc/run_pip_install_req_dev.sh 
```

Then modify your requirements/*.in files, run 
```sh
misc/run_pip_multi.sh
misc/run_pip_install_req_dev.sh 
```
and now you are ready to start your development. 

### Notes:

- Do not forget to create new git tags
(to keep version of the package bumped/updated). 
- Do not forget to update CHANGELOG.md. 
- Do not forget to add descriptions to doc/*.md files or to this README.md file. 


Test configuration is defined in the `tox.ini` file and includes
`py.test` tests and `flake8` source code checker.

You can run all of the tests:

```sh
misc/run_bash.sh
python setup.py test
```

or 

```sh
misc/run_tests_setup.sh
```


To run just the `py.test` tests, not `flake8`, and to re-use pipenv `virtualenv` do the following:

```sh
misc/run_bash.sh
py.test
```

or with 

```sh
misc/run_tests_pytest.sh
```


## Usage

### Simple Validation
```python
from pmc.pubone_client import PubOneClient

pubone = PubOneClient()

# validate PubMed and PMC ids for existance and
# match to the same article.
if pubone.valid(pmid=10, pmcid=5922622):
    print("You PubMed id and PMC ids are valid and matching to the same article.")

# validate PubMed id for existance.
if pubone.valid(pmid=10):
    print("You PubMed id is valid.")

# validate PMC id for existance.
if pubone.valid(pmcid=13901):
    print("You PMC id is valid.")

```

### For Web Service environment.

#### With prebuilt sessions types:

##### CmdLineFtsType

    max_tries=10,  # maximum number of tries.
    max_time=120,  # maximum time to try.
    max_value=15,  # maximum interval between tries.

```python
from pmc.pubone_client import PubOneClient

pubone = PubOneClient()
...
```

##### WebServiceFtsType

    max_time=3,  # maximum time to try.
    max_value=1,  # maximum interval between tries
    timeout=(3.2, 2),

```python
from pmc.pubone_client import PubOneClient, WebServiceFtsType
pubone = PubOneClient(session=WebServiceFtsType())
...
```

#### Customize session class yourself.

```python
from pmc.pubone_client import PubOneClient
from pmc.rest_client.session import FtsClassFactory

SessionType = FtsClassFactory(
    max_time=60,  # maximum time to try.
    max_value=15,  # maximum interval between tries
    timeout=None,
    ...
)

pubone = PubOneClient(session=SessionType())
...
```


