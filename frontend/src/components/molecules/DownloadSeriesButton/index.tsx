import { Button } from '@mantine/core';
import { Frame } from '@/types/frame.ts';

interface DownloadSeriesButtonProps {
  series: Frame[];
}

export default function DownloadSeriesButton(props: DownloadSeriesButtonProps) {
  return (
    <Button
      onClick={() => {
        const csvContent = props.series
          .map(frame => {
            const row = [
              frame.frame,
              frame.detected,
              frame.box?.score,
              frame.rotation?.yaw,
              frame.rotation?.pitch,
              frame.rotation?.roll,
            ];
            return row.join(',');
          })
          .join('\n');
        const headers = [
          'frame_count',
          'detected',
          'score',
          'yaw',
          'pitch',
          'roll',
        ];
        const headerRow = headers.join(',');
        const csv = headerRow + '\n' + csvContent;
        const blob = new Blob([csv], {
          type: 'text/csv;charset=utf-8;',
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', 'data.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }}
    >
      Download CSV
    </Button>
  );
}
