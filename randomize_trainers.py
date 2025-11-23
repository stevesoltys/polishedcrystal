import os
import re
import random
import argparse
from collections import namedtuple, defaultdict

# A structure to hold the data for a single Pokémon entry.
PokemonData = namedtuple('PokemonData', ['level', 'species_and_data', 'moves_line'])

# A generic pool key for all Pokémon that do not have moves defined in their schema.
NO_MOVES_POOL_KEY = 'NO_MOVES_POOL'

def get_pokemon_list(constants_file):
    """
    Parses the pokemon_constants.asm file to get a list of all Pokémon.
    It excludes special entries like UNOWN, EGG, and TERU_SAMA.
    """
    pokemon_list = []
    # This regex is designed to find lines like:
    # const MEW          ; 151
    # and extract "MEW". It ensures the name starts with a letter.
    pokemon_regex = re.compile(r'^\s*const\s+([A-Z][A-Z_0-9]*)\s+;.*')
    
    # These are not real Pokémon that should appear in the wild.
    blacklist = {"NO_POKEMON", "UNOWN", "EGG", "TERU_SAMA"}

    try:
        with open(constants_file, 'r') as f:
            for line in f:
                match = pokemon_regex.match(line)
                if match:
                    pokemon_name = match.group(1)
                    if pokemon_name not in blacklist:
                        pokemon_list.append(pokemon_name)
    except FileNotFoundError:
        print(f"Error: The file {constants_file} was not found.")
        return None
    return pokemon_list

def parse_trainer_parties(lines):
    """
    Parses the trainer parties file to extract all Pokémon data.
    It groups Pokémon into pools. If a Pokémon's schema does not include moves,
    it is added to a large, generic pool. Otherwise, it is pooled with other
    Pokémon sharing the exact same schema.
    """
    pools = defaultdict(list)

    schema_regex = re.compile(r'^\s*db\s+((?:TRAINERTYPE_\w+\s*(?:\|\s*)?)+)\s*')
    pokemon_line_regex = re.compile(r'^\s*db\s+(\d+)(,\s*[A-Z][A-Z_0-9]*.*)')
    moves_line_regex = re.compile(r'^\s*db\s+[A-Z_0-9]+,\s*[A-Z_0-9]+.*')

    current_schema = None
    i = 0
    while i < len(lines):
        line = lines[i]

        schema_match = schema_regex.match(line)
        if schema_match:
            current_schema = schema_match.group(1).strip()

        poke_match = pokemon_line_regex.match(line)
        if poke_match:
            if not current_schema:
                i += 1
                continue

            level = poke_match.group(1)
            species_and_data = poke_match.group(2)
            moves_line = None

            if 'TRAINERTYPE_MOVES' in current_schema:
                pool_key = current_schema
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith(';'):
                    j += 1
                if j < len(lines) and moves_line_regex.match(lines[j]):
                    moves_line = lines[j]
                    i = j
            else:
                pool_key = NO_MOVES_POOL_KEY

            pools[pool_key].append(PokemonData(level, species_and_data, moves_line))
        i += 1
    return pools

def randomize_and_rebuild(pools, pokemon_list, original_lines, output_filepath):
    """
    Rebuilds the trainer party file using shuffled Pokémon pools.
    For trainers with move-based schemas, it shuffles their existing Pokémon.
    For trainers without moves, it replaces their Pokémon with random ones
    from the full list, preserving levels and items.
    """
    if not pools:
        print("No Pokémon found in trainer parties. Nothing to randomize.")
        return

    # Shuffle pools for schemas that include moves.
    shuffled_pools_with_moves = {
        schema: random.sample(p_list, len(p_list))
        for schema, p_list in pools.items() if schema != NO_MOVES_POOL_KEY
    }
    pool_counters = {schema: 0 for schema in shuffled_pools_with_moves}

    for schema, p_list in shuffled_pools_with_moves.items():
        print(f"Found and shuffled {len(p_list)} Pokémon for schema: {schema}")
    if NO_MOVES_POOL_KEY in pools:
        count = len(pools[NO_MOVES_POOL_KEY])
        print(f"Found {count} Pokémon slots in the generic (no-moves) pool. They will be filled from the full Pokémon list.")

    new_lines = []
    schema_regex = re.compile(r'^\s*db\s+((?:TRAINERTYPE_\w+\s*(?:\|\s*)?)+)\s*')
    pokemon_line_regex = re.compile(r'^\s*db\s+(\d+)(,\s*[A-Z][A-Z_0-9]*.*)')
    moves_line_regex = re.compile(r'^\s*db\s+[A-Z_0-9]+,\s*[A-Z_0-9]+.*')

    current_schema = None
    i = 0
    while i < len(original_lines):
        line = original_lines[i]

        schema_match = schema_regex.match(line)
        if schema_match:
            current_schema = schema_match.group(1).strip()

        poke_match = pokemon_line_regex.match(line)
        if poke_match and current_schema:
            original_level = poke_match.group(1)
            indentation = re.match(r'(\s*)', line).group(1)

            if 'TRAINERTYPE_MOVES' in current_schema:
                pool_key = current_schema
                if pool_key in shuffled_pools_with_moves:
                    pool_idx = pool_counters[pool_key]
                    if pool_idx < len(shuffled_pools_with_moves[pool_key]):
                        template = shuffled_pools_with_moves[pool_key][pool_idx]
                        pool_counters[pool_key] += 1

                        new_pokemon_line = f"{indentation}db {original_level}{template.species_and_data}\n"
                        new_lines.append(new_pokemon_line)
                        if template.moves_line:
                            new_lines.append(template.moves_line)

                        j = i + 1
                        while j < len(original_lines) and original_lines[j].strip().startswith(';'):
                            j += 1
                        if j < len(original_lines) and moves_line_regex.match(original_lines[j]):
                            i = j
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                if pokemon_list:
                    new_species = random.choice(pokemon_list)
                    original_species_and_data = poke_match.group(2)
                    parts = original_species_and_data.split(',')
                    new_species_and_data = f", {new_species}"
                    if len(parts) > 2:  # Has an item
                        item = parts[2].strip()
                        new_species_and_data += f", {item}"
                    
                    new_pokemon_line = f"{indentation}db {original_level}{new_species_and_data}\n"
                    new_lines.append(new_pokemon_line)
                else:
                    new_lines.append(line)
        else:
            new_lines.append(line)
        i += 1

    try:
        with open(output_filepath, 'w', newline='') as f:
            f.writelines(new_lines)
        print(f"\nSuccessfully wrote randomized trainer data to {output_filepath}")
    except Exception as e:
        print(f"An error occurred while writing to {output_filepath}: {e}")

def main():
    """Main function to run the trainer randomization script."""
    parser = argparse.ArgumentParser(
        description="Randomize trainer Pokémon in Polished Crystal, respecting schemas and preserving levels.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--path',
        default='.',
        help='Path to the root of the polishedcrystal project directory.'
    )
    args = parser.parse_args()

    project_path = args.path
    parties_file = os.path.join(project_path, 'data', 'trainers', 'parties.asm')
    constants_file = os.path.join(project_path, 'constants', 'pokemon_constants.asm')

    print("Starting trainer Pokémon randomization process...")

    try:
        with open(parties_file, 'r') as f:
            original_lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Trainer parties file not found at '{parties_file}'")
        return

    pools = parse_trainer_parties(original_lines)
    pokemon_list = get_pokemon_list(constants_file)

    if not pokemon_list:
        print("Could not generate a Pokémon list. Aborting randomization for no-moves trainers.")

    if pools:
        randomize_and_rebuild(pools, pokemon_list, original_lines, parties_file)
        print("\nRandomization complete!")
        print("Trainer parties have been updated.")

if __name__ == '__main__':
    main()
