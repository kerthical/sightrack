import { useViewportSize } from '@mantine/hooks';
import Chart from 'react-apexcharts';
import { Frame } from '@/types/frame.ts';

interface FaceChartProps {
  series: Frame[];
}

export default function FaceChart(props: FaceChartProps) {
  const { width } = useViewportSize();
  const yaws = props.series.map(frame => Math.abs(frame.yaw / 180)).slice(-100);
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
        dataLabels: {
          enabled: false,
        },
        stroke: {
          curve: 'smooth',
        },
        title: {
          text: 'Size of turn angles',
          align: 'center',
        },
        markers: {
          size: 0,
        },
        xaxis: {
          labels: {
            show: false,
          },
        },
        yaxis: {
          min: 0,
          max: 1,
          labels: {
            show: true,
            formatter: (val: number) => `${Math.round(val * 180)}°`,
          },
        },
        legend: {
          show: false,
        },
      }}
      series={[
        {
          name: 'turn',
          data: yaws,
        },
      ]}
      type="line"
      width={width / 2}
      height={200}
    />
  );
}
