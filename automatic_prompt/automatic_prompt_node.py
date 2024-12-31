from comfy_execution.graph_utils import GraphBuilder
from ..prompt_control.parser import parse_prompt_schedules
from .utils import build_lora_graph
from ..prompt_control.nodes_lazy import build_scheduled_prompts

class AutomaticPrompt:
  CATEGORY = "automatic-prompt"
  @classmethod    
  def INPUT_TYPES(s):
    return { 
      "required": {
        "clip": ("CLIP", {"rawLink": True}),
        "text": ("STRING", {"multiline": True}),
      },
    }
  RETURN_TYPES = ("CONDITIONING",)
  FUNCTION = "apply"
  DESCRIPTION = "Adds some Automatic1111 features to your prompt"

  def apply(self, clip, text):
    schedules = parse_prompt_schedules(text)
    graph = GraphBuilder()
    clip = build_lora_graph(graph, schedules, clip)
    return build_scheduled_prompts(graph, schedules, clip)
