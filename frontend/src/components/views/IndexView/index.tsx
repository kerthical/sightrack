import { Box, Loader } from '@mantine/core';
import { useEffect, useRef } from 'react';
import AppLayout from '@/components/layouts/AppLayout';

export default function IndexView() {
  const videoRef = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    const pc = new RTCPeerConnection();

    pc.addEventListener('track', event => {
      const stream = event.streams[0];
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    });

    navigator.mediaDevices
      .getUserMedia({
        audio: false,
        video: {
          width: 1280,
          height: 720,
        },
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
            const response = await fetch('/offer', {
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

  return (
    <AppLayout>
      <Box
        w="100dvw"
        h="100dvh"
        maw="100dvw"
        mah="100dvh"
        className="flex flex-col items-center justify-center"
      >
        {videoRef.current?.srcObject !== null ? (
          <video
            autoPlay={true}
            playsInline={true}
            ref={videoRef}
            className="w-[80%]"
          />
        ) : (
          <Loader />
        )}
      </Box>
    </AppLayout>
  );
}
