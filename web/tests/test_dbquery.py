import app.dbqueryStructures as dbs
from app.dbquery import dbquery

def test_dbquery_scores():
    q = dbs.DbQueryRequest(query_type=dbs.QueryRequestType.PACKAGE_COUNTS, 
                         package_type=dbs.PackageType.BIOC, package_name='S4Vectors', year='2022')
    r = dbquery(q)
    print(r)
    assert r.status == dbs.DataRetrievalStatus.SUCCESS
    assert r.result[0].package_name == 'S4Vectors'

    
def test_getpackages(getpackages):
    assert getpackages[0] == 'bob'