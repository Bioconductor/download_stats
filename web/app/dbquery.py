import app.dbqueryStructures as dbs

def dbquery(request: dbs.DbQueryRequest) -> dbs.DbQueryResponse:
    match request.query_type:
        case dbs.QueryRequestType.PACKAGE_SCORES:
            u = dbs.DbResultEntry(request.package_name, '2021-03-01', False, 1543, 12345)
            r = dbs.DbQueryResponse(status=dbs.DataRetrievalStatus.SUCCESS,
                                    result=[u])
            return r
        case dbs.QueryRequestType.PACKAGE_COUNTS:
            u = dbs.DbResultEntry(request.package_name, '2021-03-01', False, 1422, None)
            r = dbs.DbQueryResponse(status=dbs.DataRetrievalStatus.SUCCESS,
                                    result=[u])
            return r
        case _:
            raise Exception(f'Invalid request type ({dbs.DbQueryRequest})')

