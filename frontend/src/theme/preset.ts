import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

/*
 * Preset do PrimeVue para o FeedLens: Aura com a primária trocada pelo âmbar
 * da marca. Mantemos a escala neutra do Aura (bem calibrada) e só
 * sobrescrevemos a cor primária, para não brigar com os tokens em theme.css.
 */
const amber = {
  50: '#fdf6e9',
  100: '#fae6c4',
  200: '#f6d59c',
  300: '#f3c374',
  400: '#f2b657',
  500: '#f2a93b', // âmbar foco
  600: '#d78f26',
  700: '#a86f1d',
  800: '#7a5015',
  900: '#4d320c',
  950: '#2a1b06',
}

export const FeedLensPreset = definePreset(Aura, {
  semantic: {
    primary: amber,
    colorScheme: {
      light: {
        primary: {
          color: '{primary.500}',
          contrastColor: '#171a23',
          hoverColor: '{primary.600}',
          activeColor: '{primary.700}',
        },
      },
      dark: {
        primary: {
          color: '{primary.400}',
          contrastColor: '#171a23',
          hoverColor: '{primary.300}',
          activeColor: '{primary.200}',
        },
      },
    },
  },
})
