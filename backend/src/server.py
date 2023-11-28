import asyncio
import json
import sys
import time

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay, MediaPlayer
from aiortc import MediaStreamTrack
from av import VideoFrame
from processor import process_frame


class VideoStreamTransformTrack(MediaStreamTrack):
    def __init__(self, track):
        super().__init__()
        self.kind = "video"
        self.track = track
        self.last_img = None
        self.start_time = None

    async def recv(self):
        frame = await self.track.recv()
        image = frame.to_ndarray(format="bgr24")

        if self.start_time is None:
            self.start_time = time.time()
        if (
            time.time() - self.start_time - frame.pts * frame.time_base * 1.0 >= 0.2
            and self.last_img is not None
        ):
            frame = self.last_img
            return frame

        try:
            image = process_frame(image, frame.pts)
        except Exception as e:
            print(e)
            sys.exit(1)
            pass

        new_frame = VideoFrame.from_ndarray(image, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base

        self.last_img = new_frame

        return new_frame


pcs = set()
relay = MediaRelay()


async def handle_shutdown(_):
    await asyncio.gather(*[pc.close() for pc in pcs])
    pcs.clear()



async def handle_remote(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("track")
    def on_track(track):
        pc.addTrack(VideoStreamTransformTrack(relay.subscribe(track)))

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


async def handle_local(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState == "connected":
            pc.addTrack(
                VideoStreamTransformTrack(
                    relay.subscribe(MediaPlayer(params["file"]).video)
                )
            )

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


if __name__ == "__main__":
    app = web.Application()
    app.on_shutdown.append(handle_shutdown)
    app.router.add_post("/remote", handle_remote)
    app.router.add_post("/local", handle_local)
    app.router.add_static("/", "../frontend/dist", show_index=True)
    web.run_app(app, host="127.0.0.1", port=8080)
