'''
conftest.py - shareable fixtures
'''

import pytest
import app.dbqueryStructures as dbs

@pytest.fixture
def getpackages():
    return ['bob', 'shear']