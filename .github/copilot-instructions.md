# Copilot Instructions for Pokédex

## Project Overview

A web-based Pokédex that displays Pokémon information with interactive flip cards, generation filtering, and search functionality. Uses pre-scraped local JSON data and assets for fast, offline-capable loading.

## Architecture

### Frontend (Vanilla JS)
- **`index.html`** - Single-page app with search bar, generation buttons, and card container
- **`index.js`** - All frontend logic: local JSON loading, card rendering, search/filter, animations
- **`style/style.css`** - Layout, search bar, generation buttons
- **`style/cards.css`** - Pokémon card styling, flip animations, stat display

### Data Layer
- **`data/all-pokemon.json`** - All 1025 Pokémon with stats, types, evolution info, sprite positions
- **`data/spritesheet.png`** - Combined sprite sheet for card display

### Data Scraping (Python)
- **`scrape_pokemon.py`** - Async scraper using `aiohttp` to fetch from PokéAPI
  - Generates `all-pokemon.json` and `spritesheet.png`
  - Caches evolution chains for depth/family calculations
  - Run with: `python scrape_pokemon.py`

## Key Patterns

### Type Color Mapping
The `type_colors` object in `index.js` maps Pokémon types to hex colors for card backgrounds:
```javascript
const type_colors = {
    normal:'#a8a878',
    fire:'#f08030',
    // ... all 18 types
}
```

### Card Rendering
Cards use CSS 3D transforms for flip animation. Dual-type Pokémon get gradient backgrounds:
```javascript
pokemon_card_front.style = `background: linear-gradient(to right, ${type_colors[types[0]]}, ${type_colors[types[1]]})`;
```

### Search Behavior
- 1-second debounce before searching (`timeout` variable)
- Searches both name and type fields
- Animates results with staggered `move_card_up` animation

### Data Flow
1. `loadPokemonData()` fetches local `all-pokemon.json` once at startup
2. `createGenerationButtons()` creates buttons for all 9 generations
3. `changeGeneration()` filters Pokemon by `gen` field and renders cards
4. `createPokemonCard()` renders each card using local data and spritesheet

## Conventions

- **Pokémon IDs**: Always 3-digit padded (`#001`, `#025`)
- **Stats order**: HP, ATK, DEF, SP.ATK, SP.DEF, SPEED (matches PokéAPI)
- **Special cases**: Nidoran♀/♂ have special name handling with `-f`/`-m` suffix detection
- **Spritesheet**: Uses `spriteX`/`spriteY` from JSON, 96x96 sprites

## External Dependencies

- **Bulbapedia** - Card links go to `bulbapedia.bulbagarden.net/wiki/{Name}_(Pokémon)`

## Python Scraper Notes

When modifying `scrape_pokemon.py`:
- Uses `aiohttp` for async HTTP, `PIL` for sprite sheet generation
- Processes in chunks of 50 with 0.5s delay to avoid rate limits
- Evolution data cached globally before processing species
- PNG cleaning function handles corrupted iCCP chunks from PokéAPI sprites
