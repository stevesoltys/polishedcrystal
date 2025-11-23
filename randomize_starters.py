import os
import re
import random
import argparse

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

def randomize_starters(elms_lab_file, pokemon_list):
    """
    Randomizes the three starter Pokémon in ElmsLab.asm.
    """
    if not pokemon_list:
        print("Pokémon list is empty. Cannot perform randomization.")
        return

    try:
        with open(elms_lab_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: The file {elms_lab_file} was not found.")
        return

    # Choose 3 unique random starters
    starters = random.sample(pokemon_list, 3)
    
    original_starters = ["CYNDAQUIL", "TOTODILE", "CHIKORITA"]
    
    new_starters = {
        original_starters[0]: starters[0],
        original_starters[1]: starters[1],
        original_starters[2]: starters[2],
    }

    # Use placeholders to avoid chained replacements
    content = content.replace("pokepic CYNDAQUIL", "pokepic __STARTER1__")
    content = content.replace("pokepic TOTODILE", "pokepic __STARTER2__")
    content = content.replace("pokepic CHIKORITA", "pokepic __STARTER3__")
    content = content.replace("cry CYNDAQUIL", "cry __STARTER1__")
    content = content.replace("cry TOTODILE", "cry __STARTER2__")
    content = content.replace("cry CHIKORITA", "cry __STARTER3__")
    content = content.replace("givepoke CYNDAQUIL", "givepoke __STARTER1__")
    content = content.replace("givepoke TOTODILE", "givepoke __STARTER2__")
    content = content.replace("givepoke CHIKORITA", "givepoke __STARTER3__")

# Replace placeholders with new starter names
    content = content.replace("__STARTER1__", new_starters["CYNDAQUIL"])
    content = content.replace("__STARTER2__", new_starters["TOTODILE"])
    content = content.replace("__STARTER3__", new_starters["CHIKORITA"])

    try:
        with open(elms_lab_file, 'w') as f:
            f.write(content)
        print(f"Successfully randomized starters in {elms_lab_file}")
    except Exception as e:
        print(f"An error occurred while writing to {elms_lab_file}: {e}")

def main():
    """Main function to run the randomization script."""
    parser = argparse.ArgumentParser(
        description="Randomize starter Pokémon in Polished Crystal.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--path', 
        default='.', 
        help='Path to the root of the polishedcrystal project directory.'
    )
    args = parser.parse_args()

    project_path = args.path
    constants_file = os.path.join(project_path, 'constants', 'pokemon_constants.asm')
    elms_lab_file = os.path.join(project_path, 'maps', 'ElmsLab.asm')

    print("Starting starter Pokémon randomization process...")

    if not os.path.exists(elms_lab_file):
        print(f"Error: Elm's Lab file not found at '{elms_lab_file}'")
        return

    pokemon_list = get_pokemon_list(constants_file)
    if pokemon_list:
        print(f"Successfully loaded {len(pokemon_list)} Pokémon.")
        randomize_starters(elms_lab_file, pokemon_list)
        print("\nRandomization complete!")

if __name__ == '__main__':
    main()
