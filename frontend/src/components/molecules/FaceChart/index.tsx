import { useViewportSize } from '@mantine/hooks';
import Chart from 'react-apexcharts';
import { Frame } from '@/types/frame.ts';

interface FaceChartProps {
  series: Frame[];
}

export default function FaceChart(props: FaceChartProps) {
  const { width } = useViewportSize();
  const detectedYaws = props.series
    .filter(frame => frame.detected)
    .map(frame => frame.yaw / 90);
  const sortedYaws = [...detectedYaws].sort((a, b) => a - b);
  const middle = Math.floor(sortedYaws.length / 2);
  let median: number;
  if (sortedYaws.length % 2 === 0) {
    median = (sortedYaws[middle - 1] + sortedYaws[middle]) / 2;
  } else {
    median = sortedYaws[middle];
  }

  const yaws = props.series.map(frame =>
    frame.detected ? frame.yaw / 90 - median : null,
  );

  return (
    <Chart
      options={{
        chart: {
          height: 350,
          type: 'line',
          zoom: {
            enabled: false,
          },
          toolbar: {
            show: false,
          },
          animations: {
            enabled: true,
            easing: 'easeinout',
            dynamicAnimation: {
              speed: 1000,
            },
          },
        },
        annotations: {
          yaxis: [
            {
              y: 0.3333,
              fillColor: '#00E396',
              borderColor: '#00E396',
              opacity: 0.3,
            },
            {
              y: -0.3333,
              fillColor: '#FEB019',
              borderColor: '#FEB019',
              opacity: 0.3,
            },
          ],
        },
        stroke: {
          curve: 'smooth',
        },
        grid: {
          show: false,
        },
        tooltip: {
          enabled: false,
        },
        legend: {
          show: false,
        },
        markers: {
          size: 0,
          fillOpacity: 0,
          strokeOpacity: 0,
        },
        xaxis: {
          type: 'numeric',
          range: 200,
          labels: {
            show: false,
          },
          axisTicks: {
            show: false,
          },
        },
        yaxis: {
          min: -1,
          max: 1,
          axisTicks: {
            show: false,
          },
          tickAmount: 5,
          labels: {
            formatter: (val: number) => `${Math.round(val * 90)}°`,
          },
        },
      }}
      series={[
        {
          name: 'yaw',
          data: yaws,
        },
      ]}
      type="line"
      width={width / 2}
      height={200}
    />
  );
}
