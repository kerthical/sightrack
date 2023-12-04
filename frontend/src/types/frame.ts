export type Frame = {
  detected: boolean;
  frame: number;
  box?: {
    bbox: number[];
    score: number;
  };
  rotation?: {
    yaw: number;
    pitch: number;
    roll: number;
  };
};
