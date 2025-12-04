import asyncio
import aiohttp
import json
import os
import time
from PIL import Image
from io import BytesIO
import math
import struct

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'all-pokemon.json')

# Cache for evolution chain data: species_name -> evolution_depth
evolution_depth_cache = {}
# Cache for evolution family: species_name -> list of all species IDs in the family
evolution_family_cache = {}
# Cache for final evolution method: species_name -> 'early' | 'late' | None
# 'late' = evolves at level 40+, uses item, special location, trade, or other special method
# 'early' = evolves by level-up before level 40
# None = doesn't evolve or is base form
evolution_method_cache = {}

def clean_png_data(data):
    """Remove non-critical PNG chunks that may have bad checksums (e.g., iCCP)"""
    if not data or len(data) < 8 or data[:8] != b'\x89PNG\r\n\x1a\n':
        return data
    
    clean = data[:8]  # PNG signature
    pos = 8
    
    while pos < len(data):
        if pos + 8 > len(data):
            break
            
        chunk_len = struct.unpack('>I', data[pos:pos+4])[0]
        chunk_type = data[pos+4:pos+8]
        chunk_end = pos + 12 + chunk_len
        
        if chunk_end > len(data):
            break
        
        # Keep only critical chunks and safe ancillary chunks
        # Skip chunks that may have bad checksums (iCCP, iTXt, zTXt, etc.)
        safe_chunks = [b'IHDR', b'PLTE', b'IDAT', b'IEND', b'tRNS', b'bKGD', b'pHYs']
        
        if chunk_type in safe_chunks:
            clean += data[pos:chunk_end]
        
        pos = chunk_end
        
        if chunk_type == b'IEND':
            break
    
    return clean

async def fetch_url(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Error fetching {url}: {response.status}")
                return None
    except Exception as e:
        print(f"Exception fetching {url}: {e}")
        return None

async def fetch_all_evolution_chains(session):
    """Fetch all evolution chains and build a mapping of species name to evolution stage."""
    print("Fetching evolution chains...")
    
    # Get total count of evolution chains
    url = "https://pokeapi.co/api/v2/evolution-chain/?limit=1"
    data = await fetch_url(session, url)
    if not data:
        return
    
    total_chains = data['count']
    print(f"Found {total_chains} evolution chains to process.")
    
    # Fetch all chain URLs
    url = f"https://pokeapi.co/api/v2/evolution-chain/?limit={total_chains}"
    data = await fetch_url(session, url)
    if not data:
        return
    
    chain_urls = [item['url'] for item in data['results']]
    
    # Process chains in chunks
    chunk_size = 50
    for i in range(0, len(chain_urls), chunk_size):
        chunk = chain_urls[i:i+chunk_size]
        print(f"Processing evolution chains {i} to {i+len(chunk)}...")
        tasks = [fetch_url(session, url) for url in chunk]
        results = await asyncio.gather(*tasks)
        
        for chain_data in results:
            if chain_data:
                process_evolution_chain(chain_data['chain'], 1)
        
        await asyncio.sleep(0.3)
    
    print(f"Cached evolution data for {len(evolution_depth_cache)} species.")

def get_max_chain_depth(chain):
    """Recursively find the maximum depth of an evolution chain."""
    if not chain.get('evolves_to') or len(chain['evolves_to']) == 0:
        return 1
    
    max_depth = 0
    for evolution in chain['evolves_to']:
        depth = get_max_chain_depth(evolution)
        max_depth = max(max_depth, depth)
    
    return 1 + max_depth

def process_evolution_chain(chain, current_stage, max_stage=None, family_ids=None):
    """Process an evolution chain and cache species with their evolution depth and family.
    
    The evolution depth represents how many total stages exist in this Pokemon's
    evolution line. The evolution family is a list of all Pokemon IDs in the line.
    For example: Bulbasaur has depth 3 and family [1, 2, 3].
    """
    # First pass: calculate max depth and collect all family IDs
    if max_stage is None:
        max_stage = get_max_chain_depth(chain)
        family_ids = collect_family_ids(chain)
    
    species_name = chain['species']['name']
    evolution_depth_cache[species_name] = max_stage
    evolution_family_cache[species_name] = family_ids
    
    # For the base form (no evolution details), set method to None
    if not chain.get('evolution_details') or len(chain['evolution_details']) == 0:
        evolution_method_cache[species_name] = None
    
    for evolution in chain.get('evolves_to', []):
        # Determine if this evolution is "late game"
        evo_details = evolution.get('evolution_details', [])
        is_late_game = False
        
        if evo_details:
            detail = evo_details[0]  # Use first evolution method
            trigger = detail.get('trigger', {}).get('name', '')
            min_level = detail.get('min_level')
            
            # Late game conditions:
            # 1. Level 40+
            # 2. Uses an evolution item
            # 3. Trade evolution
            # 4. Special location required
            # 5. Needs specific held item
            # 6. Needs known move or move type (usually learned late)
            if min_level and min_level >= 40:
                is_late_game = True
            elif trigger == 'use-item' or detail.get('item'):
                is_late_game = True
            elif trigger == 'trade':
                is_late_game = True
            elif detail.get('location'):
                is_late_game = True
            elif detail.get('held_item'):
                is_late_game = True
            elif detail.get('known_move') or detail.get('known_move_type'):
                is_late_game = True
        
        evolved_species_name = evolution['species']['name']
        evolution_method_cache[evolved_species_name] = 'late' if is_late_game else 'early'
        
        process_evolution_chain(evolution, current_stage + 1, max_stage, family_ids)

def collect_family_ids(chain):
    """Recursively collect all species IDs in an evolution chain."""
    # Extract ID from species URL (e.g., ".../pokemon-species/1/" -> 1)
    species_url = chain['species']['url']
    species_id = int(species_url.rstrip('/').split('/')[-1])
    
    ids = [species_id]
    for evolution in chain.get('evolves_to', []):
        ids.extend(collect_family_ids(evolution))
    
    return sorted(ids)

async def fetch_url(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Error fetching {url}: {response.status}")
                return None
    except Exception as e:
        print(f"Exception fetching {url}: {e}")
        return None

async def get_generations(session):
    print("Fetching generations...")
    url = "https://pokeapi.co/api/v2/generation/"
    data = await fetch_url(session, url)
    generations = []
    if data:
        generations.extend(data['results'])
        while data['next']:
            data = await fetch_url(session, data['next'])
            if data:
                generations.extend(data['results'])
    return generations

async def get_species_from_gen(session, gen_url, gen_id):
    data = await fetch_url(session, gen_url)
    species_list = []
    region_name = "Unknown"
    if data:
        region_name = data.get('main_region', {}).get('name', 'Unknown').capitalize()
        for s in data['pokemon_species']:
            s['gen_id'] = gen_id
            species_list.append(s)
    return species_list, region_name

async def process_species(session, species_entry):
    url = species_entry['url']
    gen_id = species_entry['gen_id']
    
    species_data = await fetch_url(session, url)
    if not species_data:
        return None

    # Get English flavor text
    description = ""
    for entry in species_data.get('flavor_text_entries', []):
        if entry['language']['name'] == 'en':
            description = entry['flavor_text'].replace('\n', ' ').replace('\f', ' ')
            break
    
    # Get egg groups
    egg_group_renames = {
        'Water1': 'Water 1',
        'Water2': 'Water 2',
        'Water3': 'Water 3',
        'No-eggs': 'No Eggs',
        'Ground': 'Field',
        'Humanshape': 'Human-Like',
        'Plant': 'Grass',
        'Indeterminate': 'No Gender'
    }
    egg_groups = []
    for eg in species_data.get('egg_groups', []):
        name = eg['name'].capitalize()
        egg_groups.append(egg_group_renames.get(name, name))
    
    # Get capture rate
    capture_rate = species_data.get('capture_rate', 0)
            
    # Get default variety
    default_variety = next((v for v in species_data['varieties'] if v['is_default']), species_data['varieties'][0])
    pokemon_url = default_variety['pokemon']['url']
    
    pokemon_data = await fetch_url(session, pokemon_url)
    if not pokemon_data:
        return None

    # Stats
    stats = {}
    stat_map = {
        'hp': 'hp',
        'attack': 'atk',
        'defense': 'def',
        'special-attack': 'spa',
        'special-defense': 'spd',
        'speed': 'spe'
    }
    bst = 0
    for s in pokemon_data['stats']:
        s_name = s['stat']['name']
        if s_name in stat_map:
            val = s['base_stat']
            stats[stat_map[s_name]] = val
            bst += val

    # Types
    types = [t['type']['name'].capitalize() for t in pokemon_data['types']]

    # Pseudo detection (Heuristic: BST >= 600, Not Legendary/Mythical, usually 3 stage but we skip that check)
    # Exclude Slaking (670), Traunt ability makes it not pseudo despite high BST
    is_legendary = species_data['is_legendary']
    is_mythical = species_data['is_mythical']
    is_pseudo = (bst >= 600) and (not is_legendary) and (not is_mythical) and (pokemon_data['name'] != 'slaking')
    
    # Evolution depth and family (from cached data)
    evolution_depth = evolution_depth_cache.get(species_data['name'], 1)
    evolution_family = evolution_family_cache.get(species_data['name'], [species_data['id']])
    
    # Is this Pokemon a late-game evolution? (level 40+, item, trade, location, etc.)
    evolution_method = evolution_method_cache.get(species_data['name'])
    is_late_evolution = evolution_method == 'late'

    # Download Sprite to memory (will be combined into sprite sheet later)
    sprite_url = pokemon_data['sprites']['front_default']
    sprite_data = None
    if sprite_url:
        try:
            async with session.get(sprite_url) as resp:
                if resp.status == 200:
                    sprite_data = await resp.read()
        except Exception as e:
            print(f"Error downloading sprite for {species_data['name']}: {e}")

    return {
        "id": species_data['id'],
        "name": species_data['name'].capitalize(),
        "types": types,
        "eggGroups": egg_groups,
        "captureRate": capture_rate,
        "stats": stats,
        "bst": bst,
        "gen": gen_id,
        "height": pokemon_data['height'] / 10, # dm to m
        "weight": pokemon_data['weight'] / 10, # hg to kg
        "isLegendary": is_legendary,
        "isMythical": is_mythical,
        "isPseudo": is_pseudo,
        "isLateEvolution": is_late_evolution,
        "evolutionDepth": evolution_depth,
        "evolutionFamily": evolution_family,
        "description": description,
        "spriteData": sprite_data  # Raw sprite bytes for sprite sheet
    }

async def main():
    async with aiohttp.ClientSession() as session:
        # 1. Fetch all evolution chains first
        await fetch_all_evolution_chains(session)
        
        # 2. Get Generations
        gens = await get_generations(session)
        print(f"Found {len(gens)} generations.")

        # 3. Get Species List per Gen
        tasks = []
        for i, gen in enumerate(gens):
            # Gen ID is i+1 usually, or extract from url
            gen_id = int(gen['url'].split('/')[-2])
            tasks.append(get_species_from_gen(session, gen['url'], gen_id))
        
        results = await asyncio.gather(*tasks)
        all_species_entries = []
        
        for res, region in results:
            all_species_entries.extend(res)
            
        print(f"Found {len(all_species_entries)} species total.")
        
        # 4. Process Species (in chunks to avoid rate limits/overload)
        final_pokemon = []
        chunk_size = 50
        for i in range(0, len(all_species_entries), chunk_size):
            chunk = all_species_entries[i:i+chunk_size]
            print(f"Processing chunk {i} to {i+len(chunk)}...")
            tasks = [process_species(session, s) for s in chunk]
            chunk_results = await asyncio.gather(*tasks)
            final_pokemon.extend([r for r in chunk_results if r])
            # Small sleep to be nice to API
            await asyncio.sleep(0.5)

        # Sort by ID
        final_pokemon.sort(key=lambda x: x['id'])

        # Generate Sprite Sheet
        print("Generating sprite sheet...")
        SPRITE_SIZE = 96
        # Calculate grid dimensions (use a square-ish layout)
        total_pokemon = len(final_pokemon)
        cols = math.ceil(math.sqrt(total_pokemon))
        rows = math.ceil(total_pokemon / cols)
        
        # Create sprite sheet image
        sheet_width = cols * SPRITE_SIZE
        sheet_height = rows * SPRITE_SIZE
        sprite_sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
        
        # Place each sprite and record position
        for i, pokemon in enumerate(final_pokemon):
            col = i % cols
            row = i // cols
            x = col * SPRITE_SIZE
            y = row * SPRITE_SIZE
            
            # Store sprite position in pokemon data
            pokemon['spriteX'] = col
            pokemon['spriteY'] = row
            
            # Paste sprite if we have data
            if pokemon.get('spriteData'):
                try:
                    sprite_bytes = pokemon['spriteData']
                    # Clean PNG data to remove potentially corrupted chunks (e.g., bad iCCP)
                    clean_bytes = clean_png_data(sprite_bytes)
                    bio = BytesIO(clean_bytes)
                    sprite_img = Image.open(bio)
                    sprite_img.load()  # Force decode
                    # Resize to 96x96 if needed (sprites are usually 96x96)
                    if sprite_img.size != (SPRITE_SIZE, SPRITE_SIZE):
                        sprite_img = sprite_img.resize((SPRITE_SIZE, SPRITE_SIZE), Image.Resampling.NEAREST)
                    # Convert to RGBA if needed
                    if sprite_img.mode != 'RGBA':
                        sprite_img = sprite_img.convert('RGBA')
                    sprite_sheet.paste(sprite_img, (x, y), sprite_img)
                except Exception as e:
                    print(f"Error processing sprite for {pokemon['name']} (id={pokemon['id']}): {e}")
            
            # Remove sprite data from final output (not needed in JSON)
            del pokemon['spriteData']
        
        # Save sprite sheet
        sprite_sheet_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'spritesheet.png')
        sprite_sheet.save(sprite_sheet_path, 'PNG', optimize=True)
        print(f"Sprite sheet saved: {cols}x{rows} grid ({sheet_width}x{sheet_height}px)")

        # Save Pokemon
        print(f"Saving {len(final_pokemon)} pokemon to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_pokemon, f, indent=2)

        print("Done!")

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    print(f"Duration: {time.time() - start_time:.2f} seconds")
