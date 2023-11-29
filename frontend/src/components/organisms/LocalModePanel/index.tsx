import { Loader } from '@mantine/core';
import { useEffect, useRef } from 'react';

export default function LocalModePanel() {
  const videoRef = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    const pc = new RTCPeerConnection();

    pc.addEventListener('track', event => {
      const stream = event.streams[0];
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    });

    (async () => {
      try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        const offer_1 = pc.localDescription as RTCSessionDescription;
        const response = await fetch('/local', {
          body: JSON.stringify({
            sdp: offer_1.sdp,
            type: offer_1.type,
            file: 'input.mp4',
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
    })().catch(alert);
  }, []);
  return videoRef.current?.srcObject !== null ? (
    <video
      autoPlay={true}
      playsInline={true}
      ref={videoRef}
      className="min-w-1/2 w-1/2 max-w-1/2"
    />
  ) : (
    <Loader />
  );
}
