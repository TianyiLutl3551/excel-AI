import os
import sys
import pandas as pd
import extract_msg
from bs4 import BeautifulSoup
import re
from datetime import datetime

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.processors.msg_processor import MsgProcessor
from prompts.prompt import get_llm_prompt as get_blue_llm_prompt
from prompts.prompt2 import get_llm_prompt2 as get_red_llm_prompt 