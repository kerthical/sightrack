import asyncio
import json

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay, MediaPlayer

from processor import VideoProcessor

pcs = set()
relay = MediaRelay()


async def handle_shutdown(_):
    await asyncio.gather(*[pc.close() for pc in pcs])
    pcs.clear()


async def handle_index(_):
    return web.HTTPFound("/index.html")


async def handle_offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("track")
    def on_track(track):
        pc.addTrack(VideoProcessor(relay.subscribe(track)))

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


async def handle_temp(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("track")
    def on_track(_):
        pc.addTrack(VideoProcessor(MediaPlayer("temp.mp4").video))

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
    app.router.add_get("/", handle_index)
    app.router.add_post("/offer", handle_offer)
    app.router.add_post("/temp", handle_temp)
    app.router.add_static("/", "../frontend/dist")
    web.run_app(app, host="127.0.0.1", port=8080)
