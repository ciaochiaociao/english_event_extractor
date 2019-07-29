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

# generate did list and copy the original files to a folder
input_folder = 'english_1990'
clean_fname_folder = 'temp'
doc_id_dict = gen_doc_index(infolder=input_folder, out_fname='did', write_to_text=True, write_to_json=True)
copy_and_rename(infolder=input_folder, outfolder=clean_fname_folder)

# batch 
for id_ in doc_id_dict.keys():
    logging.getLogger('info').info('--- start extracting doc ' + str(id_) + '---')
    EventExtractor.extract({id_: doc_id_dict[id_]})
    logging.getLogger('info').info('--- finish extracting ---')
