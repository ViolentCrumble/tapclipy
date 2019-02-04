from tapclipy import queries
from urllib import request
import json
import re


class Connect:

    def __init__(self, url='http://localhost:9000', endpoint='/graphql'):
        self.__full_url = url + endpoint
        self.__can_connect = False
        self.__current_schema = ""
        self.__current_query_name_types = dict()

    def url(self):
        return self.__full_url

    def schema_query_name_types(self):
        return self.__current_query_name_types

    def query(self, name):
        if name in self.__current_query_name_types:
            return queries.query[name]
        else:
            return ""

    def parameters(self, name):
        if name in self.__current_query_name_types:
            return queries.parameters[name]

    def fetch_schema(self):
        schema_query = json.dumps({'query': queries.query['schema']})
        jbody = self.__tap_connect(schema_query)
        if jbody == '{}':
            return jbody
        else:
            self.__current_schema = jbody['data']['__schema']['queryType']['fields']
            self.__current_query_name_types = dict()
            for field in self.__current_schema:
                name = field['name']
                self.__current_query_name_types[name] = field['type']['ofType']['name']
            return self.__current_schema

    def analyse_text(self, query, text, parameters=''):
        variables = {'input': text,'parameters': parameters}
        #escaped_query = query.replace("\n", "\\n")  # query.encode('utf8').decode('unicode_escape')
        analyse_query = json.dumps({'query': query, 'variables': variables})
        return self.__tap_connect(analyse_query)

    def process_sentences(self, tags):

        # create empty array to hold completed sentences
        sentences = []

        # loop tag data
        for data in tags:

            # get copy of sentence we are working on
            newString = data['sentence']

            # loop phrase tags
            for phrase in data['phrases']:
                capturedPhrase = re.search("^([a-z A-Z']+)\[", phrase).group(1)
                tag = re.search("\[([a-zA-Z]+),", phrase).group(1)
                newString = newString.lower().replace(capturedPhrase,
                                                      "<span class='{tagType}'>{word}</span>".format(
                                                          word=capturedPhrase, tagType=tag.lower()))

            sentences.append(newString)

        return sentences

    def make_css(self, custom_style):
        styles = ""
        if custom_style is not None:
            for key in custom_style:
                rules = ""
                for rule in custom_style[key]:
                    rules += "  " + rule + ": " + custom_style[key][rule] + ";\n"
                styles += "." + key + "{\n" + rules + "}\n"

        return styles

    def make_html(self, result_data):
        output = ""
        analytics = result_data['data']['reflectExpressions']['analytics']
        sentences = self.process_sentences(analytics['tags'])

        for sentence in sentences:
            output += sentence

        return output

    def markup(self, html, css="""
            .anticipate{
                background-color: red;
            }
            .compare{
                background-color: blue;
            }
            .consider{
                background-color: green;
            }
            .definite{
                background-color: aqua;
            }
            .generalpronounverb {
                background-color: cadetblue;
            }
            .grouppossessive{
                background-color: gold;
            }
            .pertains{
                background-color: blueviolet;
            }
            .selfpossessive{
                background-color: brown;
            }            
            .selfreflexive{
                background-color: chocolate;
            }"""):

        style = '''
        <style type="text/css" media="screen">
        {custom_style}
        </style>
        '''.format(custom_style=css)

        return style + html

    def __tap_connect(self, query):
        try:
            json_header = {'Content-Type': 'application/json'}
            tap_request = request.Request(self.__full_url, data=query.encode('utf8'), headers=json_header)
            tap_response = request.urlopen(tap_request)
            body = tap_response.read().decode('utf8')
            self.__can_connect = True
            return json.loads(body)
        except Exception as error:
            self.__can_connect = False
            print('QUERY:', query)
            print('ERROR', error)
            return json.dumps({})
