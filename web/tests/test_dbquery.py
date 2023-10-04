from app.dbqueryStructures import DbQueryRequest, QueryRequestType, PackageType
from app.dbquery import dbquery

def test_dbquery_scores():
    result = DbQueryRequest(query_type=QueryRequestType.PACKAGE_COUNTS, 
                         package_type=PackageType.BIOC, package_name='S4Vectors', year='2022')
    result = dbquery(result)
    print(result)

test_dbquery_scores()
