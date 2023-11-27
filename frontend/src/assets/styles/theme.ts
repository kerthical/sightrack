import { createTheme } from '@mantine/core';
import { themeToVars } from '@mantine/vanilla-extract';
import * as classes from './theme.css.ts';

export const theme = createTheme({
  activeClassName: classes.active,
});

export const vars = themeToVars(theme);
