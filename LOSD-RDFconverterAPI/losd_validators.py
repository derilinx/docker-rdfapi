# -*- coding: utf-8 -*-
import json
import validators
#import urllib2
from urllib.request import urlopen
from collections import OrderedDict
import re
import string
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Validator:
    """
        This corresponds to all the validation of the request parameters throws an json content if any error found.
    """

    validator_response = {'file_url_error': {'status': 400, 'ErrorMessage': 'File URL Error',
                                             'ErrorType': 'file_url_error'},
                          'file_content_error': {'status': 400,
                                                 'ErrorMessage': 'given file format is not a json stat format',
                                                 'ErrorType': 'file_content_error'},
                          'dataset_id_error': {'status': 400, 'ErrorMessage': 'Make sure the '
                                                                              'name of the data set and should not '
                                                                              'contain any special characters',
                                               'ErrorType': 'dataset_id_error'},
                          'vocab_namespace_error': {'status': 400,
                                                    'ErrorMessage':
                                                        'Not a valid vocabulary name space '
                                                        '- should be of type http://',
                                                    'ErrorType': 'vocab_namespace_error'},
                          'data_namespace_error': {'status': 400,
                                                   'ErrorMessage': 'Not a valid data name space - '
                                                                   'should be of type http://',
                                                   'ErrorType': 'data_namespace_error'},
                          'null_parameter_error': {'status': 400,
                                                   'ErrorMessage': 'missing or null value parameter',
                                                   'ErrorType': 'null value'},
                          'HTTPError': {'status': 400,
                                        'ErrorMessage': 'Invalid RDF file. Please validate rdf syntax',
                                        'ErrorType': 'HTTPError'},
                          'ConnectionError': {'status': 400,
                                        'ErrorMessage': 'Invalid RDF store URL. Please verify virtuoso RDF store URL',
                                        'ErrorType': 'ConnectionError'},
                          'TimeoutError': {'status': 400,
                                        'ErrorMessage': 'Error connecting to rdf store',
                                        'ErrorType': 'TimeoutError'},
                          'RequestException': {'status': 400,
                                           'ErrorMessage': 'Something went wrong.',
                                           'ErrorType': 'RequestException'},
                          'SystemError': {'status': 400,
                                           'ErrorMessage': 'Please verify that RDF file (URL) exists.',
                                           'ErrorType': 'SystemError'},
                          'OSError': {'status': 400,
                                          'ErrorMessage': 'Temporary file already exists. '
                                                          'Please contact system administrator.',
                                          'ErrorType': 'OSError'},
                          'URLError': {'status': 400,
                                      'ErrorMessage': 'Make sure RDFStoreURL and RDFStoreGraphURI (http://)'
                                                      ' are valid urls',
                                      'ErrorType': 'RDF URLError'},
                          }

    def __init__(self, datasetid, vocabulary_namespace, data_namespace, file_url, content, request_dict):
        self.datasetid = datasetid
        self.vocabulary_namespace = vocabulary_namespace
        self.data_namespace = data_namespace
        self.file_content = content
        self.file_url = file_url
        self.request_dict = request_dict

    def check_empty_fields(self):
        """
        Checks if the parameter given is empty
        :return: null if the value is not empty else returns json error response
        """

        if (not self.datasetid) or (not self.vocabulary_namespace) or \
                (not self.data_namespace):
            logger.info("missing required parameter")
            return Validator.validator_response.get('null_parameter_error')

        if (not self.file_url) and (not self.file_content):
            logger.info("missing required parameter")
            return Validator.validator_response.get('null_parameter_error')

        return ""

    def datasetid_validator(self):

        """
        For cleaning the space, punctuations, special characters from dataset id - replace space by _
        :return: null (i.e. stores the cleaned dataset id) or error response
        """
        logging.info("dataset id *************************: {}".format(self.datasetid))

        try:

            self.datasetid = str(re.sub(r'\([^)]*\)', '', self.datasetid))
            translator=str.maketrans('','',string.punctuation)
            self.datasetid = self.datasetid.translate(translator)

            self.datasetid = self.datasetid.strip().replace(" ", "_").lower()
        except Exception as e:
            logging.error("This error is from datasetid_validator: {}".format(str(e)))
            return Validator.validator_response.get('dataset_id_error')

        if self.datasetid.strip():
            return ""
        else:
            val = Validator.validator_response.get('dataset_id_error')
            val['ErrorMessage'] = 'Dataset Id cannot be empty or special characters'
            logger.error("dastaset id validation failed")
            return val

    def vocab_namespace_validator(self):
        """
        This is type of url validator - validates vocabulary name space
        :return: empty if it is a valid url else give appropriate error response
        """
        if bool(validators.url(self.vocabulary_namespace)):
            return ""
        else:
            return Validator.validator_response.get('vocab_namespace_error')

    def data_namespace_vaidator(self):
        """
        This is type of url validator - validates data name space
        :return: empty if it is a valid url else give appropriate error response
        """
        if bool(validators.url(self.data_namespace)):
            return ""
        else:
            return Validator.validator_response.get('data_namespace_error')

    def file_content_format_validator(self):
        """
        This validates if the file content is json stat or empty file. If empty give appropriate error response.
        :return: Null if content is json stat and not empty
        """

        if str(self.file_content).strip():
            try:
                json.loads(self.file_content)
                return ""
            except ValueError:
                logging.debug("This error is from file_content_format_validator value error")
                return Validator.validator_response.get('file_content_error')
            except Exception as e:
                logging.debug("This error is from file_content_format_validator: {}".format(str(e)))
                val = Validator.validator_response.get('file_content_error')
                val['ErrorMessage'] = str(e)
                return val
        else:
            val = Validator.validator_response.get('file_content_error')
            val['ErrorMessage'] = 'File content cannot be empty'
            logger.error('Empty json-stat content')
            return val

    def file_url_validator(self):
        """
        Checks the given url is valid and contains json stat content
        :return: Null if url can be opened and the content is valid json-stat
        """

        if bool(validators.url(self.file_url)):
            try:
                json.loads(urlopen(self.file_url).read().decode('utf-8'), object_pairs_hook=OrderedDict)
                return ""
            except Exception as e:
                logging.debug("This error is from file_url_validato: {}".format(str(e)))
                val = Validator.validator_response.get('file_url_error')
                val['ErrorMessage'] = str(e)
                logger.error('file url error {}'.format(str(val)))
                return val
        else:
            logger.error('file url error')
            return Validator.validator_response.get('file_url_error')

    @staticmethod
    def boolean_converter(val):
        """
        Gets string and check is content can be converted to boolean
        :param val: string
        :return: True or False
        """

        boolean_vals = ('true', '1', 'yes', 'y')

        if val and (str(val).lower() in boolean_vals):
            return True
        return False

    @staticmethod
    def url_validator(val):
        """
        Checks a if a sting is valid url
        :param val: string
        :return: True or False
        """
        logger.info("url validator ********* {}:{}".format(bool(validators.url(val)), type(val)))
        return bool(validators.url(val))

    def rdf_store_validator(self):
        """
        Validates all the parameters corresponding push to rdf store functionality.
        Checks only if PushToRDFStore is True
        :return: Null if validations is successful
        """
        request_parms = self.request_dict
        logger.info("********* Request Parameters ************")
        logger.info(request_parms)

        rdf_store_values = ('PushToRDFStore', 'RDFStoreURL', 'RDFStoreUserName', 'RDFStorePassword', 'RDFStoreGraphURI')

        if Validator.boolean_converter(request_parms.get('PushToRDFStore', '')):

            for rdf_val in rdf_store_values:
                if not request_parms.get(rdf_val, ''):
                    return Validator.validator_response.get('null_parameter_error')
                if rdf_val in ('RDFStoreURL', 'RDFStoreGraphURI') and (
                        not Validator.url_validator(request_parms.get(rdf_val, ''))):
                    logger.info("**********rdfstore validator **********")
                    logger.info("****rdfstore validator****** {}:{}".format(rdf_val, request_parms))    

                    return Validator.validator_response.get('URLError')

        return ""

    def validate_fail(self):
        """
        Runs all the validations. I.e it runs all given class methods
        :return: Null if validation is successful else json response of errors.
        """

        exec_methods = ["check_empty_fields", "datasetid_validator", "vocab_namespace_validator",
                        "data_namespace_vaidator", 'rdf_store_validator']

        if self.file_url:
            exec_methods.append("file_url_validator")
        else:
            exec_methods.append('file_content_format_validator')

        for method in exec_methods:
            logger.info('Validation method executed: {}'.format(str(method)))
            validation_error = getattr(self, method)()
            logger.info('if any validation error: {}'.format(str(validation_error)))
            if validation_error:
                return validation_error

        return ""


