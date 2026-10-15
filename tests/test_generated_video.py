"""Offline contracts and paid-submission boundaries for generated video assets."""
import base64
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SKILLS=ROOT/"plugins/marketing-creative/skills"


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


C=module("video_provider",SKILLS/"motion-video-producer/scripts/video_provider.py")
VEO=module("veo_video",SKILLS/"marketing-veo-video/scripts/veo_video.py")
OMNI=module("omni_video",SKILLS/"marketing-omni-video/scripts/omni_video.py")
try:
    from PIL import Image
except ImportError:
    Image=None


class FakeClient:
    def __init__(self,results=(),data=b""):
        self.results=list(results)
        self.calls=[]
        self.data=data

    def send(self,method,endpoint,body=None,headers=None,raw=False):
        self.calls.append((method,endpoint,body))
        result=self.results.pop(0)
        if isinstance(result,BaseException):
            raise result
        return result,{}

    def download(self,uri):
        self.calls.append(("DOWNLOAD",uri,None))
        return self.data


class GeneratedVideoTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.config=C.read(SKILLS/"marketing-veo-video/assets/veo.example.json")
        self.path=self.root/"veo.json"
        self.write()

    def write(self):
        C.save(self.path,self.config)

    def prepare(self):
        self.write()
        return VEO.prepare(self.path)

    def image(self):
        if Image is None:
            self.skipTest("Install Pillow to validate input images")
        output=io.BytesIO()
        Image.new("RGB",(16,16),"red").save(output,format="PNG")
        (self.root/"image.png").write_bytes(output.getvalue())
        return "image.png"

    def pending(self):
        return {"name":"models/veo-3.1-generate-preview/operations/job123","done":False}

    def completed(self,uri="files/video123"):
        return {**self.pending(),"done":True,"response":{"generateVideoResponse":{
            "generatedSamples":[{"video":{"uri":uri}}]}}}

    def submit(self,client):
        body,meta=self.prepare()
        state=C.submit(body,meta,self.root/"run",VEO,meta["requestSha256"],"User approved this mocked request",client)
        return state,meta

    def test_veo_dry_run_without_key_or_output(self):
        env={k:v for k,v in os.environ.items() if k!="GEMINI_API_KEY"}
        result=subprocess.run([sys.executable,str(SKILLS/"marketing-veo-video/scripts/veo_video.py"),
            "submit",str(self.path),"--out",str(self.root/"dry"),"--dry-run"],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(json.loads(result.stdout)["approvalRequired"])
        self.assertFalse((self.root/"dry").exists())

    def test_approval_is_required_before_key_lookup_network_or_writes(self):
        body,meta=self.prepare()
        for approval,note in ((None,None),("stale","User approved"),(meta["requestSha256"],None)):
            with self.assertRaisesRegex(ValueError,"explicit user approval"):
                C.submit(body,meta,self.root/"bad",VEO,approval,note)
            self.assertFalse((self.root/"bad").exists())
        self.config.pop("costEstimate")
        body,meta=self.prepare()
        with self.assertRaisesRegex(ValueError,"costEstimate"):
            C.submit(body,meta,self.root/"bad",VEO,meta["requestSha256"],"User approved")

    def test_changed_media_or_prompt_invalidates_approval(self):
        self.config.update(mode="image",image=self.image())
        _,before=self.prepare()
        self.config["prompt"]="A different camera move"
        _,after=self.prepare()
        self.assertNotEqual(before["requestSha256"],after["requestSha256"])
        Image.new("RGB",(16,16),"blue").save(self.root/"image.png")
        _,changed=self.prepare()
        self.assertNotEqual(after["requestSha256"],changed["requestSha256"])

    def test_veo_image_reference_and_interpolation_payloads(self):
        image=self.image()
        for mode,fields in (("image",{"image":image}),("interpolate",{"image":image,"lastFrame":image}),
                            ("reference",{"referenceImages":[image,image,image]})):
            self.config=C.read(SKILLS/"marketing-veo-video/assets/veo.example.json")
            self.config.update(mode=mode,**fields)
            body,meta=self.prepare()
            self.assertEqual(meta["mode"],mode)
            self.assertEqual(body["parameters"]["personGeneration"],"allow_adult")
            if mode=="reference":
                self.assertEqual(len(body["instances"][0]["referenceImages"]),3)
                self.assertEqual(body["instances"][0]["referenceImages"][0]["referenceType"],"asset")
            else:
                self.assertIn("inlineData",body["instances"][0]["image"])

    def test_veo_invalid_combinations_fail_locally(self):
        cases=[{"aspectRatio":"1:1"},{"durationSeconds":5},{"durationSeconds":4,"resolution":"1080p"},
               {"model":"veo-3.1-lite-generate-preview","resolution":"4k"},
               {"mode":"interpolate","lastFrame":"missing.png"},{"generateAudio":False}]
        for updates in cases:
            self.config=C.read(SKILLS/"marketing-veo-video/assets/veo.example.json")
            self.config.update(updates)
            with self.subTest(updates=updates),self.assertRaises(ValueError):
                self.prepare()

    def test_veo_submission_persists_identity_and_refuses_duplicate_run(self):
        client=FakeClient([self.pending()])
        state,meta=self.submit(client)
        self.assertEqual(state["operationName"],self.pending()["name"])
        self.assertEqual(len(client.calls),1)
        self.assertIn(":predictLongRunning",client.calls[0][1])
        body,meta=self.prepare()
        with self.assertRaises(FileExistsError):
            C.submit(body,meta,self.root/"run",VEO,meta["requestSha256"],"User approved",FakeClient())

    def test_unknown_outcome_is_not_resubmitted(self):
        body,meta=self.prepare()
        client=FakeClient([TimeoutError("simulated")])
        with self.assertRaises(TimeoutError):
            C.submit(body,meta,self.root/"run",VEO,meta["requestSha256"],"User approved",client)
        self.assertEqual(C.read(self.root/"run/state.json")["status"],"failed-or-unknown")
        self.assertEqual(len(client.calls),1)

    def test_status_checks_once_and_validates_operation_identity(self):
        self.submit(FakeClient([self.pending()]))
        client=FakeClient([self.pending()])
        _,state=C.status(self.root/"run",VEO,client)
        self.assertEqual(state["status"],"pending")
        self.assertEqual([call[0] for call in client.calls],["GET"])
        changed={**self.pending(),"name":"models/veo-3.1-generate-preview/operations/other"}
        with self.assertRaisesRegex(ValueError,"identity"):
            C.status(self.root/"run",VEO,FakeClient([changed]))

    def test_filtered_result_is_not_success(self):
        update,outputs=VEO.parse_response({**self.pending(),"done":True,"response":{"generateVideoResponse":{"raiMediaFilteredCount":1}}})
        self.assertEqual(update["status"],"filtered-or-empty")
        self.assertEqual(outputs,[])

    def test_veo_extension_uses_provenance_and_total_runtime(self):
        self.submit(FakeClient([self.completed()]))
        self.config.update(mode="extend",sourceRun="run")
        body,meta=self.prepare()
        self.assertEqual(meta["expected"]["durationSeconds"],15)
        self.assertEqual(body["instances"][0]["video"]["uri"],C.API+"/v1beta/files/video123")
        state=C.read(self.root/"run/state.json")
        state["expected"]["durationSeconds"]=142
        C.save(self.root/"run/state.json",state)
        with self.assertRaisesRegex(ValueError,"141"):
            self.prepare()

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"FFmpeg/FFprobe required")
    def test_received_output_survives_probe_failure_and_download_recovers(self):
        video=self.root/"fixture.mp4"
        subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","color=c=red:s=160x90:r=24", "-t","8",
                        "-c:v","libx264","-pix_fmt","yuv420p",str(video)],check=True,capture_output=True)
        raw=video.read_bytes()
        result=self.completed()
        result["response"]["generateVideoResponse"]["generatedSamples"][0]["video"]={"videoBytes":base64.b64encode(raw).decode()}
        self.submit(FakeClient([result]))
        root=self.root/"run"
        self.assertEqual((root/"received-1.mp4").read_bytes(),raw)
        with patch.object(C,"probe",side_effect=ValueError("missing ffprobe")):
            with self.assertRaisesRegex(ValueError,"ffprobe"):
                C.download(root,VEO,FakeClient())
        self.assertEqual((root/"product-hero-1.mp4").read_bytes(),raw)
        assets=C.download(root,VEO,FakeClient())
        self.assertEqual(assets[0]["width"],160)
        self.assertFalse(assets[0]["hasAudio"])
        self.assertIn("no audio stream; review intended sound",assets[0]["reviewIssues"])
        self.assertFalse(assets[0]["reviewed"])

    def test_pending_input_file_prevents_paid_submission(self):
        body,meta=self.prepare()
        meta["references"]=[{"uri":"files/processing"}]
        meta["requestSha256"]=C.sha(C.encoded({"body":body,"metadata":{k:v for k,v in meta.items() if k!="requestSha256"}}))
        client=FakeClient([{"state":"PROCESSING"}])
        with self.assertRaisesRegex(ValueError,"not ACTIVE"):
            C.submit(body,meta,self.root/"run",VEO,meta["requestSha256"],"User approved",client)
        self.assertEqual([call[0] for call in client.calls],["GET"])

    def test_uri_download_recovers_after_probe_status_refresh_and_expiry(self):
        self.submit(FakeClient([self.completed()]))
        raw=b"\x00\x00\x00\x18ftypisom"+b"synthetic"
        details={"width":1280,"height":720,"duration":8,"fps":24,"codec":"h264","hasAudio":True}
        with patch.object(C,"probe",side_effect=ValueError("missing ffprobe")):
            with self.assertRaisesRegex(ValueError,"ffprobe"):
                C.download(self.root/"run",VEO,FakeClient([{"state":"ACTIVE"}],raw))
        C.status(self.root/"run",VEO,FakeClient([self.completed()]))
        self.assertEqual(C.read(self.root/"run/state.json")["outputs"][0]["receivedPath"],"received-1.mp4")
        with patch.object(C,"probe",return_value=details):
            first=C.download(self.root/"run",VEO,FakeClient())
            with patch.dict(os.environ,{},clear=True):
                second=C.download(self.root/"run",VEO)
        self.assertEqual(first[0]["sha256"],second[0]["sha256"])
        self.assertTrue((self.root/"run/received-1.mp4").is_file())

    def test_download_redirect_strips_key_on_google_storage(self):
        import urllib.error
        captured=[]
        class Response(io.BytesIO):
            pass
        class Opener:
            def open(self,request,timeout):
                captured.append(request)
                if len(captured)==1:
                    raise urllib.error.HTTPError(request.full_url,302,"redirect",{"Location":"https://storage.googleapis.com/signed-video"},None)
                return Response(b"video bytes")
        with patch.dict(os.environ,{"GEMINI_API_KEY":"synthetic-key"}):
            client=C.Client()
        client.opener=Opener()
        self.assertEqual(client.download("files/video123"),b"video bytes")
        self.assertIn("X-goog-api-key",dict(captured[0].header_items()))
        self.assertNotIn("X-goog-api-key",dict(captured[1].header_items()))
        with self.assertRaisesRegex(ValueError,"Gemini Files URI"):
            client.download("https://example.com/video.mp4")


class OmniVideoTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.config=C.read(SKILLS/"marketing-omni-video/assets/omni.example.json")
        self.path=self.root/"omni.json"

    def prepare(self):
        C.save(self.path,self.config)
        return OMNI.prepare(self.path)

    def image(self):
        if Image is None:
            self.skipTest("Install Pillow")
        Image.new("RGB",(12,12),"blue").save(self.root/"source.png")
        return {"type":"image","path":"source.png","role":"first_frame"}

    def video(self,role="video_source",seconds=8):
        return {"type":"video","uri":"files/source123","durationSeconds":seconds,"role":role}

    def completed(self):
        return {"id":"v1_mock123","status":"completed","steps":[
            {"type":"model_output","content":[{"type":"video","mime_type":"video/mp4","uri":"files/output123"}]}]}

    def prior(self,store=True):
        self.config["store"]=store
        body,meta=self.prepare()
        C.submit(body,meta,self.root/"prior",OMNI,meta["requestSha256"],"User approved mock",FakeClient([self.completed()]))
        return self.root/"prior"

    def test_omni_text_dry_run_and_real_approval_gate(self):
        body,meta=self.prepare()
        self.assertEqual(body["response_format"]["duration"],"5s")
        self.assertEqual(body["response_format"]["delivery"],"uri")
        self.assertEqual(OMNI.endpoint(meta),"/v1beta/interactions")
        with self.assertRaisesRegex(ValueError,"explicit user approval"):
            C.submit(body,meta,self.root/"unapproved",OMNI)
        env={k:v for k,v in os.environ.items() if k!="GEMINI_API_KEY"}
        result=subprocess.run([sys.executable,str(SKILLS/"marketing-omni-video/scripts/omni_video.py"),"submit",str(self.path),
            "--out",str(self.root/"dry"),"--dry-run"],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((self.root/"dry").exists())

    def test_omni_first_last_loop_and_reference_bindings(self):
        first=self.image()
        for mode,media in (("image",[first]),("interpolate",[first,{**first,"role":"last_frame"}]),("loop",[first]),
                           ("reference",[{**first,"role":"image_reference"},self.video("video_reference",3)])):
            self.config.update(mode=mode,media=media)
            body,meta=self.prepare()
            prompt=body["input"][-1]["text"]
            if mode=="reference":
                self.assertIn("<IMAGE_REF_0>@Image1",prompt)
                self.assertIn("<VIDEO_REF_0>@Video1",prompt)
            else:
                self.assertIn("<FIRST_FRAME>@Image1",prompt)
                if mode in {"loop","interpolate"}:
                    self.assertIn("<LAST_FRAME>@Image1" if mode=="loop" else "<LAST_FRAME>@Image2",prompt)
            self.assertNotIn("generation_config",body)
            self.assertEqual(meta["mode"],mode)

    def test_omni_uploaded_edit_extend_and_upscale(self):
        source=self.video()
        for mode in ("edit","extend","upscale"):
            self.config.update(mode=mode,media=[source],resolution="4k" if mode=="upscale" else "720p")
            if mode=="upscale":
                self.config.pop("durationSeconds",None)
            body,meta=self.prepare()
            self.assertIn("<VIDEO_0>@Video1",body["input"][-1]["text"])
            self.assertEqual(meta["expected"]["durationSeconds"],13 if mode=="extend" else 8 if mode=="upscale" else 5)

    def test_omni_multi_turn_edit_and_extension_use_stored_identity(self):
        self.prior()
        self.config.update(mode="edit",previousRun="prior")
        body,meta=self.prepare()
        self.assertEqual(body["previous_interaction_id"],"v1_mock123")
        self.config.update(mode="extend",durationSeconds=10)
        _,meta=self.prepare()
        self.assertEqual(meta["expected"]["durationSeconds"],15)
        self.config.pop("previousRun")
        self.config.update(previousInteractionId="v1_mock123",sourceDurationSeconds=35)
        with self.assertRaisesRegex(ValueError,"40s"):
            self.prepare()

    def revision_config(self,**changes):
        path=self.root/"revision.json"
        C.save(path,{"schemaVersion":1,"id":"revision","prompt":"Change the light to golden sunset; preserve the subject and camera move.",
                     "costEstimate":self.config["costEstimate"],**changes})
        return path

    def test_continue_inherits_settings_and_only_sends_the_followup(self):
        self.config.update(model="gemini-omni-flash-preview",aspectRatio="9:16",durationSeconds=8,resolution="4k")
        prior=self.prior()
        path=self.revision_config()
        body,meta=OMNI.prepare(path,previous_run=prior)
        self.assertEqual(body["previous_interaction_id"],"v1_mock123")
        self.assertEqual(body["model"],"gemini-omni-flash-preview")
        self.assertEqual(body["response_format"]["aspect_ratio"],"9:16")
        self.assertEqual(body["response_format"]["duration"],"8s")
        self.assertEqual(body["response_format"]["resolution"],"4k")
        self.assertEqual(body["input"],[{"type":"text","text":C.read(path)["prompt"]}])
        self.assertTrue(body["store"])
        self.assertEqual(meta["conversation"]["parentRun"],str(prior.resolve()))

    def test_continue_cli_dry_run_and_history_work_without_key_or_writes(self):
        prior=self.prior()
        path=self.revision_config()
        tool=str(SKILLS/"marketing-omni-video/scripts/omni_video.py")
        env={k:v for k,v in os.environ.items() if k!="GEMINI_API_KEY"}
        before=(prior/"state.json").read_bytes()
        command=[sys.executable,tool,"continue",str(prior),str(path),"--out",str(self.root/"next"),"--dry-run"]
        result=subprocess.run(command,env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)["mode"],"edit")
        self.assertFalse((self.root/"next").exists())
        history=subprocess.run([sys.executable,tool,"history",str(prior)],env=env,capture_output=True,text=True)
        self.assertEqual(history.returncode,0,history.stderr)
        self.assertTrue(json.loads(history.stdout)["canContinue"])
        self.assertEqual((prior/"state.json").read_bytes(),before)

    def test_three_turn_conversation_survives_process_restart_and_can_branch(self):
        prior=self.prior()
        path=self.revision_config()
        for previous,name,identity in ((prior,"second","v1_second"),(self.root/"second","third","v1_third"),(prior,"branch","v1_branch")):
            metadata=OMNI.continue_run(previous,path,self.root/name,dry_run=True)
            result={**self.completed(),"id":identity}
            client=FakeClient([result])
            state=OMNI.continue_run(previous,path,self.root/name,approval=metadata["requestSha256"],note="User approved mock revision",client=client)
            self.assertEqual(client.calls[0][2]["previous_interaction_id"],C.read(previous/"state.json")["interactionId"])
            self.assertEqual(state["interactionId"],identity)
        restarted=module("restarted_omni",SKILLS/"marketing-omni-video/scripts/omni_video.py")
        history=restarted.history(self.root/"third")
        self.assertEqual([t["interactionId"] for t in history["turns"]],["v1_mock123","v1_second","v1_third"])
        self.assertEqual([t["interactionId"] for t in restarted.history(self.root/"branch")["turns"]],["v1_mock123","v1_branch"])
        self.assertEqual(history["currentRun"],str((self.root/"third").resolve()))

    def test_continue_approval_binds_parent_and_edit_request(self):
        prior=self.prior()
        path=self.revision_config()
        client=FakeClient()
        with self.assertRaisesRegex(ValueError,"explicit user approval"):
            OMNI.continue_run(prior,path,self.root/"next",client=client)
        self.assertFalse(client.calls)
        self.assertFalse((self.root/"next").exists())
        metadata=OMNI.continue_run(prior,path,self.root/"next",dry_run=True)
        self.revision_config(prompt="Change only the background to blue")
        with self.assertRaisesRegex(ValueError,"explicit user approval"):
            OMNI.continue_run(prior,path,self.root/"next",approval=metadata["requestSha256"],note="Prior approval",client=client)
        self.assertFalse(client.calls)
        path=self.revision_config()
        parent=C.read(prior/"state.json")
        C.save(prior/"state.json",{**parent,"interactionId":"v1_different"})
        with self.assertRaisesRegex(ValueError,"explicit user approval"):
            OMNI.continue_run(prior,path,self.root/"next",approval=metadata["requestSha256"],note="Prior approval",client=client)
        self.assertFalse(client.calls)

    def test_continue_rejects_unusable_or_conflicting_context(self):
        prior=self.prior()
        state=C.read(prior/"state.json")
        path=self.revision_config()
        for changes in ({"status":"in_progress"},{"stored":False},{"interactionId":None}):
            C.save(prior/"state.json",{**state,**changes})
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                OMNI.continue_run(prior,path,self.root/"next",dry_run=True)
        C.save(prior/"state.json",state)
        for changes in ({"previousInteractionId":"v1_other"},{"media":[self.video()]},{"mode":"text"}):
            self.revision_config(**changes)
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                OMNI.continue_run(prior,path,self.root/"next",dry_run=True)
        self.assertFalse((self.root/"next").exists())

    def test_unknown_revision_preserves_parent_and_does_not_become_context(self):
        prior=self.prior()
        original=(prior/"state.json").read_bytes()
        path=self.revision_config()
        meta=OMNI.continue_run(prior,path,self.root/"failed",dry_run=True)
        with self.assertRaises(TimeoutError):
            OMNI.continue_run(prior,path,self.root/"failed",approval=meta["requestSha256"],note="Approved mock",client=FakeClient([TimeoutError()]))
        self.assertEqual((prior/"state.json").read_bytes(),original)
        history=OMNI.history(self.root/"failed")
        self.assertEqual(len(history["turns"]),2)
        self.assertFalse(history["canContinue"])
        with self.assertRaisesRegex(ValueError,"not completed"):
            OMNI.continue_run(self.root/"failed",path,self.root/"retry",dry_run=True)

    def test_history_rejects_replaced_parent_and_cycles(self):
        prior=self.prior()
        path=self.revision_config()
        meta=OMNI.continue_run(prior,path,self.root/"second",dry_run=True)
        OMNI.continue_run(prior,path,self.root/"second",approval=meta["requestSha256"],note="Approved mock",client=FakeClient([{**self.completed(),"id":"v1_second"}]))
        parent=C.read(prior/"state.json")
        C.save(prior/"state.json",{**parent,"interactionId":"v1_changed"})
        with self.assertRaisesRegex(ValueError,"parent identity changed"):
            OMNI.history(self.root/"second")
        parent["conversation"]={"parentRun":str(prior),"parentInteractionId":"v1_mock123","parentRequestSha256":parent["requestSha256"]}
        C.save(prior/"state.json",parent)
        with self.assertRaisesRegex(ValueError,"cycle"):
            OMNI.history(prior)

    def test_continue_uses_measured_duration_and_rejects_unbound_asset_metadata(self):
        prior=self.prior()
        state=C.read(prior/"state.json")
        asset={"duration":8,"generation":{"requestSha256":state["requestSha256"]}}
        C.save(prior/"assets.json",{"assets":[asset]})
        path=self.revision_config()
        body,_=OMNI.prepare(path,previous_run=prior)
        self.assertEqual(body["response_format"]["duration"],"8s")
        asset["duration"]=15
        C.save(prior/"assets.json",{"assets":[asset]})
        with self.assertRaisesRegex(ValueError,"explicitly"):
            OMNI.prepare(path,previous_run=prior)
        self.revision_config(durationSeconds=10)
        body,_=OMNI.prepare(path,previous_run=prior)
        self.assertEqual(body["response_format"]["duration"],"10s")
        asset["generation"]["requestSha256"]="unrelated-request"
        C.save(prior/"assets.json",{"assets":[asset]})
        with self.assertRaisesRegex(ValueError,"do not match"):
            OMNI.prepare(path,previous_run=prior)

    def test_history_marks_external_or_legacy_parent_without_inventing_turns(self):
        self.config.update(mode="edit",previousInteractionId="v1_external")
        prior=self.prior()
        history=OMNI.history(prior)
        self.assertEqual(history["externalParentInteractionId"],"v1_external")
        self.assertEqual(len(history["turns"]),1)
        state=C.read(prior/"state.json")
        state.pop("conversation")
        state["references"]=[{"kind":"provenance","previousInteractionId":"v1_legacy"}]
        C.save(prior/"state.json",state)
        self.assertEqual(OMNI.history(prior)["externalParentInteractionId"],"v1_legacy")

    def test_store_false_prevents_chaining_and_retrieval(self):
        self.prior(store=False)
        self.config.update(mode="edit",previousRun="prior")
        with self.assertRaisesRegex(ValueError,"store=false"):
            self.prepare()
        with self.assertRaisesRegex(ValueError,"store=false"):
            C.status(self.root/"prior",OMNI,FakeClient())

    def test_unsupported_controls_and_duration_limits_fail_locally(self):
        original=dict(self.config)
        for updates in ({"negativePrompt":"No cats"},{"temperature":.1},{"durationSeconds":11},{"aspectRatio":"4:5"},
                        {"mode":"edit","media":[self.video(seconds=11)]},
                        {"mode":"reference","media":[self.video("video_reference",4)]},
                        {"mode":"reference","media":[self.video("video_reference",3)]*4},
                        {"background":True,"store":False},{"media":[{"type":"audio","role":"image_reference","uri":"files/audio"}]}):
            self.config={**original,**updates}
            with self.subTest(updates=updates),self.assertRaises(ValueError):
                self.prepare()

    def test_raw_steps_ignore_source_and_thought_video_echoes(self):
        result=self.completed()
        result["steps"].insert(0,{"type":"user_input","content":[{"type":"video","uri":"files/source-secret"}]})
        result["steps"].insert(1,{"type":"thought","content":[{"type":"video","uri":"files/thought-secret"}]})
        update,videos=OMNI.parse_response(result)
        self.assertEqual(len(videos),1)
        self.assertEqual(videos[0]["uri"],"files/output123")
        self.assertNotIn("steps",update)

    def test_creation_uri_is_preserved_when_get_returns_inline(self):
        self.prior()
        result=self.completed()
        raw=b"\x00\x00\x00\x18ftypisom"+b"synthetic"
        result["steps"][0]["content"][0]={"type":"video","mime_type":"video/mp4","data":base64.b64encode(raw).decode()}
        _,state=C.status(self.root/"prior",OMNI,FakeClient([result]))
        self.assertEqual(state["outputs"][0]["uri"],"files/output123")
        self.assertEqual((self.root/"prior/received-1.mp4").read_bytes(),raw)

    def test_stream_assembles_video_and_checkpoints_without_input_or_thoughts(self):
        events=[{"event_type":"interaction.created","interaction":{"id":"v1_stream","status":"in_progress"}},
                {"event_type":"step.start","index":0,"step":{"type":"thought"}},
                {"event_type":"step.delta","index":0,"delta":{"type":"video","uri":"files/private-thought"}},
                {"event_type":"step.start","index":1,"step":{"type":"model_output"}},
                {"event_type":"step.delta","index":1,"delta":{"type":"video","mime_type":"video/mp4","uri":"files/generated"}},
                {"event_type":"step.stop","index":1},
                {"event_type":"interaction.completed","interaction":{"id":"v1_stream","status":"completed"}}]
        stream=io.BytesIO(b"".join(b"data: "+json.dumps(e).encode()+b"\n\n" for e in events))
        progress=[]
        result=C.read_stream(stream,progress.append)
        self.assertEqual(progress[0]["id"],"v1_stream")
        self.assertEqual(OMNI.parse_response(result)[1][0]["uri"],"files/generated")
        self.assertNotIn("private-thought",json.dumps(result))

    def test_interrupted_stream_keeps_interaction_identity(self):
        self.config["stream"]=True
        body,meta=self.prepare()
        class Interrupted(FakeClient):
            def send(self,*args,**kwargs):
                self.on_progress({"id":"v1_interrupted","status":"in_progress"})
                raise TimeoutError("simulated")
        with self.assertRaises(TimeoutError):
            C.submit(body,meta,self.root/"stream",OMNI,meta["requestSha256"],"User approved mock",Interrupted())
        state=C.read(self.root/"stream/state.json")
        self.assertEqual(state["interactionId"],"v1_interrupted")
        self.assertEqual(state["status"],"failed-or-unknown")

    def test_background_cancellation_and_task_override(self):
        self.config.update(background=True,task="text_to_video")
        body,meta=self.prepare()
        self.assertEqual(body["generation_config"]["video_config"]["task"],"text_to_video")
        result={"id":"v1_running","status":"in_progress"}
        C.submit(body,meta,self.root/"background",OMNI,meta["requestSha256"],"User approved mock",FakeClient([result]))
        client=FakeClient([{"id":"v1_running","status":"cancelled"}])
        state=OMNI.cancel(self.root/"background",client)
        self.assertEqual(state["status"],"cancelled")
        self.assertEqual(client.calls[0][1],"/v1beta/interactions/v1_running/cancel")

    def test_upload_timeout_retains_lookup_metadata(self):
        self.image()
        with self.assertRaises(TimeoutError):
            C.upload(self.root/"source.png",self.root/"upload",FakeClient([TimeoutError("simulated")]))
        state=C.read(self.root/"upload/state.json")
        self.assertEqual(state["status"],"failed-or-unknown")
        self.assertIn("displayName",state)
        self.assertNotIn("data",state)


if __name__=="__main__":
    unittest.main()
