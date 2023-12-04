export type Frame = {
  detected: boolean;
  frame: number;
  result: {
    bbox: number[];
    score: number;
    yaw: number;
    pitch: number;
    roll: number;
  };
};
