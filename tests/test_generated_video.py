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


if __name__=="__main__":
    unittest.main()
