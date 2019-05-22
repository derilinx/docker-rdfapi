from losd_validators import Validator
import json
import string
import re
import urllib2
from collections import OrderedDict
import uuid
from PushToRDFStore import pushToRDFStore
from losd_validators import Validator


class RDFConversion(Validator):

    def __init__(self, datasetid, vocabulary_namespace, data_namespace, file_url, content, request_dict):
        Validator.__init__(self, datasetid, vocabulary_namespace, data_namespace, file_url, content, request_dict)

    def _get_content(self):

        if self.file_url:
            source_json = json.loads(urllib2.urlopen(self.file_url).read(), object_pairs_hook=OrderedDict)
        else:
            source_json = json.loads(self.file_content)

        return source_json

    def _cleanString(self, s):

        """ For cleaning the space - replace space by _"""

        s = str(re.sub(r'\([^)]*\)', '', s.encode('utf-8')))
        s = s.translate(None, string.punctuation)

        return s.strip().replace(" ", "_").lower()

    def _prefix_build_concept(self, data_namespace_prefix, data_field_nm):
        return data_namespace_prefix + self._cleanString(data_field_nm) + 'cpt:'

    def _urlize(self, *args):

        """
        Url builder for code list concept and scheme
        """

        return "csod" + "/".join(map(self._cleanString, args))

    def _namespace_vocabspace_validator(self, given_string):

        """
        To validate the the namespace and vocabulary space links if it dosent ends with "/"
        """

        if list(given_string)[-1] != "/":
            given_string = given_string + "/"

        return given_string

    def _convert_to_rdf(self):

        """ This is used to call a specific function based on the version of json stat source."""

        job_result = {}

        # Add "/" at the end of data_namespace if not present.
        vocabulary_namespace = self._namespace_vocabspace_validator(self.vocabulary_namespace)
        data_namespace = self._namespace_vocabspace_validator(self.data_namespace) + self.datasetid + "/"
        # Vocabulary prefix
        vocabulary_namespace_prefix = "losdv"
        # Data namespace prefix
        data_namespace_prefix = "losdd"

        # read from json-stat from a url
        source_json = self._get_content()
        _cleanString = self._cleanString
        _prefix_build_concept = self._prefix_build_concept

        def conversion_for_old_jstat_version():

            scheme = [
                '@prefix qb: <http://purl.org/linked-data/cube#> .'
                '\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .'
                '\n@prefix skos: <http://www.w3.org/2004/02/skos/core#> .'
                '\n@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'
                '\n@prefix prov: <http://www.w3.org/ns/prov#> .'
                '\n@prefix dc: <http://purl.org/dc/elements/1.1/> .'
                '\n@prefix ' + vocabulary_namespace_prefix + ': <' + vocabulary_namespace + '> .\n@prefix '
                + data_namespace_prefix + ': <' + data_namespace + '> .',
                '\n@prefix ' + data_namespace_prefix + 'schm: <' + data_namespace + 'conceptscheme/> .']

            code_list = ['#CODELIST\n\n']
            observations = ['#OBSERVATIONS\n\n']

            dataset_label = source_json['dataset']['label']
            dataset_source = source_json['dataset']['source']
            dataset_updated = source_json['dataset']['updated']
            dimensions = source_json['dataset']['dimension']

            # Building prefix

            for data_field_nm in dimensions['id']:
                scheme.append('\n@prefix ' + data_namespace_prefix + _cleanString(
                    data_field_nm) + 'cpt: <' + data_namespace + 'concept/' + _cleanString(data_field_nm) + '/> .')

            scheme.append('\n\n#SCHEME\n\n')
            dataset_values = source_json['dataset']['value']
            n1 = len(dimensions['id'])

            # Scheme: Individual terms

            try:

                for data_field_nm in dimensions['id']:
                    scheme.append('' + vocabulary_namespace_prefix + ':' + _cleanString(
                        data_field_nm) + ' a qb:ComponentProperty, qb:DimensionProperty ;\n\trdfs:label "' + data_field_nm.encode(
                        'utf-8') + '" ;\n\trdfs:range xsd:string .\n\n')

                scheme.append(
                    '' + vocabulary_namespace_prefix + ':value a qb:ComponentProperty, qb:MeasureProperty ;\n\trdfs:label "value" ;\n\trdfs:range xsd:float .\n\n')

                # Scheme: DSD

                scheme.append('' + data_namespace_prefix + ':' + self._cleanString(
                    dataset_label) + '_dsd a qb:DataStructureDefinition ;\n\tqb:component\n\t\t'
                                     '[ a qb:ComponentSpecification ;\n\t\t  qb:codeList ' +
                              data_namespace_prefix + 'schm:measureType ; \n\t\t  qb:dimension qb:measureType ;'
                                                      '\n\t\t  qb:order 1 \n\t] ;\n\tqb:component [ qb:measure ' +
                              vocabulary_namespace_prefix + ':value ] ;\n\t')

                for index, data_field_nm in enumerate(dimensions['id']):
                    scheme.append(
                        'qb:component\n\t\t[ a qb:ComponentSpecification ;\n\t\t  qb:codeList ' + data_namespace_prefix +
                        'schm:' + self._cleanString(
                            data_field_nm) + ' ;\n\t\t  qb:dimension ' + vocabulary_namespace_prefix + ':' + _cleanString(
                            data_field_nm) + ' ;\n\t\t  qb:order ' + str(index + 2) + ' \n\t\t] ')

                    if index == (n1 - 1):
                        scheme.append('\n.\n\n')
                    else:
                        scheme.append(';\n\t')

                # Scheme: Dataset

                scheme.append('' + data_namespace_prefix + ':' + _cleanString(dataset_label) +
                              '_dataset a qb:DataSet ;\n\tqb:structure ' + data_namespace_prefix + ':' +
                              _cleanString(dataset_label) + '_dsd ;\n\trdfs:label "' + \
                              dataset_label.encode('utf-8') + '" ; \n\tprov:generatedAtTime "' + dataset_updated
                              + '"^^xsd:dateTime ;\n\tdc:creator "' + dataset_source + '" .\n\n')

                # Generating Codelist

                # Codelist: Conceptscheme

                for index, data_field_nm in enumerate(dimensions['id']):
                    code_list.append('' + data_namespace_prefix + 'schm:' +
                                     _cleanString(data_field_nm) + ' a skos:ConceptScheme ;\n\t')

                    skos_members = []
                    for k in dimensions[data_field_nm]['category']['index'].keys():
                        concept = dimensions[data_field_nm]['category']['label'][k]

                        skos_members.append(
                            'skos:member ' + _prefix_build_concept(data_namespace_prefix, data_field_nm) + _cleanString(
                                concept) + ' ')

                    code_list.append(';\n\t'.join(skos_members) + '.\n\n')

                # Codelist: Concepts

                for data_field_nm in dimensions['id']:

                    for k in dimensions[data_field_nm]['category']['index'].keys():
                        concept = dimensions[data_field_nm]['category']['label'][k]
                        code_list.append(
                            '' + self._prefix_build_concept(data_namespace_prefix, data_field_nm) + self._cleanString(concept) +
                            ' a skos:Concept ;\n\trdfs:label "' + concept.encode('utf-8') + '" .\n\n')

                # Generating Observations

                all_term = []

                for data_field_nm in dimensions['id']:
                    labels = []

                    for k in dimensions[data_field_nm]['category']['index'].keys():
                        concept = dimensions[data_field_nm]['category']['label'][k]
                        labels.append(self._cleanString(concept))

                    all_term.append(labels)

                size = dimensions['size']
                total_size = 1
                tracker = []

                for s in size:
                    tracker.append(0)
                    total_size *= s

                track_size = len(tracker)

                # Observations: creating each

                for t in xrange(total_size):
                    observations.append(data_namespace_prefix + ':' + str(
                        uuid.uuid4()) + ' a qb:Observation ;\n\tqb:dataSet ' + data_namespace_prefix + ':' +
                                        _cleanString(dataset_label) + '_dataset ;\n\tqb:measureType ' +
                                        vocabulary_namespace_prefix + ':value ;\n\t')

                    for index, data_field_nm in enumerate(dimensions['id']):
                        observations.append('' + vocabulary_namespace_prefix + ':' + _cleanString(data_field_nm) + ' ')
                        observations.append(
                            '' + _prefix_build_concept(data_namespace_prefix, data_field_nm) + all_term[index][
                                tracker[index]] + ' ;\n\t')

                    tracker[track_size - 1] += 1

                    for i in xrange(track_size - 1, -1, -1):
                        if i != 0:
                            if tracker[i] > size[i] - 1:
                                tracker[i] = 0
                                tracker[i - 1] += 1
                        else:
                            if tracker[i] > size[i] - 1:
                                tracker[i] = 0

                    observations.append('qb:measureType ' + vocabulary_namespace_prefix + ':value ;\n\t' +
                                        vocabulary_namespace_prefix + ':value "' +
                                        str(dataset_values[t]) + '"^^xsd:float\n . \n\n')

            except Exception as e:

                job_result['status'] = 500
                job_result['Error'] = str(e)
                job_result['version'] = "old"
                job_result['ErrorMessage'] = "Something went wrong in the parsing json-stat to rdf. " \
                                        "Please ensure json stat in required format"

                return job_result

            rdf_content = []
            rdf_content.extend(scheme)
            rdf_content.extend(code_list)
            rdf_content.extend(observations)
            job_result['status'] = 200
            job_result['Error'] = "None"
            job_result['version'] = "old"
            job_result['SuccessMessage'] = "RDF file is successfully created"
            job_result['rdf_content'] = "".join(rdf_content)

            return job_result

        def conversion_for_new_jstat_version():

            scheme = [
                '@prefix qb: <http://purl.org/linked-data/cube#> .'
                '\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .'
                '\n@prefix skos: <http://www.w3.org/2004/02/skos/core#> .'
                '\n@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'
                '\n@prefix prov: <http://www.w3.org/ns/prov#> .'
                '\n@prefix dc: <http://purl.org/dc/elements/1.1/> .'
                '\n@prefix ' + vocabulary_namespace_prefix + ': <' + vocabulary_namespace + '> .\n@prefix '
                + data_namespace_prefix + ': <' + data_namespace + '> .',
                '\n@prefix ' + data_namespace_prefix + 'schm: <' + data_namespace + 'conceptscheme/> .']

            code_list = ['#CODELIST\n\n']
            observations = ['#OBSERVATIONS\n\n']

            dataset_label = source_json['label']
            dataset_source = source_json['source']
            dataset_updated = source_json['updated']
            dimensions = source_json['dimension']
            dataset_values = source_json['value']
            field_nms = source_json['id']

            #### Building prefix

            for data_field_nm in field_nms:
                scheme.append('\n@prefix ' + data_namespace_prefix + _cleanString(
                    data_field_nm) + 'cpt: <' + data_namespace + 'concept/' + _cleanString(data_field_nm) + '/> .')

            scheme.append('\n\n#SCHEME\n\n')

            # Generating Scheme

            unit_index = source_json['id'].index('Units')
            n1 = len(field_nms)

            try:

                # Scheme: Individual terms

                for data_field_nm in field_nms:
                    scheme.append('' + vocabulary_namespace_prefix + ':' + _cleanString(
                        data_field_nm) + ' a qb:ComponentProperty, qb:DimensionProperty ;\n\trdfs:label "' + data_field_nm.encode(
                        'utf-8') + '" ;\n\trdfs:range xsd:string .\n\n')

                    scheme.append(
                        '' + vocabulary_namespace_prefix + ':value a qb:ComponentProperty, qb:MeasureProperty ;'
                                                           '\n\trdfs:label "value" ;\n\trdfs:range xsd:float .\n\n')

                # Scheme: DSD

                scheme.append('' + data_namespace_prefix + ':' + _cleanString(
                    dataset_label) + '_dsd a qb:DataStructureDefinition ;\n\tqb:component\n\t\t'
                                     '[ a qb:ComponentSpecification ;\n\t\t  qb:codeList ' +
                              data_namespace_prefix + 'schm:measureType ; \n\t\t  qb:dimension qb:measureType ;'
                                                      '\n\t\t  qb:order 1 \n\t] ;\n\tqb:component [ qb:measure ' +
                              vocabulary_namespace_prefix + ':value ] ;\n\t')

                for index, data_field_nm in enumerate(field_nms):
                    if data_field_nm != 'Units':
                        scheme.append('qb:component\n\t\t[ a qb:ComponentSpecification ;\n\t\t  qb:codeList '
                                      + data_namespace_prefix + 'schm:' + _cleanString(data_field_nm) +
                                      ' ;\n\t\t  qb:dimension ' + vocabulary_namespace_prefix + ':' +
                                      _cleanString(data_field_nm) + ' ;\n\t\t  qb:order ' + str(
                            index + 2) + ' \n\t\t] ')
                        if index == n1 - 1:
                            scheme.append('\n.\n\n')
                        else:
                            scheme.append(';\n\t')

                # Scheme: Dataset

                scheme.append('' + data_namespace_prefix + ':' + _cleanString(dataset_label) +
                              '_dataset a qb:DataSet ;\n\tqb:structure ' + data_namespace_prefix + ':' +
                              _cleanString(dataset_label) + '_dsd ;\n\trdfs:label "' + \
                              dataset_label.encode('utf-8') + '" ; \n\tprov:generatedAtTime "' + dataset_updated
                              + '"^^xsd:dateTime ;\n\tdc:creator "' + dataset_source + '" .\n\n')

                # Generating Code list

                # Code list: Conceptscheme

                for data_field_nm in field_nms:
                    if data_field_nm != 'Units':
                        code_list.append('' + data_namespace_prefix + 'schm:' +
                                         _cleanString(data_field_nm) + ' a skos:ConceptScheme ;\n\t')

                        skos_members = []
                        for k in dimensions[data_field_nm]['category']['index'].keys():
                            concept = dimensions[data_field_nm]['category']['label'][k]
                            # print(concept)

                            skos_members.append(
                                'skos:member ' + _prefix_build_concept(data_namespace_prefix,
                                                                      data_field_nm) + _cleanString(
                                    concept) + ' ')

                        code_list.append(';\n\t'.join(skos_members) + '.\n\n')

                # Code list: Concepts

                for data_field_nm in field_nms:
                    if data_field_nm != 'Units':

                        for k in dimensions[data_field_nm]['category']['index'].keys():
                            concept = dimensions[data_field_nm]['category']['label'][k]
                            code_list.append(
                                '' + _prefix_build_concept(data_namespace_prefix, data_field_nm) + _cleanString(
                                    concept) +
                                ' a skos:Concept ;\n\trdfs:label "' + concept.encode('utf-8') + '" .\n\n')

                # Generating Observations

                all_term = []
                for data_field_nm in field_nms:
                    if data_field_nm != 'Units':
                        labels = []
                        for k in dimensions[data_field_nm]['category']['index'].keys():
                            concept = dimensions[data_field_nm]['category']['label'][k]
                            labels.append(self._cleanString(concept))

                        all_term.append(labels)

                size = source_json['size']
                del size[unit_index]
                total_size = 1
                tracker = []

                for s in size:
                    tracker.append(0)
                    total_size *= s

                track_size = len(tracker)

                # Observations: creating each

                for t in xrange(total_size):
                    observations.append(data_namespace_prefix + ':' + str(
                        uuid.uuid4()) + ' a qb:Observation ;\n\tqb:dataSet ' + data_namespace_prefix + ':' +
                                        _cleanString(dataset_label) + '_dataset ;\n\tqb:measureType ' +
                                        vocabulary_namespace_prefix + ':value ;\n\t')

                    cnt_all = 0

                    for data_field_nm in field_nms:

                        if data_field_nm != 'Units':
                            observations.append('' + vocabulary_namespace_prefix + ':'
                                                + self._cleanString(data_field_nm) + ' ')
                            observations.append('' + self._prefix_build_concept(data_namespace_prefix, data_field_nm) +
                                                all_term[cnt_all][tracker[cnt_all]] + ' ;\n\t')
                            cnt_all += 1

                    tracker[track_size - 1] += 1

                    for i in xrange(track_size - 1, -1, -1):
                        if i != 0:
                            if tracker[i] > size[i] - 1:
                                tracker[i] = 0
                                tracker[i - 1] += 1
                        else:
                            if tracker[i] > size[i] - 1:
                                tracker[i] = 0

                    observations.append('qb:measureType ' + vocabulary_namespace_prefix + ':value ;\n\t' +
                                        vocabulary_namespace_prefix + ':value "' +
                                        str(dataset_values[t]) + '"^^xsd:float\n . \n\n')

            except Exception as e:

                job_result['status'] = 500
                job_result['Error'] = str(e)
                job_result['version'] = "New"
                job_result['Message'] = "Something went wrong in parsing the json-stat to RDF"

                return job_result

            rdf_content = []
            rdf_content.extend(scheme)
            rdf_content.extend(code_list)
            rdf_content.extend(observations)
            job_result['status'] = 200
            job_result['Error'] = "None"
            job_result['version'] = "New"
            job_result['SuccessMessage'] = "RDF file is successfully created"
            job_result['rdf_content'] = "".join(rdf_content)

            return job_result

        # Check for the version of the json-stat file

        if "version" in source_json.keys():
            return conversion_for_new_jstat_version()
        else:
            return conversion_for_old_jstat_version()

    def convert(self):

        """"
        Calls the respective conversion function and push to rdf store function. If any one of them is failed
        give response as 400 - failed
        """

        validation_failed = Validator.validate_fail(self)

        if validation_failed:
            return validation_failed
        else:

            rdf_conversion_response = self._convert_to_rdf()

            if (rdf_conversion_response['status'] == 200) and (
                    Validator.boolean_converter(self.request_dict.get('PushToRDFStore', ''))):
                push_response = pushToRDFStore(self.request_dict, rdf_conversion_response)

                if push_response['status'] == 200:
                    rdf_conversion_response['rdfStore_Status'] = 200
                    rdf_conversion_response['rdfStore_Message'] = 'Pushed to rdf store successfully'
                else:
                    rdf_conversion_response['status'] = push_response['status']
                    rdf_conversion_response['Message'] = "Conversion successful but push to rdf store failed"
                    rdf_conversion_response['Error'] = push_response['ErrorMessage']
                    rdf_conversion_response['ErrorType'] = push_response['ErrorType']

            return rdf_conversion_response
