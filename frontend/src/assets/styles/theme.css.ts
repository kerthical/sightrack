import { style } from '@vanilla-extract/css';

export const active = style({
  transform: 'scale(1)',
  transition: 'transform 100ms ease',
  ':active': {
    transform: 'scale(0.95)',
  },
});
