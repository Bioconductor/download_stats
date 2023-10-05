'''
conftest.py - shareable fixtures
'''

import sqlite3
import pytest
from unittest.mock import patch
from unittest.mock import patch

import app.dbqueryStructures as dbs

@pytest.fixture
def getpackages():
    return ['bob', 'shear']