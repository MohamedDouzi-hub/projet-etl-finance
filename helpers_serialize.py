import json
import os.path
from typing import Dict

import tomli  # pour lire les fichiers TOML
import toml   # pour écrire les fichiers TOML
import yaml   # pour YAML


def get_serialized_data(path: str) -> Dict:
    """
    Charge et désérialise les données depuis un fichier .yaml, .json ou .toml
    Retourne un dictionnaire utilisable pour la configuration du projet.
    """
    _, extension = os.path.splitext(path)

    with open(path, mode="rb") as file:
        if extension in [".yaml", ".yml"]:
            return yaml.load(file, Loader=yaml.FullLoader)
        elif extension == ".json":
            return json.load(file)
        elif extension == ".toml":
            return tomli.load(file)

        raise ValueError(f"Unsupported file extension {extension} | file={path}")


def dict_to_serialized_file(data: Dict, path: str) -> None:
    """
    Sérialise un dictionnaire Python et écrit dans un fichier .yaml, .json ou .toml
    Utilisé pour enregistrer des configurations ou résultats de façon structurée.
    """
    _, extension = os.path.splitext(path)

    with open(path, mode="w") as file:
        if extension in [".yaml", ".yml"]:
            yaml.dump(data, file)
        elif extension == ".json":
            json.dump(data, file, indent=4)
        elif extension == ".toml":
            toml.dump(data, file)
        else:
            raise ValueError(f"Unsupported file extension {extension} | file={path}")
