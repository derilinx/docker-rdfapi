from losd_validators import Validator as validator
import os
import tempfile
import logging as log


def _change_rdfstore_url(val):
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

    rdfStoreURL = request_dict.get('RDFStoreURL', '').strip()
    rdfStoreUser = request_dict.get('RDFStoreUserName', '').strip()
    rdfStorePass = request_dict.get('RDFStorePassword', '').strip()
    graphIRI = request_dict.get('RDFStoreGraphURI', '').strip()
    converted_content = rdf_conversion_response.get('rdf_content').strip()

    rdfStoreURL = _change_rdfstore_url(rdfStoreURL)

    push_url = rdfStoreURL + '/sparql-graph-crud-auth?graph-uri=' + graphIRI

    try:

        log.debug("RDF store push url: {}".format(push_url))
        response = requests.post(push_url, data=converted_content, auth=HTTPDigestAuth(rdfStoreUser, rdfStorePass))

        status_code = str(response.status_code)

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
