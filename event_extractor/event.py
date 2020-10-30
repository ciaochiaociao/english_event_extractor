# coding: utf-8
from typing import List, Dict
from collections import OrderedDict
from event_extractor.utils import lprint


def read_doc_id_list(doc_id_list: str) -> Dict[str, str]:
    import csv
    with open(doc_id_list, 'r') as f:
        did_ = dict([(col[0], col[1]) for col in csv.reader(f, delimiter='\t')])

    return did_


class Event:
    def __init__(self):
        self.doc = None
        self.did = None
        self.sid = None
        self.id = None
        self.abs_id = None
        self.event_type = None  # event type
        self.event_word = None  # event word
        self.role_type = []  # role type
        self.role_word = []  # role word
        self.event_attr = []  # [sid, token_b, token_e]
        self.role_attr = []  # [sid, token_b, token_e, e_type]
        self.role_char_b = []
        self.role_char_e = []

    @staticmethod
    def read_event_file(output_file: str, corenlp_json_file: str, doc_id_dict: dict) -> List['Event']:
        import json

        print(output_file)
        # put into Event structure
        event_list = []
        doc = {}
        # main program
        with open(output_file) as fh:
            init, has_event = True, True
            cur_event = None

            for line in fh:

                if line == "\n":  # The end of lines an event
                    init = True
                    if cur_event is not None:
                        event_list.append(cur_event)
                        cur_event = None

                elif init:  # The begining of an event (Trigger line)
                    init = False
                    line = (line.rstrip("\n")).split("\t")
                    event_type = line[1]  # EventType

                    if event_type == "O":  # no event
                        has_event = False
                    else:
                        cur_event = Event()
                        has_event = True
                        assert len(line[0].split("#")) == 4
                        [docID, sid, token_b, token_e] = line[0].split("#")

                        # fix the bug of flie names with ) at the end in the event extraction program
                        if '(' in docID and ')' not in docID:
                            docID += ')'

                        if docID not in doc:
                            with open(corenlp_json_file, 'r') as _f:
                                data = json.load(_f)

                            plain_text = []
                            for i in range(0, len(data['sentences'])):
                                sentence = ""
                                for j, tok in enumerate(data['sentences'][i]['tokens']):
                                    sentence += tok['originalText'] + ' '
                                plain_text.append(sentence)

                            text_tok = [sent.split(' ') for sent in plain_text]
                            doc[docID] = text_tok

                        lprint('docID: ' + repr(docID) + ' doc_id_dict: ' + repr(doc_id_dict))
                        try:
                            cur_event.doc = doc_id_dict[int(docID)]
                        except KeyError:
                            lprint('doc_id_dict', doc_id_dict)
                            lprint('docID', docID)
                            lprint('int(docID)', int(docID))
                            lprint('doc_id_dict[docID]', doc_id_dict[docID])
                            lprint('doc_id_dict[int(docID)]', doc_id_dict[int(docID)])
                            raise
                        cur_event.did = int(docID)
                        cur_event.sid = int(sid)
                        cur_event.event_type = event_type
                        cur_event.event_word = ' '.join(text_tok[int(sid)][int(token_b):int(token_e) + 1])
                        cur_event.event_attr = [int(sid), int(token_b), int(token_e),
                                                data['sentences'][int(sid)]['tokens'][int(token_b)]['characterOffsetBegin'],
                                                data['sentences'][int(sid)]['tokens'][int(token_e)]['characterOffsetEnd']]

                elif has_event:  # the following lines of an event (Roles line)
                    line = (line.rstrip("\n")).split("\t")
                    role_type = line[1]
                    cur_event.s_text = plain_text[int(line[0].split('#')[1])]

                    if role_type != "O":
                        assert len(line[0].split('#')) == 5
                        docID, sid, token_b, token_e, e_type = line[0].split('#')
                        cur_event.role_type.append(role_type)
                        cur_event.role_word.append(' '.join(text_tok[int(sid)][int(token_b):int(token_e) + 1]))
                        cur_event.role_attr.append([int(sid), int(token_b), int(token_e), e_type])
                        cur_event.role_char_b.append(
                            data['sentences'][int(sid)]['tokens'][int(token_b)]['characterOffsetBegin'])
                        cur_event.role_char_e.append(
                            data['sentences'][int(sid)]['tokens'][int(token_e)]['characterOffsetEnd'])

        # add more attributes
        from collections import OrderedDict
        import copy

        e_l = copy.deepcopy(event_list)
        # id
        id_ = 0
        lastsid = 0
        abs_id = 0
        for event in e_l:

            # set id, sid, abs_id
            if event.sid != lastsid:
                id_ = 0
            lastsid = event.sid
            event.id = id_
            event.abs_id = abs_id
            id_ += 1
            abs_id += 1
            type_arr = event.event_type.split('-')

            # set type, subtype
            if len(type_arr) == 2:
                (event.type, event.subtype) = type_arr
            elif len(type_arr) == 1:
                event.type = type_arr[0]
            else:
                raise ValueError(event.type, ': event has no type or type str can not be parsed.')

            # set trigger
            event.trigger = OrderedDict({
                'text': event.event_word,
                'token_b': event.event_attr[1],
                'token_e': event.event_attr[2] + 1,
                'char_b': event.event_attr[3],
                'char_e': event.event_attr[4]
            })

            event.args = []
            for role in list(zip(event.role_word, event.role_type, event.role_attr, event.role_char_b, event.role_char_e)):
                event.args.append(OrderedDict({
                    'sid': role[2][0],
                    'role': role[1],
                    'text': role[0],
                    'ner': role[2][3],
                    'token_b': role[2][1],
                    'token_e': role[2][2] + 1,
                    'char_b': role[3],
                    'char_e': role[4]

                }))
        return e_l

    @staticmethod
    def to_multidoc_dict(e_l: List['Event']) -> OrderedDict:

        from collections import OrderedDict

        # sort attributes

        ordered_e_l = []

        for event in e_l:
            ordered_event = OrderedDict()
            for key in ['did', 'id', 'sid', 'type', 'subtype', 's_text', 'trigger', 'args']:
                if key in event.__dict__.keys():
                    ordered_event.update({key: event.__dict__[key]})
            ordered_e_l.append(ordered_event)

        # sort arg attributes

        for event in ordered_e_l:

            args = []
            if len(event['args']) != 0:
                for arg in event['args']:
                    ordered_arg = OrderedDict()
                    for key in ['role', 'text', 'char_b', 'char_e', 'ner']:
                        if key in arg.keys():
                            ordered_arg.update({key: arg[key]})
                    args.append(ordered_arg)
                event['args'] = args

        # sort trigger attributes

        for event in ordered_e_l:
            attrs = ['text', 'char_b', 'char_e']
            ordered_attr = OrderedDict()
            for attr in attrs:
                ordered_attr.update({attr: event['trigger'][attr]})
            event['trigger'] = ordered_attr

        # add fullid
        out = OrderedDict()
        for ordered_event in ordered_e_l:
            fullid = 'D' + 'tempfile' + '-S' + str(ordered_event['sid']) + '-EVM' + str(ordered_event['id'])

            # don't output these redundant attributes
            ordered_event.pop('did')
            ordered_event.pop('id')

            out.update({fullid: ordered_event})

        return out
