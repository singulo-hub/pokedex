# Pokédex
Easily find information about Pokémon.

## Features
- Browse all 1025 Pokémon across 9 generations
- Filter by generation using the numbered buttons
- Search by name or type within the current generation
- Click any Pokémon card to flip and see base stats
- Each card links to the Pokémon's Bulbapedia entry

## How It Works

The app loads pre-scraped Pokémon data from local JSON files for fast, offline-capable browsing. All artwork and sprites are stored locally.

### Data Scraping

To update the Pokémon data, run the Python scraper:

```bash
python scrape_pokemon.py
```

This fetches data from [PokéAPI](https://pokeapi.co/) and generates:
- `data/all-pokemon.json` - All Pokémon with stats, types, evolution info
- `data/spritesheet.png` - Combined sprite sheet for card display

## History

### Original Version (API-based)
The original Pokédex fetched data directly from PokéAPI on every page load:
- `getGenerations()` fetched the generation list from the API
- `changeGeneration()` fetched generation details to get Pokémon count/offset
- `getAllPokemon()` batch-fetched individual Pokémon data
- Each Pokémon card loaded sprites and artwork directly from PokéAPI URLs
- A loading Pikachu GIF displayed while waiting for API responses

This approach had drawbacks:
- Slow initial load times (many API requests per generation)
- Dependent on PokéAPI availability
- No offline support
- Rate limiting concerns with heavy usage

### Current Version (Local Data)
The app now uses pre-scraped local data:
- Single fetch of `all-pokemon.json` at startup (~1MB)
- Instant generation switching (just filters local array)
- All assets served locally (spritesheet + artwork)
- Works offline once loaded
- No API dependencies at runtime

## Credits
Icon: https://iconarchive.com/show/dumper-icons-by-draseart/PokeBall-icon.html

Bulbapedia icon: https://www.clipartmax.com/middle/m2i8A0b1A0N4d3m2_pok%C3%A9mon-wiki-file-apk-free-for-pc-smart-tv-download-bulbapedia-icon/

Pokémon and Pokémon names are trademarks of Nintendo.
