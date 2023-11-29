import { Loader, Text } from '@mantine/core';
import { useEffect, useRef, useState } from 'react';

export default function RemoteModePanel() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [detected, setDetected] = useState(false);
  const [yaw, setYaw] = useState(0);
  const [pitch, setPitch] = useState(0);
  const [roll, setRoll] = useState(0);

  useEffect(() => {
    const pc = new RTCPeerConnection();

    pc.addEventListener('track', event => {
      const stream = event.streams[0];
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    });

    pc.addEventListener('datachannel', event => {
      const dataChannel = event.channel;
      dataChannel.addEventListener('message', (event: MessageEvent<string>) => {
        const data = JSON.parse(event.data) as {
          detected: boolean;
          yaw: number;
          pitch: number;
          roll: number;
        };
        setDetected(data.detected);
        setYaw(data.yaw);
        setRoll(data.pitch);
        setPitch(data.roll);
      });
    });

    navigator.mediaDevices
      .getUserMedia({
        audio: false,
        video: true,
      })
      .then(async (stream: MediaStream) => {
        stream.getTracks().forEach(function (track) {
          pc.addTrack(track, stream);
        });
        await pc.setLocalDescription(await pc.createOffer());
        const offer = pc.localDescription as RTCSessionDescription;
        const response = await fetch('/remote', {
          body: JSON.stringify({
            sdp: offer.sdp,
            type: offer.type,
          }),
          headers: {
            'Content-Type': 'application/json',
          },
          method: 'POST',
        });
        const answer = (await response.json()) as RTCSessionDescriptionInit;
        await pc.setRemoteDescription(answer);
      })
      .catch(console.error);

    pc.createDataChannel('data');

    return () => {
      pc.close();
    };
  }, []);

  return videoRef.current?.srcObject !== null ? (
    <>
      <video
        autoPlay={true}
        playsInline={true}
        ref={videoRef}
        className="min-w-1/2 w-1/2 max-w-1/2"
      />
      <Text>
        Detected: {detected ? 'Yes' : 'No'}
        <br />
        Yaw: {yaw}
        <br />
        Pitch: {roll}
        <br />
        Roll: {pitch}
      </Text>
    </>
  ) : (
    <Loader />
  );
}
