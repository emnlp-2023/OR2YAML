#!/usr/bin/env python

import os
import sys
import numpy as np
import openreview
import yaml
from argparse import ArgumentParser

def parse_args():
    parser = ArgumentParser(description = 'Convert "Notes" into a draft YAML file (to be manually revised).')
    arg_group = parser.add_argument_group( 'Required arguments' )
    arg_group.add_argument('-u', '--username', type = str, dest = 'username', \
                           help = 'Username for OpenReview', required = True)
    arg_group.add_argument('-p', '--password', type = str, dest = 'password', \
                           help = 'Password for OpenReview', required = True)
    arg_group.add_argument('-n', '--notes', type = str, dest = 'notes', \
                           help = 'Notes in an NPZ file', default = 'EMNLP2023-Conference.npz')
    arg_group.add_argument('-v', '--volume', type = str, dest = 'volume', \
                           help = 'Main or Findings', default = 'Main')
    arg_group.add_argument('-m', '--mapfile', type = str, dest = 'mapfile', \
                           help = 'Mapping file', required = True)
    arg_group.add_argument('-o', '--output', type = str, dest = 'output', \
                           help = 'Output YAML file', default = 'papers.yml')
    return parser.parse_args()

def load_notes(npz_file):
    print (f"Loading {npz_file}", file = sys.stderr)
    loaded_array = np.load(npz_file, allow_pickle = True)
    notes = loaded_array['notes']
    return notes

def load_mapfile(filename):
    lines = []
    with open(filename, "r") as f:
        lines = [s.rstrip() for s in f.readlines()]
    data = {}
    for line in lines:
        elems = line.split("\t")
        if (len(elems) < 2):
            continue
        byte = elems[0].encode('latin-1')
        k = byte.decode('unicode-escape')
        data[k] = elems[1]
    print (data, file = sys.stderr)
    return data

def escape_characters(string, charmap):
    string = string.replace('\t', ' ')
    string = string.replace('-\n', '-').replace('\n', ' ')
    string = string.replace('&', '\&').replace('\\\\&', '\&')
    string = string.replace('%', '\%').replace('\\\\%', '\%')

    # string = string.replace('_', '\_').replace('\\\\_', '\_')  ## Bare < Math & URL
    # string = string.replace('$', '\$').replace('\\$', '\$')    ## Bare < Math

    for char in charmap.keys():
        string = string.replace(char, charmap[char])
    return string

def get_preferred_name(names, charmap):
    # Not sure if there is always a preferred name
    preferred_name = names[0]
    if len(names) > 1:
        for name in names:
            if 'preferred' in name.keys() and name['preferred']:
                preferred_name = name
                break
    parsed_name = {}
    if 'first' in preferred_name.keys():
        parsed_name['first_name'] = escape_characters(preferred_name['first'], charmap)
        parsed_name['last_name'] = escape_characters(preferred_name['last'], charmap)
        if preferred_name['middle'] and preferred_name['middle'] != '':
            parsed_name['middle_name'] = escape_characters(preferred_name['middle'], charmap)
    else:
        parsed_name['full_name'] = escape_characters(preferred_name['fullname'], charmap)

    return parsed_name

def note2yaml(note, charmap):
    data = {}

    # Obligatory fields
    data['id'] = note.id
    data['file'] = f"EMNLP2023/{note.id}.pdf"
    for field in ['title', 'abstract', 'venue']:
        data[field] = escape_characters(note.content[field]['value'], charmap)
    data['keywords'] = [escape_characters(kw, charmap) for kw in note.content['keywords']['value']]
    data['authors'] = []
    for i in range (0, len(note.content['authorids']['value'])):
        print (note.content['authorids']['value'][i])
        try:
            mp = client.get_profile(note.content['authorids']['value'][i])
            names = mp.content['names']
            print (names)
            preferred_name = get_preferred_name(names, charmap)
            data['authors'].append(preferred_name)
        except:
            name = escape_characters(note.content['authors']['value'][i], charmap)
            data['authors'].append({'full_name' : name})
            print (f"No Profile for {name}")

    data['attributes'] = {}
    if note.content['Submission_Type']['value'] == 'Regular Long Paper':
        data['attributes']['paper_type'] = 'long'
    elif note.content['Submission_Type']['value'] == 'Regular Short Paper':
        data['attributes']['paper_type'] = 'short'
    data['attributes']['submitted_area'] = note.content['Submission_Track']['value']

    # Optional field
    if 'supplementary_materials' in note.content.keys() and len(note.content['supplementary_materials']['value']) > 0:
        ext = note.content['supplementary_materials']['value'].split('.')[-1]
        data['attachment'] = f"EMNLP2023/{note.id}.attachment.{ext}"

    return data

def notes2yaml(submissions, target_volumes, charmap):
    print (target_volumes, file = sys.stderr)
    data = []
    for note in submissions:
        if note.content['venue']['value'] in target_volumes:
            data.append(note2yaml(note, charmap))
    return data

def dump_yaml(data, filename):
    print (f"{len(data)} records", file = sys.stderr)
    print (f"Saving into {filename}", file = sys.stderr)
    with open(filename, "w") as yamlfile:
        yaml.dump(data, yamlfile, default_flow_style=False)

if __name__ == "__main__":
    args = parse_args()

    target_volumes = []
    if args.volume in ['Main', 'Findings']:
        for prefix in ['EMNLP 2023 ', 'EMNLP 2023 Conditional ', 'ARR Commitment to EMNLP 2023 ']:
            target_volumes.append(prefix + args.volume)
        # target_volumes.append('EMNLP 2023 ' + args.volume)
        # target_volumes.append('EMNLP 2023 Conditional ' + args.volume)
        # target_volumes.append('ARR Commitment to EMNLP 2023 ' + args.volume)
    else:
        print (f"Invalid volume is specified: {args.volume}", file = sys.stderr)
        sys.exit()

    client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net', username=args.username, password=args.password)
    notes = load_notes(args.notes)
    mapper = load_mapfile(args.mapfile)
    data = notes2yaml(notes, target_volumes, mapper)
    dump_yaml(data, args.output)
