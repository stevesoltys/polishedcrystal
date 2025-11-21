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

def randomize_wild_files(wild_dir, pokemon_list):
    """
    Scans for .asm files in the specified directory and randomizes
    the Pokémon in `wildmon` entries.
    """
    if not pokemon_list:
        print("Pokémon list is empty. Cannot perform randomization.")
        return

    # This regex captures the parts of a `wildmon` line:
    # Group 1: The 'wildmon <level>, ' part.
    # Group 2: The Pokémon name.
    # Group 3: Any extra data like ', ALOLAN_FORM'.
    wildmon_regex = re.compile(r'(^\s*wildmon\s+\d+,\s+)([A-Z][A-Z_0-9]*)(.*)')

    for filename in os.listdir(wild_dir):
        if not filename.endswith('.asm'):
            continue
            
        filepath = os.path.join(wild_dir, filename)
        print(f"Processing {filepath}...")
        
        new_content = []
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            for line in lines:
                match = wildmon_regex.match(line)
                if match:
                    # Choose a new random Pokémon
                    new_pokemon = random.choice(pokemon_list)
                    
                    # Reconstruct the line with the new Pokémon
                    # `match.group(1)` is 'wildmon <level>, '
                    # `match.group(3)` is the optional form data
                    new_line = f"{match.group(1)}{new_pokemon}{match.group(3)}\n"
                    new_content.append(new_line)
                else:
                    # Keep lines that don't match as they are
                    new_content.append(line)
            
            # Write the modified content back to the file
            with open(filepath, 'w') as f:
                f.writelines(new_content)
                
        except Exception as e:
            print(f"An error occurred while processing {filepath}: {e}")

def main():
    """Main function to run the randomization script."""
    parser = argparse.ArgumentParser(
        description="Randomize wild Pokémon in Polished Crystal.",
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
    wild_dir = os.path.join(project_path, 'data', 'wild')

    print("Starting Pokémon randomization process...")

    if not os.path.isdir(wild_dir):
        print(f"Error: Wild data directory not found at '{wild_dir}'")
        return

    pokemon_list = get_pokemon_list(constants_file)
    if pokemon_list:
        print(f"Successfully loaded {len(pokemon_list)} Pokémon.")
        randomize_wild_files(wild_dir, pokemon_list)
        print("\nRandomization complete!")
        print("All wild Pokémon encounter files in 'data/wild/' have been updated.")

if __name__ == '__main__':
    main()
