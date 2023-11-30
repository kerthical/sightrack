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

  const yaws = props.series.map((frame, index) => ({
    x: index,
    y: frame.detected ? frame.yaw / 90 - median : null,
    fillColor:
      frame.yaw > 40 ? '#00E396' : frame.yaw < -40 ? '#FEB019' : '#008FFB',
  }));

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
              y: 0.5,
              borderColor: '#00E396',
              fillColor: '#00E396',
              label: {
                borderColor: '#00E396',
                style: {
                  color: '#fff',
                  background: '#00E396',
                },
                text: 'yaw over 40°',
              },
            },
            {
              y: -0.5,
              borderColor: '#FEB019',
              fillColor: '#FEB019',
              label: {
                borderColor: '#FEB019',
                style: {
                  color: '#fff',
                  background: '#FEB019',
                },
                text: 'yaw under -40°',
              },
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
        xaxis: {
          type: 'numeric',
          range: 1000,
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
