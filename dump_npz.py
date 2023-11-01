#!/usr/bin/env python

import sys
import numpy as np

if len(sys.argv) < 3:
    print(f"{sys.argv[0]} npz_file array_name", file = sys.stderr)
    exit(1)

npz_file = sys.argv[1]
array_name = sys.argv[2]

loaded_array = np.load(npz_file, allow_pickle = True)
np.savetxt(sys.stdout, loaded_array[array_name], fmt="%s")
