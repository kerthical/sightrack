import { Loader, Text } from '@mantine/core';
import { useEffect, useRef, useState } from 'react';

export default function RemoteModePanel() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [currentStatus, setCurrentStatus] = useState<'loading' | 'done'>(
    'loading',
  );
  const [srcObject, setSrcObject] = useState<MediaStream | null>(null);
  const [detected, setDetected] = useState(false);
  const [yaw, setYaw] = useState(0);
  const [pitch, setPitch] = useState(0);
  const [roll, setRoll] = useState(0);

  useEffect(() => {
    if (srcObject) {
      videoRef.current!.srcObject = srcObject;
    }
  }, [currentStatus, srcObject]);

  useEffect(() => {
    const pc = new RTCPeerConnection();

    pc.addEventListener('track', event => {
      setSrcObject(event.streams[0]);
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
        setPitch(data.pitch);
        setRoll(data.roll);
      });
    });
    pc.createDataChannel('data');

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
        await new Promise(resolve => {
          if (pc.iceGatheringState === 'complete') {
            resolve(null);
          } else {
            const checkGatheringState = () => {
              if (pc.iceGatheringState === 'complete') {
                pc.removeEventListener(
                  'icegatheringstatechange',
                  checkGatheringState,
                );
                resolve(null);
              }
            };
            pc.addEventListener('icegatheringstatechange', checkGatheringState);
          }
        });
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
        setCurrentStatus('done');
      })
      .catch(console.error);

    return () => {
      pc.close();
    };
  }, []);

  return currentStatus === 'done' ? (
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
        Pitch: {pitch}
        <br />
        Roll: {roll}
      </Text>
    </>
  ) : (
    <Loader />
  );
}
