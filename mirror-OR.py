#!/usr/bin/env python

import os
import sys
import numpy as np
import openreview
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from argparse import ArgumentParser

def parse_args():
    parser = ArgumentParser(description = 'Retrieve "Notes" and download only updated files.')
    arg_group = parser.add_argument_group( 'Required arguments' )
    arg_group.add_argument('-u', '--username', type = str, dest = 'username', \
                           help = 'Username for OpenReview', required = True)
    arg_group.add_argument('-p', '--password', type = str, dest = 'password', \
                           help = 'Password for OpenReview', required = True)
    arg_group.add_argument('-c', '--channel', type = str, dest = 'channel', \
                           help = 'Channel at OpenReview', default = 'Conference')
    arg_group.add_argument('-l', '--latest', type = str, dest = 'latest', \
                           help = 'Latest file of notes (npz)', required = False)
    return parser.parse_args()

def load_notes_as_hash(npz_file):
    print (f"Loading {npz_file}", file=sys.stderr)
    loaded_array = np.load(npz_file, allow_pickle = True)
    notes = loaded_array['notes']
    hash = {}
    for note in notes:
        hash[note.id] = note
    return hash

def download_to_folder(args):
    output_dir, note_id, field_name, extension = args
    f = client.get_attachment(id=note_id, field_name=field_name)
    with open(os.path.join(output_dir, f"{note_id}.{extension}"),'wb') as op: op.write(f)

if __name__ == "__main__":
    args = parse_args()

    target_channel = ''
    if args.channel in ['Conference', 'ARR_Commitment']:
        target_channel = 'EMNLP/2023/' + args.channel + '/-/Submission'
    else:
        print (f"Invalid channel is specified: {args.channel}", file = sys.stderr)
        sys.exit()

    client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net', username=args.username, password=args.password)
    notes = client.get_all_notes(invitation=target_channel)
    output_file = args.channel + '.npz'
    np.savez_compressed(output_file, notes=notes)
    print (f"Saved notes in {output_file}", file = sys.stderr)

    output_dir = args.channel
    download_args = []

    if args.latest != None:
        old_notes = load_notes_as_hash(args.latest)
        entries = len(old_notes.keys())
        print (f"{entries} notes in {args.latest}", file = sys.stderr)
    else:
        os.mkdir(output_dir)
        print (f"mkdir {output_dir}", file = sys.stderr)

    for note in notes:
        if args.latest != None and note.id in old_notes.keys() and note.mdate <= old_notes[note.id].mdate:
            continue
        # Prepare PDF arguments
        if 'pdf' in note.content.keys() and len(note.content['pdf']['value']) > 0:
            download_args.append((output_dir, note.id, 'pdf', 'pdf'))
        # Prepare supplementary material arguments (this assumes attachment is not a PDF)
        if 'supplementary_materials' in note.content.keys() and len(note.content['supplementary_materials']['value']) > 0:
            ext = note.content['supplementary_materials']['value'].split('.')[-1]
            download_args.append((output_dir, note.id, 'supplementary_materials', 'attachment.' + ext))

    n = len(download_args)
    print (f"{n} items to newly download.", file = sys.stderr)

    if n > 0:
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(tqdm(executor.map(download_to_folder, download_args), total=len(download_args)))
