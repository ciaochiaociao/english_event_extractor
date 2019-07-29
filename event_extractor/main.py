#!/usr/bin/python3
# coding: utf-8
import json
import re
import sys
import shlex, subprocess
import os
import shutil
from  typing import List, Tuple, Dict
import subprocess
from event_extractor.utils import setup_logger, logtime
import logging
from event_extractor.event import *
from event_extractor.utils import lprint


# set up loggers
debug_logger = setup_logger('debug', 'debug.log', level=logging.DEBUG)
info_logger = setup_logger('info', 'info.log', level=logging.INFO)
error_logger = setup_logger('error', 'error.log', level=logging.ERROR)

FILE_DIR_PATH = os.path.dirname(os.path.abspath(__file__))

CWD = os.getcwd()
ALL_OUTPUTS_FOLDER = os.path.join(CWD, 'outputs')
CORENLP_STORE_FOLDER = os.path.join(ALL_OUTPUTS_FOLDER, 'corenlp_jsons')
OUTPUT_FOLDER = os.path.join(ALL_OUTPUTS_FOLDER, 'output')
MD_FOLDER = os.path.join(ALL_OUTPUTS_FOLDER, 'multi_doc')
CORENLP_INPUT_FOLDER = 'temp'

def stanfordcorenlp_command(path2corenlp, inputfile) -> str:
    return "java -cp " + os.path.join(path2corenlp, "*") + " -Xmx8g edu.stanford.nlp.pipeline.StanfordCoreNLP " + " -annotators tokenize,ssplit,pos,depparse,lemma,ner,parse " + " -ner.applyFineGrained false " + " -file " + inputfile + " -outputFormat json "


@logtime('info')
def corenlp_gen_data(docID_list) -> dict:
    # note that the author (Bishan Yang) use version 3.6
    path2corenlp = os.path.join(FILE_DIR_PATH, "stanford-corenlp-full-2018-10-05") # ver. 3.9.2
    lprint(docID_list)
    data_dict = {}
    for docID in docID_list:
        lprint('docID:', docID)
        cmd = stanfordcorenlp_command(path2corenlp, os.path.join(CORENLP_INPUT_FOLDER, str(docID)))  # store file as <docID>.json
        args = shlex.split(cmd)
        ret = subprocess.check_output(args)  # ignore return
        info_logger.info(ret)
        with open(str(docID) + ".json", 'r') as f:
            data_dict[docID] = json.load(f)
    
    return data_dict


class EventExtractor:

    EEE_INPUT_PATH = os.path.join(FILE_DIR_PATH, "EventEntityExtractor/input")
    EEE_OUTPUT_FILE = os.path.join(FILE_DIR_PATH, 'EventEntityExtractor/output/joint.results.txt')

    @staticmethod
    @logtime('info')
    def extract(doc_id_dict: Dict[str, str]) -> Event:
        
        docID_list = list(doc_id_dict.keys())
        id_ = docID_list[0]
        lprint('id_', id_)
        lprint('docID_list', docID_list)
        
        OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, str(id_) + '.event.entity')
        CORENLP_STORE_FILE = os.path.join(CORENLP_STORE_FOLDER, str(id_) + '.json')
        JSON_OUTPUT_FILE = os.path.join(MD_FOLDER, str(id_) + '.md.json')

        # store CoreNLP json data
        data_dict = corenlp_gen_data(docID_list)
        _, attr_dict = EventExtractor.get_text_attr(data_dict)
        assert len(docID_list) == len(data_dict) == len(attr_dict)
        
        # generate required file for Event Extractor
        EventExtractor.gen_ace_test_conll(attr_dict, docID_list)
        EventExtractor.gen_stanford_ner(data_dict, docID_list)
        EventExtractor.gen_stanford_dep(data_dict, docID_list)

        # run Event Extraction
        os.chdir(os.path.join(FILE_DIR_PATH, 'EventEntityExtractor'))  # to execute, it is required to cd to this folder
#         input(os.getcwd())
        proc = subprocess.Popen('./Release/JEE', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()

        # logging
        if stdout:
            print('stdout: ', stdout.decode('utf-8'))
            info_logger.info('[docID]: ' + str(id_) + ' [stdout]: ' + stdout.decode('utf-8'))
        if stderr:
            error_logger.error('[docID]: ' + str(id_) + ' [stderr]: ' + stderr.decode('utf-8'))
        
        # copy the output file to the cwd
#         input()
        shutil.move(EventExtractor.EEE_OUTPUT_FILE, OUTPUT_FILE)
        shutil.move(os.path.join(CWD, str(id_) + '.json'), CORENLP_STORE_FILE)
        
        os.chdir(CWD)

        # Read Event File
        event = Event.read_event_file(OUTPUT_FILE, CORENLP_STORE_FILE, doc_id_dict)
        
        # write to JSON file
        with open(JSON_OUTPUT_FILE, 'w') as f:
            json.dump(Event.to_multidoc_dict(event), f)
                  
        return event
    
    @staticmethod
    @logtime('info')
    def get_text_attr(data_dict) -> Tuple[dict, dict]:
        text_dict, attr_dict = {}, {}

        for docID in data_dict.keys():
            data = data_dict[docID]

            plain_text = []
            sent_attr = [] # naryTree, words, posTags, lemmas
            for i in range(0, len(data['sentences'])):
                sentence = ""
                attr = {'naryTree':"", 'words':[], 'posTags':[], 'lemmas':[]}

                naryTree = re.sub("\s\s+" , " ", data['sentences'][i]['parse'])
                attr['naryTree'] = naryTree

                for j, tok in enumerate(data['sentences'][i]['tokens']):
                    if j == 0:
                        sentence += tok['originalText']
                    else:
                        sentence += tok['before'] + tok['originalText']
                    attr['words'].append(tok['word'])
                    attr['posTags'].append(tok['pos'])
                    attr['lemmas'].append(tok['lemma'])


                plain_text.append(sentence)
                sent_attr.append(attr)

            assert len(plain_text) == len(sent_attr)
            text_dict[docID] = plain_text
            attr_dict[docID] = sent_attr

        return text_dict, attr_dict

    @staticmethod
    @logtime('info')
    def gen_ace_test_conll(attr_dict, docID_list):
        """Write to <EEE_INPUT_PATH>/ace.test.conll"""
        with open(os.path.join(EventExtractor.EEE_INPUT_PATH, "ace.test.conll"), 'w') as f:

            for docID in docID_list:
                sent_attr = attr_dict[docID]

                f.write("#begin document (" + str(docID) + "); part 0\n")

                for sentID in range(0, len(sent_attr)):

                    new_parse = []
                    test_string = sent_attr[sentID]['naryTree']
                    start_idx, end_idx = 0, 0
                    for i in range(0, len(test_string)-2):
                        if test_string[i:i+3] == ") (":
                            end_idx = i+1
                            new_parse.append(test_string[start_idx : end_idx])
                            start_idx = i+2
                        elif i == len(test_string) - 3: # reach end
                            new_parse.append(test_string[start_idx : ])

                    res = []
                    for naryTree_i, (i, words_i) in zip(new_parse, enumerate(sent_attr[sentID]['words'])):
                        tok = '(' + sent_attr[sentID]['posTags'][i] + ' ' + words_i + ')'
                        res.append(''.join(naryTree_i.replace(tok,"*").split()))

                    for wordID in range(0, len(sent_attr[sentID]['words'])):
                        f.write(str(docID) + "\t" + str(sentID) + "\t" + str(wordID) + "\t" +
                                sent_attr[sentID]['words'][wordID] + "\t" +
                                sent_attr[sentID]['posTags'][wordID] + "\t" + res[wordID] + "\t" + 
                                sent_attr[sentID]['lemmas'][wordID] + "\t" + 
                                "-\t-\t-\t-\tO" + "\n")
                    f.write("\n")

                f.write("#end document\n")

    
    @staticmethod
    @logtime('info')
    def gen_stanford_ner(data_dict, docID_list):
        """Write to <EEE_INPUT_PATH>/ace.test.stanford.ner.txt"""
        with open(os.path.join(EventExtractor.EEE_INPUT_PATH, "ace.test.stanford.ner.txt"), 'w') as f:
            for docID in docID_list:
                data = data_dict[docID]
                for sentID in range(0, len(data['sentences'])):
                    sent_em = data['sentences'][sentID]['entitymentions']
#                     logging.getLogger('debug').debug('sent_em: ' + repr(sent_em))
                    for _, val in enumerate(sent_em):
                        line = "{}\t{}\t{}\t{},{}\n".format(val['ner'], docID, sentID, val['tokenBegin'], val['tokenEnd']-1)
                        f.write(line)
#         lprint()
#         input()

    @staticmethod
    @logtime('info')
    def gen_stanford_dep(data_dict, docID_list):
        """Write to <EEE_INPUT_PATH>/ace.test.dependencies.txt"""
        with open(os.path.join(EventExtractor.EEE_INPUT_PATH, "ace.test.dependencies.txt"), 'w') as f:

            for docID in docID_list:
                data = data_dict[docID]

                for sentID in range(0, len(data['sentences'])):
                    # sd: stanford dependencies
                    sent_sd = data['sentences'][sentID]['basicDependencies']
                    res = []
                    for idx, dep in enumerate(sent_sd):
                        try:
                            tok = "{}({}-{}, {}-{})".format(dep['dep'].lower(), dep['governorGloss'], dep['governor'], 
                                                        dep['dependentGloss'], dep['dependent'])
                        except KeyError:
                            logging.getLogger('error').error('[Dependency Key Error] docID: ' + str(docID) + 
                                                             ' sentID: ' + str(sentID) + " dep:" + str(idx))
                            continue
                            
                        res.append(tok)
                        f.write(tok + "\n")

                    f.write("\n")
