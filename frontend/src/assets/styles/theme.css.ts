import { style } from '@vanilla-extract/css';

export const active = style({
  transform: 'scale(1)',
  ':active': {
    transform: 'scale(0.95)',
  },
});
