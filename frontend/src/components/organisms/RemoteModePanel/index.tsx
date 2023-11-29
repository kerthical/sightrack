import { Loader, Stack, Text } from '@mantine/core';
import { useEffect, useRef, useState } from 'react';

export default function RemoteModePanel() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [yaw, setYaw] = useState(0);
  const [pitch, setPitch] = useState(0);

  useEffect(() => {
    const pc = new RTCPeerConnection();

    pc.addEventListener('track', event => {
      const stream = event.streams[0];
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    });

    pc.addEventListener('datachannel', event => {
      console.log("DataChannel '%s' is created!", event.channel.label);
      const dataChannel = event.channel;
      dataChannel.addEventListener('message', (event: MessageEvent<string>) => {
        console.log(
          "Message from DataChannel '%s': '%s'",
          dataChannel.label,
          event.data,
        );
        if (event.type === 'face') {
          const data = JSON.parse(event.data) as {
            yaw: number;
            pitch: number;
          };
          setYaw(data.yaw);
          setPitch(data.pitch);
        }
      });
    });

    navigator.mediaDevices
      .getUserMedia({
        audio: false,
        video: true,
      })
      .then(
        async function (stream) {
          stream.getTracks().forEach(function (track) {
            pc.addTrack(track, stream);
          });
          try {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            const offer_1 = pc.localDescription as RTCSessionDescription;
            const response = await fetch('/remote', {
              body: JSON.stringify({
                sdp: offer_1.sdp,
                type: offer_1.type,
              }),
              headers: {
                'Content-Type': 'application/json',
              },
              method: 'POST',
            });
            const answer = (await response.json()) as RTCSessionDescriptionInit;
            return await pc.setRemoteDescription(answer);
          } catch (e) {
            alert(e);
          }
        },
        function (err) {
          alert('Could not acquire media: ' + err);
        },
      );
  }, []);

  return videoRef.current?.srcObject !== null ? (
    <Stack>
      <video
        autoPlay={true}
        playsInline={true}
        ref={videoRef}
        className="min-w-1/2 w-1/2 max-w-1/2"
      />
      <Text>
        Yaw: {yaw}
        <br />
        Pitch: {pitch}
      </Text>
    </Stack>
  ) : (
    <Loader />
  );
}
