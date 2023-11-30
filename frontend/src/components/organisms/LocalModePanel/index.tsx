import { Button, FileButton } from '@mantine/core';
import { useListState } from '@mantine/hooks';
import { useEffect, useRef, useState } from 'react';
import DownloadSeriesButton from '@/components/molecules/DownloadSeriesButton';
import FaceChart from '@/components/molecules/FaceChart';
import { Frame } from '@/types/frame.ts';

export default function LocalModePanel() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [currentStatus, setCurrentStatus] = useState<
    'idle' | 'loading' | 'done'
  >('idle');
  const [srcObject, setSrcObject] = useState<MediaStream | null>(null);
  const [series, handlers] = useListState<Frame>();

  useEffect(() => {
    if (srcObject) {
      videoRef.current!.srcObject = srcObject;
    }
  }, [currentStatus, srcObject]);

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
    <>
      <FileButton
        onChange={file => {
          if (!file) {
            return;
          }
          (async () => {
            setCurrentStatus('loading');
            const pc = new RTCPeerConnection();

            pc.addEventListener('track', event => {
              setSrcObject(event.streams[0]);
            });

            pc.addEventListener('datachannel', event => {
              const dataChannel = event.channel;
              dataChannel.addEventListener(
                'message',
                (event: MessageEvent<string>) => {
                  const data = JSON.parse(event.data) as Frame;
                  handlers.append(data);
                },
              );
            });
            pc.createDataChannel('data');

            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            if (!ctx) {
              return;
            }
            const stream = canvas.captureStream();
            const track = stream.getTracks()[0];
            pc.addTrack(track, stream);

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
                pc.addEventListener(
                  'icegatheringstatechange',
                  checkGatheringState,
                );
              }
            });
            const offer = pc.localDescription as RTCSessionDescription;
            const formData = new FormData();
            formData.append('file', file);
            formData.append(
              'data',
              JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
              }),
            );
            const response = await fetch('/local', {
              body: formData,
              method: 'POST',
            });
            const answer = (await response.json()) as RTCSessionDescriptionInit;
            await pc.setRemoteDescription(answer);
            setCurrentStatus('done');
          })().catch(console.error);
        }}
        accept="video/*,image/*"
      >
        {props => (
          <Button {...props} loading={currentStatus === 'loading'}>
            Upload Video/Image File
          </Button>
        )}
      </FileButton>
    </>
  );
}
