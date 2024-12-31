# ComfyUI Automatic Prompt
Clip text encode node with some features from [Automatic1111](https://github.com/AUTOMATIC1111/stable-diffusion-webui) like [LoRA loading](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/features#lora) and [Prompt editing](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/features#prompt-editing). Also this repo is an opinionated fork of [comfyui-prompt-control](https://github.com/asagi4/comfyui-prompt-control), please refer to it for better optimization and customization

## Usage
Just put `Automatic Prompt` node in place of regular clip text encode:

![automatic-prompt-simple-example](/workflows/automatic-prompt-simple-example.png)

To quickly add LoRA's to your prompt you may want to use [pythongosssss](https://github.com/pythongosssss/ComfyUI-Custom-Scripts) autocomplete feature(check LoRA in settings)

## Features

See comfyui-prompt-control [features](https://github.com/asagi4/comfyui-prompt-control?tab=readme-ov-file#features)

## TODO

1. Modal window with LoRA previews to insert LoRA into prompt with its trigger words
2. Support `[:cat:0.5]` syntax
3. Support [sd-webui-loractl](https://github.com/cheald/sd-webui-loractl) syntax
4. XYZ plots???