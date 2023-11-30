import { Loader } from '@mantine/core';
import { useListState } from '@mantine/hooks';
import { useEffect, useRef, useState } from 'react';
import DownloadSeriesButton from '@/components/molecules/DownloadSeriesButton';
import FaceChart from '@/components/molecules/FaceChart';
import { Frame } from '@/types/frame.ts';

export default function RemoteModePanel() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [currentStatus, setCurrentStatus] = useState<'loading' | 'done'>(
    'loading',
  );
  const [srcObject, setSrcObject] = useState<MediaStream | null>(null);
  const [series, handlers] = useListState<Frame>();

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
        handlers.append(JSON.parse(event.data) as Frame);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return currentStatus === 'done' ? (
    <>
      <video
        autoPlay={true}
        playsInline={true}
        controls={true}
        ref={videoRef}
        className="min-w-1/3 w-1/3 max-w-1/3"
      />
      <FaceChart series={series} />
      <DownloadSeriesButton series={series} />
    </>
  ) : (
    <Loader />
  );
}
