export type Frame = {
  detected: boolean;
  yaw: number;
  pitch: number;
  roll: number;
  gaze_x: number;
  gaze_y: number;
  frame_count: number;
  box?: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
  score?: number;
};
