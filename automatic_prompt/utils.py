import logging
from ..prompt_control.utils import consolidate_schedule, find_nonscheduled_loras
from ..prompt_control.nodes_lazy import create_hook_nodes_for_lora

log = logging.getLogger("comfyui-automatic-prompt")

def build_lora_graph(graph, schedule, clip):
  # This gets rid of non-existent LoRAs
  consolidated = consolidate_schedule(schedule)
  non_scheduled = find_nonscheduled_loras(consolidated)

  hook_nodes = {}
  start_pct = 0.0

  def key(lora, info):
    return f"{lora}-{info['weight']}-{info['weight_clip']}"

  for end_pct, loras in consolidated:
    for lora, info in loras.items():
      k = key(lora, info)
      existing_node = hook_nodes.get(k)
      if non_scheduled.get(lora) == info:
        hook_nodes[k] = create_hook_nodes_for_lora(graph, lora, info, existing_node, 0.0, 1.0)
      else:
        hook_nodes[k] = create_hook_nodes_for_lora(graph, lora, info, existing_node, start_pct, end_pct)
    start_pct = end_pct

  hooks = []
  # Attach the keyframe chain to the hook node
  for hook, kfs in hook_nodes.values():
    n = graph.node("SetHookKeyframes")
    n.set_input("hooks", hook.out(0))
    n.set_input("hook_kf", kfs.out(0))
    hooks.append(n)

  res = None
  # Finally, combine all hooks
  if len(hooks) > 0:
    res = hooks[0]
    for h in hooks[1:]:
      n = graph.node("CombineHooks2")
      n.set_input("hooks_A", res.out(0))
      n.set_input("hooks_B", h.out(0))
      res = n
    res = res.out(0)
    n = graph.node("SetClipHooks")
    n.set_input("clip", clip)
    n.set_input("hooks", res)
    n.set_input("apply_to_conds", True)
    n.set_input("schedule_clip", True)
    clip = n.out(0)

  return clip
