from builtins import str
import random

def generate_nickname() -> str:
    """Generate a nickname that starts with a letter, followed by alphanumeric characters, underscores, or hyphens."""
    adjectives = ["clever", "jolly", "brave", "sly", "gentle"]
    animals = ["panda", "fox", "raccoon", "koala", "lion"]
    number = random.randint(0, 999)

    # Ensure the nickname starts with a letter
    adjective = random.choice(adjectives)
    animal = random.choice(animals)
    return f"{adjective}_{animal}_{number}"