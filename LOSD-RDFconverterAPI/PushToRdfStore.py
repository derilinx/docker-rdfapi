from losd_validators import Validator as validator
import os
import tempfile
import logging
import requests
from requests.auth import HTTPDigestAuth
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _change_rdfstore_url(val):
    """
    Check if url ends with /
    :param val: URL String
    :return: Modified URL with / at the end.
    """
    if val[-1] == '/':
        return val
    else:
        return str(val)+'/'


def pushToRDFStore(request_dict, rdf_conversion_response):

    """
    This function push the content of converted json stat to rdf triple store.

    :param request_dict: Contains all request arguments - all params are validated before sending to this function.
    :param rdf_conversion_response: This is conversion response. Contains converted n triples.
    :return: Returns a suitable response on push to rdf store.
    """

    push_stat = {}
    request_dict = dict(request_dict)
    logger.info("Push to rdf store request parameters".format(request_dict))

    rdfStoreURL = request_dict.get('RDFStoreURL', '')[0].strip()
    rdfStoreUser = request_dict.get('RDFStoreUserName', '')[0].strip()
    rdfStorePass = request_dict.get('RDFStorePassword', '')[0].strip()
    graphIRI = request_dict.get('RDFStoreGraphURI', '')[0].strip()
    converted_content = rdf_conversion_response.get('rdf_content')

    graphIRI = _change_rdfstore_url(graphIRI)
    rdfStoreURL = _change_rdfstore_url(rdfStoreURL)

    push_url = rdfStoreURL + '/sparql-graph-crud-auth?graph-uri=' + graphIRI

    try:

        temp_ttl = tempfile.NamedTemporaryFile(suffix='.ttl', delete=False)
        logger.info("Created a new temporary file: {}".format(temp_ttl.name))
        with open(temp_ttl.name, 'w') as ttl:
            ttl.write(converted_content)
            ttl.close()

        logger.info("RDF store push url: {}".format(push_url))
        headers = {'Content-type': 'text/rdf+ttl'}
        response = requests.post(push_url, data=open(temp_ttl.name, 'r').read(),
                                 auth=HTTPDigestAuth(rdfStoreUser, rdfStorePass), headers=headers)
        os.remove(temp_ttl.name)
        logger.info("Removed a temporary file")
        status_code = str(response.status_code)
        logger.info("RDF store push status: {}".format(status_code))
        logger.info("response text: {}".format(response.text))

        if (status_code == '201') or (status_code == '200'):

            push_stat['status'] = 200

        elif status_code == '401':

            push_stat['status'] = 400

        elif status_code == '500':
            push_stat['status'] = 400
            push_stat['ErrorMessage'] = "Invalid RDF file or Invalid graph uri. " \
                                        "Please validate RDF or Graph URI!. Graph URI must be of type http://**"
            push_stat['ErrorType'] = "Invalid file or URI"
        else:

            push_stat['status'] = 400
            push_stat['ErrorMessage'] = "Bad request! Please validate RDF file, username and password."
            push_stat['ErrorType'] = "Bad Request"

        return push_stat

    except requests.exceptions.HTTPError:
        return validator.validator_response.get('HTTPError')

    except requests.exceptions.ConnectionError:
        return validator.validator_response.get('ConnectionError')

    except requests.exceptions.Timeout:
        return validator.validator_response.get('ConnectionError')

    except requests.exceptions.RequestException:
        return validator.validator_response.get('RequestException')

    except SystemError:
        return validator.validator_response.get('SystemError')

    except OSError:
        return validator.validator_response.get('OSError')
    except Exception as e:
        logger.error('Exception while pushing to rdf store: {}'.format(str(e)))
        return validator.validator_response.get('OSError')
