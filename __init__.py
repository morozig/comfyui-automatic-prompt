"""
@author: morozig
@title: comfyui-automatic-prompt
@nickname: ComfyUI Automatic Prompt
@description: Clip Text Encode node with some Automatic1111 features
"""

import os
import sys
import logging
import importlib
from .automatic_prompt.automatic_prompt_node import AutomaticPrompt

log = logging.getLogger("comfyui-automatic-prompt")
log.propagate = False
if not log.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("[AutomaticPrompt] %(levelname)s: %(message)s"))
    log.addHandler(h)

if os.environ.get("AUTOMATICPROMPT_DEBUG"):
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)

if not importlib.util.find_spec("comfy.hooks"):
    log.warning(
        "Your ComfyUI version is too old. Update your installation."
    )

NODE_CLASS_MAPPINGS = {
    "Automatic Prompt" : AutomaticPrompt,
}

__all__ = ['NODE_CLASS_MAPPINGS']
