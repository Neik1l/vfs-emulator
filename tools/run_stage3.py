# tools/run_stage3.py
import sys, argparse
from stages.stage3_vfs import main as stage3_main

if __name__ == "__main__":
    # можно вынести дефолтные vfs/examples и scripts
    stage3_main()