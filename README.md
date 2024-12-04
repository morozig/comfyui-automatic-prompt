# ComfyUI prompt control

Nodes for LoRA and prompt scheduling that make basic operations in ComfyUI completely prompt-controllable.

LoRA and prompt scheduling should produce identical output to the equivalent ComfyUI workflow using multiple samplers or the various conditioning manipulation nodes. If you find situations where this is not the case, please report a bug.

## What can it do?

Things you can control via the prompt:
- Prompt editing and filtering without multiple samplers
- LoRA loading and scheduling (including LoRA block weights)
- Prompt masking and area control, combining prompts and interpolation
- SDXL parameters
- Other miscellaneous things

[This example workflow](workflows/example.json?raw=1) implements a two-pass workflow illustrating most scheduling features.

The tools in this repository combine well with the macro and wildcard functionality in [comfyui-utility-nodes](https://github.com/asagi4/comfyui-utility-nodes)

## Requirements

You need to have `lark` installed in your Python environment for parsing to work (If you reuse A1111's venv, it'll already be there)

If you use the portable version of ComfyUI on Windows with its embedded Python, you must open a terminal in the ComfyUI installation directory and run the command:
```
.\python_embeded\python.exe -m pip install lark
```

Then restart ComfyUI afterwards.

## Notable changes

I try to avoid behavioural changes that break old prompts, but they may happen occasionally.

- 2024-12-03 ComfyUI merged support for model/conditioning hooks. There are two new nodes, `PCEncodeSchedule` and `PCLoraHooksFromSchedule` that can be used in combination with the hook nodes. Some functionality is still missing from them, but going forward, these nodes will be the only nodes supported; **I will not spend significant time fixing bugs in the old monkeypatched nodes anymore.**
- 2024-02-02 The node will now automatically enable offloading LoRA backup weights to the CPU if you run out of memory during LoRA operations, even when `--highvram` is specified. This change persists until ComfyUI is restarted.
- 2024-01-14 Multiple `CLIP_L` instances are now joined with a space separator instead of concatenated.
- 2024-01-09 AITemplate support dropped. I don't recommend or test AITemplate anymore. Use Stable-Fast instead (see below for info)
- 2024-01-08 Prompt control now enables in-place weight updates on the model. This shouldn't affect anything, but increases performance slightly. You can disable this by setting the environment variable `PC_NO_INPLACE_UPDATE` to any non-empty value.
- 2023-12-28 MASK now uses ComfyUI's `mask_strength` attribute instead of calculating it on its own. This changes its behaviour slightly.
- 2023-12-06: Removed `JinjaRender`, `SimpleWildcard`, `ConditioningCutoff`, `CondLinearInterpolate` and `StringConcat`. For the first two, see [this repository](https://github.com/asagi4/comfyui-utility-nodes) for mostly-compatible implementations.
- 2023-10-04: `STYLE:...` syntax changed to `STYLE(...)`

## Note on how schedules work

ComfyUI does not use the step number to determine whether to apply conds; instead, it uses the sampler's timestep value which is affected by the scheduler you're using. This means that when the sampler scheduler isn't linear, the schedules generated by prompt control will not be either.

# Scheduling syntax

Syntax is like A1111 for now, but only fractions are supported for steps. LoRAs are scheduled by including them in a scheduling expression.

```
a [large::0.1] [cat|dog:0.05] [<lora:somelora:0.5:0.6>::0.5]
[in a park:in space:0.4]
```

## Scheduled prompts

There are two forms of scheduled prompts.

### Basic scheduling expressions
Basic expressions take the form `[before:after:X]` where `X` is the switch point, a decimal number between 0.0 and 1.0 inclusive, representing 0 to 100% of timesteps.
For example:
```
a [red:blue:0.5] cat
```
switches from `a red cat` to `a blue cat` at 0.5. `before` and `after` can be arbitrary prompts (`after` can also be empty), including other scheduling expressions, allowing nesting:
```
a [red:[blue::0.7]:0.5] cat
```

switches from `a red cat` to `a blue cat` at 0.5 and to `a cat` at 0.7


**Note:** As a special case, `[cat:0.5]` is like `[:cat:0.5]` meaning it switches from empty to `cat` at 0.5. Currently, `[:cat:0.5]` doesn't actually parse correctly, so you **must** use the shortcut form

### Range expressions

You can also use `a [during:after:0.3,0.7]` as a shortcut. The prompt be `a` until 0.3, `a during` until 0.7, and then `a after`. This form is equivalent to `[[during:after:0.7]:0.3]`
For convenience, `[during:0.1,0.4]` is equivalent to `[during::0.1,0.4]`

## Tag selection
Using the `FilterSchedule` node, in addition to step percentages, you can use a *tag* to select part of an input:
```
a large [dog:cat<lora:catlora:0.5>:SECOND_PASS]
```
Set the `tags` parameter in the `FilterSchedule` node to filter the prompt. If the tag matches any tag `tags` (comma-separated), the second option is returned (`cat`, in this case, with the LoRA). Otherwise, the first option is chosen (`dog`, without LoRA).

the values in `tags` are case-insensitive, but the tags in the input **must** be uppercase A-Z and underscores only, or they won't be recognized. That is, `[dog:cat:hr]` will not work.

For example, a prompt
```
a [black:blue:X] [cat:dog:Y] [walking:running:Z] in space
```
with `tags` `x,z` would result in the prompt `a blue cat running in space`

## LoRA Scheduling
LoRAs can be scheduled by referring to them in a scheduling expression, like so:

`<lora:fulllora:1> [<lora:partialora:1>::0.5]`

This will schedule `fulllora` for the entire duration of the prompt and `partiallora` until half of sampling is complete.

`PCLoraHooksFromSchedule` creates a properly scheduled `HOOKS` object from LoRA expressions included in the prompt. The older (deprecated) `ScheduleToModel` nodes will monkeypatch ComfyUI sampling and attempt to perform LoRA loading directly.

You can refer to LoRAs by using the filename without extension and subdirectories will also be searched. For example, `<lora:cats:1>`. will match both `cats.safetensors` and `sd15/animals/cats.safetensors`. If there are multiple LoRAs with the same name, the first match will be loaded.

Alternatively, the name can include the full directory path relative to ComfyUI's search paths, without extension: `<lora:XL/sdxllora:0.5>`. In this case, the *full* path must match.

If no match is found, the node will try to replace spaces with underscores and search again. That is, `<lora:cats and dogs:1>` will find `cats_and_dogs.safetensors`. This helps with some autocompletion scripts that replace underscores with spaces.

Finally, you can give the exact path (including the extension) as shown in `LoRALoader`.


## Alternating

Alternating syntax is `[a|b:pct_steps]`, causing the prompt to alternate every `pct_steps`. `pct_steps` defaults to 0.1 if not specified. You can also have more than two options.


## Sequences

The syntax `[SEQ:a:N1:b:N2:c:N3]` is shorthand for `[a:[b:[c::N3]:N2]:N1]` ie. it switches from `a` to `b` to `c` to nothing at the specified points in sequence.

Might be useful with Jinja templating (see https://github.com/asagi4/comfyui-utility-nodes). For example:
```
[SEQ<% for x in steps(0.1, 0.9, 0.1) %>:<lora:test:<= sin(x*pi) + 0.1 =>>:<= x =><% endfor %>]
```
generates a LoRA schedule based on a sinewave


## Prompt interpolation

Note: Not currently supported by `PCEncodeSchedule`

`a red [INT:dog:cat:0.2,0.8:0.05]` will attempt to interpolate the tensors for `a red dog` and `a red cat` between the specified range in as many steps of 0.05 as will fit.


## SDXL

The nodes do not treat SDXL models specially, but there are some utilities that enable SDXL specific functionality.

You can use the function `SDXL(width height, target_width target_height, crop_w crop_h)` to set SDXL prompt parameters. `SDXL()` is equivalent to `SDXL(1024 1024, 1024 1024, 0 0)` unless the default values have been overridden by `PCScheduleSettings`.

To set the `clip_l` prompt, as with `CLIPTextEncodeSDXL`, use the function `CLIP_L(prompt text goes here)`.

Things to note:
- Multiple instances of `CLIP_L` are joined with a space. That is, `CLIP_L(foo)CLIP_L(bar)` is the same as `CLIP_L(foo bar)`
- Using `BREAK` isn't supported in it; it'll just parse as the plain word BREAK.
- similarly, `AND` inside `CLIP_L` does not do anything sensible; `CLIP_L(foo AND bar)` will parse as two prompts `CLIP_L(foo` and `bar)`
- `CLIP_L` and `SDXL` have no effect on SD 1.5.
- The rest of the prompt becomes the `clip_g` prompt.
- If there is no `CLIP_L` or `SDXL`, the prompts will work as with `CLIPTextEncode`.

# Other syntax:

- `<emb:xyz>` is alternative syntax for `embedding:xyz` to work around a syntax conflict with `[embedding:xyz:0.5]` which is parsed as a schedule that switches from `embedding` to `xyz`.

- The keyword `BREAK` causes the prompt to be tokenized in separate chunks, which results in each chunk being individually padded to the text encoder's maximum token length. This is mostly equivalent to the `ConditioningConcat` node.


## Combining prompts
`AND` can be used to combine prompts. You can also use a weight at the end. It does a weighted sum of each prompt,
```
cat :1 AND dog :2
```
The weight defaults to 1 and are normalized so that `a:2 AND b:2` is equal to `a AND b`. `AND` is processed after schedule parsing, so you can change the weight mid-prompt: `cat:[1:2:0.5] AND dog`

if there is `COMFYAND()` in the prompt, the behaviour of `AND` will change to work like `ConditioningCombine`, but in practice this seems to be just slower while producing the same output.

Note: `PCEncodeSchedule` only has ComfYUI behaviour and does not have ´COMFYAND()´


## Functions

There are some "functions" that can be included in a prompt to do various things. 

Functions have the form `FUNCNAME(param1, param2, ...)`. How parameters are interpreted is up to the function.
Note: Whitespace is *not* stripped from string parameters by default. Commas can be escaped with `\,`

Like `AND`, these functions are parsed after regular scheduling syntax has been expanded, allowing things like `[AREA:MASK:0.3](...)`, in case that's somehow useful.

### SHUFFLE and SHIFT

Default parameters: `SHUFFLE(seed=0, separator=,, joiner=,)`, `SHIFT(steps=0, separator=,, joiner=,)`

`SHIFT` moves elements to the left by `steps`. The default is 0 so `SHIFT()` does nothing
`SHUFFLE` generates a random permutation with `seed` as its seed.

These functions are applied to each prompt chunk **after** `BREAK`, `AND` etc. have been parsed. The prompt is split by `separator`, the operation is applied, and it's then joined back by `joiner`.

Multiple instances of these functions are applied in the order they appear in the prompt.

**NOTE:** These functions are *not* smart about syntax and will break emphasis if the separator occurs inside parentheses. I might fix this at some point, but for now, keep this in mind.

For example:
- `SHIFT(1) cat, dog, tiger, mouse` does a shift and results in `dog, tiger, mouse, cat`. (whitespace may vary)
- `SHIFT(1,;) cat, dog ; tiger, mouse` results in `tiger, mouse, cat, dog`
- `SHUFFLE() cat, dog, tiger, mouse` results in `cat, dog, mouse, tiger`
- `SHUFFLE() SHIFT(1) cat, dog, tiger, mouse` results in `dog, mouse, tiger, cat`

- `SHIFT(1) cat,dog BREAK tiger,mouse` results in `dog,cat BREAK tiger,mouse`
- `SHIFT(1) cat, dog AND SHIFT(1) tiger, mouse` results in `dog, cat BREAK mouse, tiger`

Whitespace is *not* stripped and may also be used as a joiner or separator
- `SHIFT(1,, ) cat,dog` results in `dog cat`

### NOISE

The function `NOISE(weight, seed)` adds some random noise into the prompt. The seed is optional, and if not specified, the global RNG is used. `weight` should be between 0 and 1.

### MASK, IMASK and AREA

You can use `MASK(x1 x2, y1 y2, weight, op)` to specify a region mask for a prompt. The values are specified as a percentage with a float between `0` and `1`, or as absolute pixel values (these can't be mixed). `1` will be interpreted as a percentage instead of a pixel value.

Similarly, you can use `AREA(x1 x2, y1 y2, weight)` to specify an area for the prompt (see ComfyUI's area composition examples). The area is calculated by ComfyUI relative to your latent size.

#### Custom masks: IMASK and `PCScheduleAddMasks`

You can attach custom masks to a `PROMPT_SCHEDULE` with the `PCScheduleAddMasks` node and then refer to those masks in the prompt using `IMASK(index, weight, op)`. Indexing starts from zero, so 0 is the first attached mask etc. `PCSCheduleAddMasks` ignores empty inputs, so if you only add a mask to the `mask4` input, it will still have index 0.

Applying `PCScheduleAddMasks` multiple times *appends* masks to a schedule rather than overriding existing ones, so if you need more than 4, you can just use it more than once.

#### Behaviour of masks
If multiple `MASK`s are specified, they are combined together with ComfyUI's `MaskComposite` node, with `op` specifying the operation to use (default `multiply`). In this case, the combined mask weight can be set with `MASKW(weight)` (defaults to 1.0).

Masks assume a size of `(512, 512)`, unless overridden with `PCScheduleSettings` and pixel values will be relative to that. ComfyUI will scale the mask to match the image resolution. You can change it manually by using `MASK_SIZE(width, height)` anywhere in the prompt,

These are handled per `AND`-ed prompt, so in `prompt1 AND MASK(...) prompt2`, the mask will only affect prompt2.

The default values are `MASK(0 1, 0 1, 1)` and you can omit unnecessary ones, that is, `MASK(0 0.5, 0.3)` is `MASK(0 0.5, 0.3 1, 1)`

Note that because the default values are percentages, `MASK(0 256, 64 512)` is valid, but `MASK(0 200)` will raise an error.

Masking does not affect LoRA scheduling unless you set unet weights to 0 for a LoRA.

### FEATHER

When you use `MASK` or `IMASK`, you can also call `FEATHER(left top right bottom)` to apply feathering using ComfyUI's `FeatherMask` node. The values are in pixels and default to `0`.

If multiple masks are used, `FEATHER` is applied *before compositing* in the order they appear in the prompt, and any leftovers are applied to the combined mask. If you want to skip feathering a mask while compositing, just use `FEATHER()` with no arguments.

For example:
```
MASK(1) MASK(2) MASK(3) FEATHER(1) FEATHER() FEATHER(3) weirdmask FEATHER(4)
```

gives you a mask that is a combination of 1, 2 and 3, where 1 and 3 are feathered before compositing and then `FEATHER(4)` is applied to the composite.

The order of the `FEATHER` and `MASK` calls doesn't matter; you can have `FEATHER` before `MASK` or even interleave them.

# Schedulable LoRAs

Note: Use `PCLoraHooksFromSchedule`. It will work better.

## Old nodes
The `ScheduleToModel` node patches a model so that when sampling, it'll switch LoRAs between steps. You can apply the LoRA's effect separately to CLIP conditioning and the unet (model).

Swapping LoRAs often can be quite slow without the `--highvram` switch because ComfyUI will shuffle things between the CPU and GPU. When things stay on the GPU, it's quite fast.

If you run out of VRAM during a LoRA swap, the node will attempt to save VRAM by enabling CPU offloading for future generations even in highvram mode. This persists until ComfyUI is restarted.

You can also set the `PC_RETRY_ON_OOM` environment variable to any non-empty value to automatically retry sampling once if VRAM runs out.

## LoRA Block Weight

Note: Not supported by `PCEncodeSchedule` yet

If you have [ComfyUI Inspire Pack](https://github.com/ltdrdata/ComfyUI-Inspire-Pack) installed, you can use its Lora Block Weight syntax, for example:

```
a prompt <lora:cars:1:LBW=SD-OUTALL;A=1.0;B=0.0;>
```
The `;` is optional if there is only 1 parameter.
The syntax is the same as in the `ImpactWildcard` node, documented [here](https://github.com/ltdrdata/ComfyUI-extension-tutorials/blob/Main/ComfyUI-Impact-Pack/tutorial/ImpactWildcard.md)

# Other integrations
## Advanced CLIP encoding
Note: `perp` is not supported by `PCEncodeSchedule`

You can use the syntax `STYLE(weight_interpretation, normalization)` in a prompt to affect how prompts are interpreted.

Without any extra nodes, only `perp` is available, which does the same as [ComfyUI_PerpWeight](https://github.com/bvhari/ComfyUI_PerpWeight) extension.

If you have [Advanced CLIP Encoding nodes](https://github.com/BlenderNeko/ComfyUI_ADV_CLIP_emb/tree/master) cloned into your `custom_nodes`, more options will be available.

The style can be specified separately for each AND:ed prompt, but the first prompt is special; later prompts will "inherit" it as default. For example:

```
STYLE(A1111) a (red:1.1) cat with (brown:0.9) spots and a long tail AND an (old:0.5) dog AND a (green:1.4) (balloon:1.1)
```
will interpret everything as A1111, but
```
a (red:1.1) cat with (brown:0.9) spots and a long tail AND STYLE(A1111) an (old:0.5) dog AND a (green:1.4) (balloon:1.1)
```
Will interpret the first one using the default ComfyUI behaviour, the second prompt with A1111 and the last prompt with the default again

For things (ie. the code imports) to work, the nodes must be cloned in a directory named exactly `ComfyUI_ADV_CLIP_emb`.

## Cutoff node integration

Note: Not supported by `PCEncodeSchedule` yet.

If you have [ComfyUI Cutoff](https://github.com/BlenderNeko/ComfyUI_Cutoff) cloned into your `custom_nodes`, you can use the `CUT` keyword to use cutoff functionality

The syntax is
```
a group of animals, [CUT:white cat:white], [CUT:brown dog:brown:0.5:1.0:1.0:_]
```
the parameters in the `CUT` section are `region_text:target_text:weight;strict_mask:start_from_masked:padding_token` of which only the first two are required.
If `strict_mask`, `start_from_masked` or `padding_token` are specified in more than one section, the last one takes effect for the whole prompt

# Nodes

## PCLoraHooksFromSchedule

Creates a ComfyUI `HOOKS` object from a prompt schedule. Can be attached to a CLIP model to perform encoding and LoRA switching

## PCEncodeSchedule

Encodes all prompts in a schedule. Pass in a `CLIP` object with hooks attached for LoRA scheduling, then use the resulting `CONDITIONING` normally

## PromptToSchedule
Parses a schedule from a text prompt. A schedule is essentially an array of `(valid_until, prompt)` pairs that the other nodes can use.

## FilterSchedule
Filters a schedule according to its parameters, removing any *changes* that do not occur within `[start, end)`.

The node also does tag filtering if any tags are specified.

Always returns at least the last prompt in the schedule if everything would otherwise be filtered.

`start=0, end=0` returns the prompt at the start and `start=1.0, end=1.0` returns the prompt at the end.

## PCScheduleSettings
Returns an object representing **default values** for the `SDXL` function and allows configuring `MASK_SIZE` outside the prompt. You need to apply them to a schedule with `PCApplySettings`. Note that for the SDXL settings to apply, you still need to have `SDXL()` in the prompt.

The "steps" parameter currently does nothing; it's for future features.

## PCApplySettings
Applies the give default values from `PCScheduleSettings` to a schedule

## PCPromptFromSchedule

Extracts a text prompt from a schedule; also logs it to the console.
LoRAs are *not* included in the text prompt, though they are logged.

## PCScheduleAddMasks

Attaches custom masks to a `PROMPT_SCHEDULE` that can then be used in a prompt.

## ScheduleToCond (deprecated)
Produces a combined conditioning for the appropriate timesteps. From a schedule. Also applies LoRAs to the CLIP model according to the schedule.

## ScheduleToModel (deprecated)
Produces a model that'll cause the sampler to reapply LoRAs at specific steps according to the schedule.

This depends on a callback handled by a monkeypatch of the ComfyUI sampler function, so it might not work with custom samplers, but it shouldn't interfere with them either.

## PCSplitSampling (deprecated)
Causes sampling to be split into multiple sampler calls instead of relying on timesteps for scheduling. This makes the schedules more accurate, but seems to cause weird behaviour with SDE samplers. (Upstream bug?)


## PromptControlSimple (deprecated)
This node exists purely for convenience. It's a combination of `PromptToSchedule`, `ScheduleToCond`, `ScheduleToModel` and `FilterSchedule` such that it provides as output a model, positive conds and negative conds, both with and without any specified filters applied.

This makes it handy for quick one- or two-pass workflows.

## Older nodes

- `EditableCLIPEncode`: A combination of `PromptToSchedule` and `ScheduleToCond`
- `LoRAScheduler`: A combination of `PromptToSchedule`, `FilterSchedule` and `ScheduleToModel`

# Known issues

- If you use LoRA scheduling in a workflow with `LoRALoader` nodes, you might get inconsistent results. For now, just avoid mixing `ScheduleToModel` or `LoRAScheduler` with `LoRALoader`. See https://github.com/asagi4/comfyui-prompt-control/issues/36
- Workflows using `SamplerCustom` will calculate LoRA schedules based on the number of sigmas given to the sampler instead of the number of steps, since that information isn't available.
- `CUT` does not work with `STYLE:perp`
- `PCSplitSampling` overrides ComfyUI's `BrownianTreeNoiseSampler` noise sampling behaviour so that each split segment doesn't add crazy amounts of noise to the result with some samplers.
- Split sampling may have weird behaviour if your step percentages go below 1 step.
- Interpolation is probably buggy and will likely change behaviour whenever code gets refactored.
- If execution is interrupted and LoRA scheduling is used, your models might be left in an undefined state until you restart ComfyUI
