#!/usr/bin/env python3
import sys
import os

script_path = os.path.realpath(__file__)
project_root = os.path.dirname(script_path)
sys.path.insert(0, project_root)

from ui.app import main

if __name__ == "__main__":
    main()
