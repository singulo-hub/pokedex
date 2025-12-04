const pokemon_container = document.getElementById('pokemon_container');
const search_bar = document.getElementById('search_bar');
const search_error = document.getElementById('search_error');
const generation_container = document.getElementById('generation_container');
const pokedex_name = document.getElementById('pokedex_name');

// In milliseconds
const card_anim_speed = 1000;

let timeout = null;
// Helps keep track of the current gen for the buttons
let current_generation = 1;
// Number is used for staggering the animation
let number = 0;
// All pokemon data from local JSON
let allPokemonData = [];
// Current displayed pokemon for search filtering
let currentPokemon = [];
let anim_timeouts = [];

// These are all the colors I use for the background of each pokemon card
const type_colors = {
    normal:'#a8a878',
    fire:'#f08030',
    water:'#6890f0',
    grass:'#78c850',
    electric:'#f8d030',
    ice:'#98d8d8',
    fighting:'#c03028',
    poison:'#a040a0',
    ground:'#e0c068',
    flying:'#a890f0',
    psychic:'#f85888',
    bug:'#a8b820',
    rock:'#b8a038',
    ghost:'#705898',
    dark:'#705848',
    dragon:'#7038f8',
    steel:'#b8b8d0',
    fairy:'#f0b6bc'
}

// Generation data with region names
const generations = [
    { id: 1, name: 'Kanto' },
    { id: 2, name: 'Johto' },
    { id: 3, name: 'Hoenn' },
    { id: 4, name: 'Sinnoh' },
    { id: 5, name: 'Unova' },
    { id: 6, name: 'Kalos' },
    { id: 7, name: 'Alola' },
    { id: 8, name: 'Galar' },
    { id: 9, name: 'Paldea' }
];

// Load all pokemon data from local JSON
const loadPokemonData = async () => {
    try {
        const response = await fetch('data/all-pokemon.json');
        allPokemonData = await response.json();
        
        // Create generation buttons
        createGenerationButtons();
        
        // Load first generation
        changeGeneration(1);
    } catch(e) {
        errorShake('Failed to load Pokemon data');
        console.error(e);
    }
}

const createGenerationButtons = () => {
    generations.forEach((gen) => {
        const generation_button = document.createElement('div');
        generation_button.classList.add('generation_button_container');

        generation_button.innerHTML = `
            <button type="button" id="generation_button_${gen.id}" onclick="changeGeneration(${gen.id})">${gen.id}</button>`;
        
        if (gen.id === 1) {
            const button = Array.from(generation_button.children)[0];
            button.disabled = true;
            button.style.color = '#fff';
            button.style.cursor = 'default';
        }

        generation_container.appendChild(generation_button);
    });
}

const changeGeneration = (genId) => {
    current_generation = genId;
    const gen = generations.find(g => g.id === genId);

    // Clear disabled from each generation button
    const children = Array.from(generation_container.children);
    children.forEach(child => {
        const button = Array.from(child.children)[0];

        if (button.id === `generation_button_${genId}`) {
            button.disabled = true;
            button.style.color = '#fff';
            button.style.cursor = 'default';
        } else {
            button.disabled = false;
            button.style.color = '#999';
            button.style.cursor = 'pointer';
        }
    });

    search_bar.value = '';
    search_error.textContent = '';
    
    pokedex_name.innerHTML = `${gen.name} Pokédex`;
    pokemon_container.innerHTML = '';

    // Filter pokemon by generation
    currentPokemon = allPokemonData.filter(p => p.gen === genId);
    
    number = 0;
    currentPokemon.forEach(pokemon => {
        createPokemonCard(pokemon);
    });
}

// Shake the search bar when the search fails and show error message
function errorShake(error_text) {
    search_error.textContent = error_text;

    search_bar.classList.add('error_shake');
    setTimeout(function() {
        search_bar.classList.remove('error_shake');
    }, 500);
}

// Waits for one second to see if the user stops typing,
// then searches for the Pokemon
const searchPokemon = async () => {
    clearTimeout(timeout);

    search_error.textContent = '';

    timeout = setTimeout(function() {
        const search_value = search_bar.value.toLowerCase();
        const pokemon_cards = Array.from(pokemon_container.children);
        let search_results = [];

        if (search_value != '') {
            for (let index = 0; index < currentPokemon.length; index++) {
                // First search for names
                if (currentPokemon[index].name.toLowerCase().search(search_value) != -1) {
                    search_results.push(index);
                    continue;
                }

                // Then search for types
                for (let type_index = 0; type_index < currentPokemon[index].types.length; type_index++) {
                    if (currentPokemon[index].types[type_index].toLowerCase().search(search_value) != -1) {
                        search_results.push(index);
                        break;
                    }
                }
            }

            // Clear the animation timeouts
            anim_timeouts.forEach(anim_timeout => {
                clearTimeout(anim_timeout);
            });

            // Next hide the cards
            for (let index = 0; index < pokemon_cards.length; index++) {
                if (pokemon_cards[index].classList.contains('move_card_up')) {
                    pokemon_cards[index].classList.remove('move_card_up');
                    pokemon_cards[index].style.animationPlayState = 'paused';
                }
                pokemon_cards[index].style.display = 'none';
            }     

            anim_timeouts = [];
            number = 0;

            // Then show the few results
            search_results.forEach(index => {
                addMoveUpAnim(pokemon_cards[index]);
            });
        // If search bar is cleared, then show all pokemon in current gen
        } else {
            // Clear the animation timeouts
            anim_timeouts.forEach(anim_timeout => {
                clearTimeout(anim_timeout);
            });

            anim_timeouts = [];
            number = 0;

            pokemon_cards.forEach(pokemon_card => {
                addMoveUpAnim(pokemon_card);
            });
        }
    }, 1000);
}

function addMoveUpAnim(pokemon_card) {
    pokemon_card.style.display = 'flex';
                    
    pokemon_card.classList.add('move_card_up');

    // Add the animation to the cards
    let anim_timeout = setTimeout(() => {
        pokemon_card.style.animationPlayState = 'running';
        pokemon_card.style.display = 'flex';
        setTimeout(() => {
            pokemon_card.classList.remove('move_card_up');
            pokemon_card.style.animationPlayState = 'paused';
        }, card_anim_speed);
    }, number * 20);

    anim_timeouts.push(anim_timeout);
    number += 1;
}

function createPokemonCard(pokemon) {
    const pokemon_card = document.createElement('div');
    pokemon_card.classList.add('pokemon_card');
    
    const types = pokemon.types;
    let type_innerHTML = `<span class='type'>${types[0].toUpperCase()}</span>`;
    if (types.length > 1) {
        type_innerHTML += `<span class='type'>${types[1].toUpperCase()}</span>`;
    }

    let name = pokemon.name;
    
    // Very special case for the Nidoran family
    if (name.endsWith('-f')) {
        name = name.slice(0, -2) + '♀';
    } else if (name.endsWith('-m')) {
        name = name.slice(0, -2) + '♂';
    }

    // Calculate sprite position from spritesheet
    const SPRITE_SIZE = 96;
    const spriteX = pokemon.spriteX * SPRITE_SIZE;
    const spriteY = pokemon.spriteY * SPRITE_SIZE;

    // Use pre-calculated BST from JSON
    const stats = pokemon.stats;
    const total_stats = pokemon.bst;

    let stats_innerHTML = `
    <table class='stats'>
        <tr>
            <th>
                <div class='stat_box hp'></div>
                HP
            </th>
            <th>${stats.hp}</th>
            <th>
                <div class='stat_box sp_atk'></div>
                SP. ATK
            </th>
            <th>${stats.spa}</th>
        </tr>
        <tr>
            <th>
                <div class='stat_box atk'></div>
                ATK
            </th>
            <th>${stats.atk}</th>
            <th>
                <div class='stat_box sp_def'></div>
                SP. DEF
            </th>
            <th>${stats.spd}</th>
        </tr>
        <tr>
            <th>
                <div class='stat_box def'></div>
                DEF
            </th>
            <th>${stats.def}</th>
            <th>
                <div class='stat_box speed'></div>
                SPEED
            </th>
            <th>${stats.spe}</th>
        </tr>
        <tr>
            <th class='total'>TOTAL</th>
            <th>${total_stats}</th>
            <th></th>
            <th>
                <a class='bulb_link' href='https://bulbapedia.bulbagarden.net/wiki/${name}_(Pokémon)' target='_blank'>
                    <img src='data/bulbapedia.png'>
                </a>
            </th>
        </tr>
    </table>
    `;

    const pokemon_innerHTML = `
        <div class='pokemon_card_inner' onclick='flipCard(this)'>
            <div class='pokemon_card_front'>
                <div class='info'>
                    <div class='basic_info'>
                        <span class='number'>#${('000' + pokemon.id).slice(-3)}</span>
                        <div class='sprite_and_name'>
                            <h3 class='name'>${name}</h3>
                        </div>
                    </div>
                    <div class='types'>
                        ${type_innerHTML}
                    </div>
                </div>
                <div class='img-container'>
                    <div class='sprite' style='background-position: -${spriteX}px -${spriteY}px;'></div>
                </div>
            </div>
            <div class='pokemon_card_back'>
                ${stats_innerHTML}
            </div>
        </div>
    `;

    pokemon_card.innerHTML = pokemon_innerHTML;
    
    // Color the front and back with a gradient if more than one type is present
    const pokemon_card_front = Array.from(Array.from(pokemon_card.children)[0].children)[0];
    const pokemon_card_back = Array.from(Array.from(pokemon_card.children)[0].children)[1];
    const type1 = types[0].toLowerCase();
    const type2 = types.length > 1 ? types[1].toLowerCase() : null;
    
    if (type2) {
        pokemon_card_front.style = `background: -webkit-linear-gradient(
            to right,
            ${type_colors[type1]},
            ${type_colors[type2]})`;
        pokemon_card_back.style = `background: -webkit-linear-gradient(
            to right,
            ${type_colors[type1]},
            ${type_colors[type2]})`;

        pokemon_card_front.style = `background: linear-gradient(
        to right,
        ${type_colors[type1]},
        ${type_colors[type2]})`;
        pokemon_card_back.style = `background: linear-gradient(
            to right,
            ${type_colors[type1]},
            ${type_colors[type2]})`;
    } else {
        pokemon_card_front.style = `background:${type_colors[type1]}`;
        pokemon_card_back.style = `background:${type_colors[type1]}`;
    }
    pokemon_container.appendChild(pokemon_card);

    addMoveUpAnim(pokemon_card);
}

function flipCard(card) {
    if (card.style.transform == 'rotateX(180deg)') {
        card.style.transform = '';
    } else {
        card.style.transform = 'rotateX(180deg)';
    }
}

// Clear the search bar from previous visits
search_bar.value = '';

// Load pokemon data and initialize
loadPokemonData();
