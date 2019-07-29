import os
import json
from distutils.dir_util import copy_tree

def gen_doc_index(infolder, out_fname=None, write_to_text=False, write_to_json=False):

    from collections import OrderedDict
    import json
    import csv
    
    doc_id_dict = OrderedDict()
    
    files = (file for file in sorted(os.listdir(infolder)) 
         if os.path.isfile(os.path.join(infolder, file)))  # get only files
    
    for did, fname in enumerate(files): # ....txt
        doc_id_dict[did] = fname

    if write_to_json:
        with open(out_fname + '.json', 'w') as f:
            json.dump(doc_id_dict, f)
            
    if write_to_text:
        with open(out_fname + '.txt', 'w') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(doc_id_dict.items())
            
    return doc_id_dict

def copy_and_rename(infolder, outfolder):
    
    import shutil

    if os.path.exists(outfolder):
        shutil.rmtree(outfolder)
    os.mkdir(outfolder)
    for did, fname in doc_id_dict.items():
        shutil.copy(os.path.join(infolder, fname), os.path.join('temp', str(did)))
        
from event_extractor.main import EventExtractor
from event_extractor.event import Event
from event_extractor.utils import lprint
import logging
import csv
import subprocess

info_logger = logging.getLogger('info')
error_logger = logging.getLogger('error')

with open('did.txt', 'r') as f:
    data = csv.reader(f, delimiter='\t')
    rest_data = list(data)[213:]

for item in rest_data:
    info_logger.info('--- start extracting doc ' + item[0] + '---')
    try:
        EventExtractor.extract({int(item[0]): item[1]})
    except subprocess.CalledProcessError as e:
        error_logger.error('[docID] {} [doc] {} \n[stderr/stdout]: \n{}'.format(
            item[0], item[1], str(e.output)))
    info_logger.info('--- finish extracting ---')
