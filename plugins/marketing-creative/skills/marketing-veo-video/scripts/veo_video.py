#!/usr/bin/env python3
"""Prepare and explicitly approve Veo marketing video generation (Python 3.10+)."""
from pathlib import Path
import re
import runpy
import sys

sys.dont_write_bytecode=True
V=runpy.run_path(str(Path(__file__).resolve().parents[2]/"motion-video-producer/scripts/video_provider.py"))
require,read,media=V["require"],V["read"],V["media"]
PROVIDER="veo"
DEFAULT_MODEL="veo-3.1-generate-preview"
MODELS={DEFAULT_MODEL,"veo-3.1-fast-generate-preview","veo-3.1-lite-generate-preview"}


def inline_image(base,value,references):
    image=media(base,value,"image",references)
    require("data" in image,"Veo image inputs use local files; download supplied references first")
    return {"inlineData":{"mimeType":image["mimeType"],"data":image["data"]}}


def prepare(path):
    path=Path(path).resolve()
    config=read(path)
    require(config.get("schemaVersion")==1,"Unsupported Veo config version")
    allowed={"schemaVersion","id","model","mode","prompt","image","lastFrame","referenceImages",
             "sourceRun","aspectRatio","durationSeconds","resolution","personGeneration","seed","negativePrompt","costEstimate"}
    require(set(config)<=allowed,"Unknown Veo config fields; do not silently ignore provider settings")
    model=config.get("model",DEFAULT_MODEL)
    require(model in MODELS,"Use a documented Veo 3.1 model ID")
    mode=config.get("mode","text")
    require(mode in {"text","image","interpolate","reference","extend"},"Unsupported Veo mode")
    prompt=config.get("prompt","")
    require(isinstance(prompt,str) and (mode!="text" or prompt.strip()),"Text generation needs a prompt")
    ratio=config.get("aspectRatio","16:9")
    duration=config.get("durationSeconds",8)
    resolution=config.get("resolution","720p")
    require(ratio in {"16:9","9:16"},"Veo native ratios are 16:9 and 9:16; recompose square/feed in the producer")
    require(type(duration) is int and duration in {4,6,8},"Veo durationSeconds must be 4, 6 or 8")
    require(resolution in {"720p","1080p","4k"},"Unsupported Veo resolution")
    require(not (model.endswith("lite-generate-preview") and (resolution=="4k" or mode in {"extend","reference"})),
            "Veo Lite does not support 4k, extension or reference-image generation")
    require(duration==8 or (resolution=="720p" and mode not in {"reference","extend"}),"This Veo mode/resolution requires durationSeconds=8")
    expected_duration=duration
    references=[]
    instance={"prompt":prompt}
    require(("image" in config)==(mode in {"image","interpolate"}),"Supply image only for image/interpolate mode")
    require(("lastFrame" in config)==(mode=="interpolate"),"Interpolation needs image and lastFrame")
    require(("sourceRun" in config)==(mode=="extend"),"Extension requires a previous Veo sourceRun")
    require(("referenceImages" in config)==(mode=="reference"),"Supply referenceImages only for reference mode")
    if "image" in config:
        instance["image"]=inline_image(path.parent,config["image"],references)
    if "lastFrame" in config:
        instance["lastFrame"]=inline_image(path.parent,config["lastFrame"],references)
    if mode=="reference":
        images=config["referenceImages"]
        require(isinstance(images,list) and 1<=len(images)<=3,"Use one to three Veo asset references")
        instance["referenceImages"]=[{"image":inline_image(path.parent,value,references),"referenceType":"asset"} for value in images]
    if mode=="extend":
        require(resolution=="720p","Veo extension supports only 720p")
        source=(path.parent/config["sourceRun"]).resolve()
        _,state=V["read_run"](source,PROVIDER)
        require(state.get("outputs"),"Previous Veo run has no generated video yet")
        source_duration=state["expected"]["durationSeconds"]
        source_ratio=state["expected"]["aspectRatio"]
        source_resolution=state["expected"]["resolution"]
        if (source/"assets.json").exists():
            asset=read(source/"assets.json")["assets"][0]
            source_duration=asset["duration"]
            require(min(asset["width"],asset["height"])==720,"Measured extension source must be 720p")
        require(source_duration<=141 and source_resolution=="720p" and source_ratio==ratio,
                "Extension source must be Veo-generated, <=141 seconds, 720p and the same ratio")
        video=state["outputs"][0]
        if video.get("uri"):
            name=V["file_name"](video["uri"])
            instance["video"]={"uri":V["API"]+"/v1beta/"+name,"mimeType":"video/mp4"}
            references.append({"kind":"video","uri":instance["video"]["uri"]})
        else:
            received=source/video["receivedPath"]
            require(not received.is_symlink() and received.parent==source and V["sha"](received.read_bytes())==video["sha256"],"Previous Veo output changed")
            part=media(source,video["receivedPath"],"video",references)
            instance["video"]={"inlineData":{"mimeType":"video/mp4","data":part["data"]}}
        references.append({"kind":"provenance","sourceRunSha256":V["sha"]((source/"state.json").read_bytes())})
        expected_duration=source_duration+7
    person=config.get("personGeneration","allow_adult" if mode in {"image","interpolate","reference"} else "allow_all")
    require(person in {"allow_all","allow_adult"},"Unsupported personGeneration")
    require(mode not in {"image","interpolate","reference"} or person=="allow_adult","Image-driven Veo generation uses allow_adult")
    parameters={"aspectRatio":ratio,"durationSeconds":duration,"resolution":resolution,"personGeneration":person,"numberOfVideos":1}
    if "seed" in config:
        require(type(config["seed"]) is int and 0<=config["seed"]<=4294967295,"Seed must be a uint32")
        parameters["seed"]=config["seed"]
    if "negativePrompt" in config:
        require(isinstance(config["negativePrompt"],str),"negativePrompt must be text")
        parameters["negativePrompt"]=config["negativePrompt"]
    return V["prepared"](path,PROVIDER,model,mode,{"instances":[instance],"parameters":parameters},references,
                         {"aspectRatio":ratio,"durationSeconds":expected_duration,"resolution":resolution,"fps":24,"nativeAudio":True})


def endpoint(metadata):
    return f"/v1beta/models/{metadata['model']}:predictLongRunning"


def status_endpoint(state):
    name=state.get("operationName","")
    require(not name or re.fullmatch(r"models/veo-[A-Za-z0-9._-]+/operations/[A-Za-z0-9_-]+",name),"Invalid Veo operation name")
    return "/v1beta/"+name if name else None


def parse_response(result):
    name=result.get("name","")
    status_endpoint({"operationName":name})
    update={"status":"pending"}
    if name:
        update["operationName"]=name
    if result.get("error"):
        return {**update,"status":"failed","errorCode":result["error"].get("code")},[]
    if not result.get("done"):
        return update,[]
    response=result.get("response",{}).get("generateVideoResponse",result.get("response",{}))
    videos=response.get("generatedSamples") or response.get("generatedVideos") or response.get("generated_videos") or []
    outputs=[]
    for value in videos:
        video=value.get("video",{})
        if video.get("uri"):
            V["file_name"](video["uri"])
            outputs.append({"uri":video["uri"],"mimeType":"video/mp4"})
        elif video.get("videoBytes") or video.get("video_bytes"):
            outputs.append({"data":video.get("videoBytes",video.get("video_bytes")),"mimeType":"video/mp4"})
    return {**update,"status":"completed" if outputs else "filtered-or-empty",
            "filteredCount":response.get("raiMediaFilteredCount",0)},outputs


if __name__=="__main__":
    V["main"](sys.modules[__name__])
