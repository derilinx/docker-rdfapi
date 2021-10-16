# -*- coding: utf-8 -*-
from flask import request, Flask, abort, Response, send_file, make_response, jsonify
from functools import wraps
import rdflib
from losd_conversion import RDFConversion
import os


losd_api = Flask(__name__)


def _check_respose_status(conversion_response):
    """
    This checks the if the json-stat is converted to rdf without any errors.
    """
    if conversion_response['status'] == 200:
        return True
    return False


def _rdf_serialize(response):
    """
    Serialize the content in n3 form to json-ld
    """
    graph = rdflib.Graph()
    try:
        rdf_triple_data = response['rdf_content']
        g = graph.parse(data=rdf_triple_data, format='n3')
        losn_ld_content = g.serialize(format='json-ld', indent=4)
        return losn_ld_content
    except Exception as e:
        losd_api.logger.error("Could not parse to json-ld format: {}".format(str(e)))


def _make_response(op_format, conversion_response): 
    """
    Make response based on the requested output format either text response or json-ld response.
    Also set necessary headers.
    """
    
    headers_content_type = {'json-ld': 'application/json-ld', 'text': 'text/xml', 'xml': 'text/xml'}

    losd_api.logger.info(conversion_response['status'])
    
    if not _check_respose_status(conversion_response):
        status = conversion_response['status']
        resp = make_response(jsonify(conversion_response), status)
        resp.headers['Content-Type'] = headers_content_type.get(op_format.strip(), 'text/xml')

    else:
        losd_api.logger.info(op_format)

        if op_format and op_format.lower().strip() == 'json-ld':
            json_ld = _rdf_serialize(conversion_response)
            resp = make_response(json_ld, 200)
            resp.headers['Content-Type'] = headers_content_type.get(op_format.strip(), 'text/xml')
        else:
            rdf_triple_text = conversion_response['rdf_content']
            resp = make_response(rdf_triple_text, 200)
            resp.headers['Content-Type'] = headers_content_type.get(op_format.strip(), 'text/xml')

    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp


def check_auth(username, password):
    """
    This function is called to check if a username
    password combination is valid. There is not database hence check manually - string matching.
    """
    losd_api.logger.info(str(os.environ['RDFAPI_PWD']))
    losd_api.logger.info(str(os.environ['RDFAPI_USERNAME']))
    losd_api.logger.info(str(username).strip() == str(os.environ['RDFAPI_USERNAME']) and str(password).strip()
                         == str(os.environ['RDFAPI_PWD']))
    losd_api.logger.info(password)
    losd_api.logger.info(username)
    return str(username).strip() == str(os.environ['RDFAPI_USERNAME']) and str(password).strip() \
           == str(os.environ['RDFAPI_PWD'])


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response('Could not verify your access level for {}.\n You have to login with proper credentials'.
                    format('losd-rdf-conversion-api'), 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})


# Authentication wrapper function
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth:  # no header set
            return authenticate()
        if not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


# Main route to the conversion
@losd_api.route('/convert_to_rdf', methods=['POST', 'GET'])
@requires_auth
def rdf_conversion_api():
    """
    Conversion takes place nonly during post response.
    On GET - give the instrunction on how to use this API
    """

    if request.method == 'POST':
        
        losd_api.logger.info("********** Route Request Paramns **************")
        losd_api.logger.info(dict(request.args))
        req = dict(request.args)

        datasetid = req.get('DatasetId', '')
        vocabulary_namespace = req.get('VocabNmSpace', '')
        data_namespace = req.get('DataNmSpace', '')
        file_url = req.get('FileURL', '')
        file_content = req.get('Content', '')
        output_format = req.get('OutputFormat', '')

        conversion = RDFConversion(datasetid, vocabulary_namespace, data_namespace, file_url, file_content, req)
        conversion_response = conversion.convert()
        resp = _make_response(output_format, conversion_response)

        return resp

    elif request.method == "GET":
        resp = make_response(jsonify({'RDF Conversion API Usage': "This api can be used to convert a valid json stat to "
                                                              "linked data json-ld/rdf-xml format. To convert, please use "
                                                              "post request along with the basic auth to the link "
                                                              "/convert_to_rdf. The parameters required to convert "
                                                              "json-stat to rdf is given below",
                                      'Parameters': {'DatasetId': "This is name of the dataset",
                                                     'VocabNmSpace': "This should be a valid http:// url",
                                                     'DataNmSpace': "This should be a valid http:// url",
                                                     'FileURL': "You can give a valid link to json stat file "
                                                                 "(optional)",
                                                     'Content': "You can also give json stat content as text.",
                                                     'OutputFormat': 'text or json-ld',
                                                     'PushToRDFStore': 'True or False. If True parameters RDFStoreURL, '
                                                                       'RDFStoreUserName, RDFStorePassword, '
                                                                       'RDFStoreGraphURI should be given',
                                                     'RDFStoreURL': 'RDF Store/Virtuoso URL',
                                                     'RDFStoreUserName': 'RDF Store username',
                                                     'RDFStorePassword': 'RDF store password',
                                                     'RDFStoreGraphURI': 'URI '},
                                      "Tips": "You can send either file url or content of the json-stat to this api. "
                                              "OutputFormat=text is lot faster than json-ld"}))
        return resp


if __name__ == "__main__":
    losd_api.run(host='0.0.0.0')
