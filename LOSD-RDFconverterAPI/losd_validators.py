import json
import validators
import urllib2
from collections import OrderedDict
import re
import string
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Validator:

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
                                                   'ErrorType': 'null value'}}

    def __init__(self, datasetid, vocabulary_namespace, data_namespace, file_url, content):
        self.datasetid = datasetid
        self.vocabulary_namespace = vocabulary_namespace
        self.data_namespace = data_namespace
        self.file_content = content
        self.file_url = file_url

    def check_empty_fields(self):

        if (not self.datasetid) or (not self.vocabulary_namespace) or \
                (not self.data_namespace):
            logger.debug("missing required parameter")
            return Validator.validator_response.get('null_parameter_error')

        if (not self.file_url) and (not self.file_content):
            logger.debug("missing required parameter")
            return Validator.validator_response.get('null_parameter_error')

        return ""

    def datasetid_validator(self):
        """ For cleaning the space - replace space by _"""

        try:

            self.datasetid = str(re.sub(r'\([^)]*\)', '', self.datasetid.encode('utf-8')))
            self.datasetid = self.datasetid.translate(None, string.punctuation)

            self.datasetid = self.datasetid.strip().replace(" ", "_").lower()
        except Exception as e:
            logging.debug("This error is from datasetid_validator: {}".format(str(e)))
            return Validator.validator_response.get('dataset_id_error')

        if self.datasetid.strip():
            return ""
        else:
            val = Validator.validator_response.get('dataset_id_error')
            val['ErrorMessage'] = 'Dataset Id cannot be empty or special characters'
            logger.debug("dastaset id validation failed")
            return val

    def vocab_namespace_validator(self):
        if bool(validators.url(self.vocabulary_namespace)):
            return ""
        else:
            return Validator.validator_response.get('vocab_namespace_error')

    def data_namespace_vaidator(self):
        if bool(validators.url(self.data_namespace)):
            return ""
        else:
            return Validator.validator_response.get('data_namespace_error')

    def file_content_format_validator(self):
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
            logger.debug('Empty json-stat content')
            return val

    def file_url_validator(self):

        if bool(validators.url(self.file_url)):
            try:
                json.loads(urllib2.urlopen(self.file_url).read(), object_pairs_hook=OrderedDict)
                return ""
            except Exception as e:
                logging.debug("This error is from file_url_validato: {}".format(str(e)))
                val = Validator.validator_response.get('file_url_error')
                val['ErrorMessage'] = str(e)
                logger.error('file url error {}'.format(str(val)))
                return val
        else:
            logger.debug('file url error')
            return Validator.validator_response.get('file_url_error')

    def validate_fail(self):

        exec_methods = ["check_empty_fields", "datasetid_validator", "vocab_namespace_validator", "data_namespace_vaidator"]

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


