from dbqueryStructures import *

def dbquery(request: DbQueryRequest):
    match request.query:
        case QueryRequestType.PACKAGE_SCORES:
            return "scores"
        case QueryRequestType.PACKAGE_COUNTS:
            return "counts"
        case _:
            raise Exception(f'Invalid request type ({DbQueryRequest})')

