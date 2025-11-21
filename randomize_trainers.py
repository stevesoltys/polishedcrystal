import os
import re
import random
import argparse
from collections import namedtuple, defaultdict

# A structure to hold the data for a single Pokémon entry.
# 'level' is stored separately from the rest of the definition line.
PokemonData = namedtuple('PokemonData', ['level', 'species_and_data', 'moves_line'])

def parse_trainer_parties(lines):
    """
    Parses the trainer parties file to extract all Pokémon data.
    It groups Pokémon into pools based on their schema (the TRAINERTYPE flags).

    Returns a dictionary of pools: {schema_string: [PokemonData, ...]}
    """
    pools = defaultdict(list)

    # Regex to identify a trainer's schema definition line.
    schema_regex = re.compile(r'^\s*db\s+((?:TRAINERTYPE_\w+\s*(?:\|\s*)?)+)\s*')
    # Regex to identify and capture parts of a Pokémon definition line.
    # Group 1: The level (e.g., '45')
    # Group 2: The rest of the line, including species and optional data (e.g., ', KINGLER, KINGS_ROCK')
    pokemon_line_regex = re.compile(r'^\s*db\s+(\d+)(,\s*[A-Z][A-Z_0-9]*.*)')
    # Regex to identify a line defining moves.
    moves_line_regex = re.compile(r'^\s*db\s+[A-Z_0-9]+,\s*[A-Z_0-9]+.*')

    current_schema = None
    i = 0
    while i < len(lines):
        line = lines[i]

        # Find the schema for the current trainer party.
        schema_match = schema_regex.match(line)
        if schema_match:
            current_schema = schema_match.group(1).strip()

        # If we have a schema and find a Pokémon, parse it.
        poke_match = pokemon_line_regex.match(line)
        if poke_match:
            if not current_schema:
                # This can happen for malformed entries; we'll skip them.
                i += 1
                continue

            level = poke_match.group(1)
            species_and_data = poke_match.group(2)
            moves_line = None

            # If the schema includes moves, look for the corresponding moves line.
            if 'TRAINERTYPE_MOVES' in current_schema:
                # Look ahead for the moves line, skipping any comments.
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith(';'):
                    j += 1

                if j < len(lines) and moves_line_regex.match(lines[j]):
                    moves_line = lines[j]
                    i = j  # Move the main index past the moves line we just consumed.

            # Add the parsed Pokémon to the appropriate pool based on its schema.
            pools[current_schema].append(PokemonData(level, species_and_data, moves_line))

        i += 1

    return pools

def randomize_and_rebuild(pools, original_lines, output_filepath):
    """
    Rebuilds the trainer party file using the shuffled Pokémon pools,
    while preserving the original levels for each slot.
    """
    if not pools:
        print("No Pokémon found in trainer parties. Nothing to randomize.")
        return

    # Shuffle each pool of Pokémon independently.
    shuffled_pools = {schema: random.sample(pokemon_list, len(pokemon_list))
                      for schema, pokemon_list in pools.items()}

    # Keep track of how many Pokémon from each pool we've used so far.
    pool_counters = {schema: 0 for schema in pools}

    for schema, pokemon_list in pools.items():
        print(f"Found and shuffled {len(pokemon_list)} Pokémon for schema: {schema}")

    new_lines = []

    # Regexes to find the lines we need to replace or skip.
    schema_regex = re.compile(r'^\s*db\s+((?:TRAINERTYPE_\w+\s*(?:\|\s*)?)+)\s*')
    pokemon_line_regex = re.compile(r'^\s*db\s+(\d+)(,\s*[A-Z][A-Z_0-9]*.*)')
    moves_line_regex = re.compile(r'^\s*db\s+[A-Z_0-9]+,\s*[A-Z_0-9]+.*')

    current_schema = None
    i = 0
    while i < len(original_lines):
        line = original_lines[i]

        # Update the current schema when we find a new trainer definition.
        schema_match = schema_regex.match(line)
        if schema_match:
            current_schema = schema_match.group(1).strip()

        # If it's a Pokémon line, replace it with a shuffled one from the correct pool.
        poke_match = pokemon_line_regex.match(line)
        if poke_match:
            if current_schema and current_schema in shuffled_pools:
                pool_idx = pool_counters[current_schema]
                if pool_idx < len(shuffled_pools[current_schema]):
                    # Get the original level from the current line.
                    original_level = poke_match.group(1)

                    # Get the next shuffled Pokémon "template" from the correct pool.
                    new_pokemon_template = shuffled_pools[current_schema][pool_idx]
                    pool_counters[current_schema] += 1

                    # Reconstruct the Pokémon line with the original level and the new species/data.
                    # We need to preserve the original indentation.
                    indentation = re.match(r'(\s*)', line).group(1)
                    new_pokemon_line = f"{indentation}db {original_level}{new_pokemon_template.species_and_data}\n"

                    # Add the new Pokémon's data to our output.
                    new_lines.append(new_pokemon_line)
                    if new_pokemon_template.moves_line:
                        new_lines.append(new_pokemon_template.moves_line)

                    # If the original Pokémon had moves, we must skip its moves line in the input.
                    if 'TRAINERTYPE_MOVES' in current_schema:
                        j = i + 1
                        while j < len(original_lines) and original_lines[j].strip().startswith(';'):
                            j += 1
                        if j < len(original_lines) and moves_line_regex.match(original_lines[j]):
                            i = j  # Skip the original moves line.
                else:
                    # This case should not be reached with correct parsing.
                    new_lines.append(line)
            else:
                # Keep the line if it's a Pokémon without a recognized schema.
                new_lines.append(line)
        else:
            # This line is not a Pokémon definition, so keep it as is.
            new_lines.append(line)

        i += 1

    # Write the new content to the file, preserving original line endings.
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

    print("Starting trainer Pokémon randomization process...")

    try:
        with open(parties_file, 'r') as f:
            original_lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Trainer parties file not found at '{parties_file}'")
        return

    # Parse the file to get all Pokémon grouped by schema.
    pools = parse_trainer_parties(original_lines)

    if pools:
        # Randomize and write back to the same file.
        randomize_and_rebuild(pools, original_lines, parties_file)
        print("\nRandomization complete!")
        print("Trainer parties have been updated while preserving original levels.")

if __name__ == '__main__':
    main()
