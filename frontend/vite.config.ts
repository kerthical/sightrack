import { vanillaExtractPlugin } from '@vanilla-extract/vite-plugin';
import viteReact from '@vitejs/plugin-react';
import cssnano from 'cssnano';
import { resolve } from 'path';
import mantinePreset from 'postcss-preset-mantine';
import simpleVars from 'postcss-simple-vars';
import tailwindcss from 'tailwindcss';
import { defineConfig } from 'vite';

const root = resolve('src');
export default defineConfig(() => ({
  plugins: [viteReact(), vanillaExtractPlugin()],
  root: root,
  resolve: {
    alias: {
      '@': root,
    },
  },
  build: {
    outDir: resolve('dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        remote: resolve(root, 'remote.html'),
        local: resolve(root, 'local.html'),
      },
    },
  },
  esbuild: {
    legalComments: 'none' as const,
  },
  css: {
    postcss: {
      plugins: [
        // eslint-disable-next-line @typescript-eslint/no-unsafe-call
        mantinePreset(),
        simpleVars({
          variables: {
            'mantine-breakpoint-xs': '36em',
            'mantine-breakpoint-sm': '48em',
            'mantine-breakpoint-md': '62em',
            'mantine-breakpoint-lg': '75em',
            'mantine-breakpoint-xl': '88em',
          },
        }),
        tailwindcss({
          content: ['./src/**/*.{js,jsx,ts,tsx}'],
        }),
        cssnano(),
      ],
    },
  },
}));
