import logging
import sys

# === 1. Créer un logger personnalisé === #
logger = logging.getLogger(__name__)

# === 2. Créer un ou plusieurs handler === #
# Diriger les logs vers "standard output"
stream_handler = logging.StreamHandler(sys.stdout)
# Diriger les logs vers un fichier
file_handler = logging.FileHandler('bs4Scrap.log', mode="w")

# === 3. Ajouter les handlers au logger === #
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# === 4. Choisir un niveau de journalisation minimum === #
logger.setLevel(logging.DEBUG)

# === 5. Définir le format des logs === #
# Définir un format pour la console
stream_format = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')

# Définir un autre format pour le fichier
file_format = logging.Formatter('[%(asctime)s] [%(levelname)s] %(name)s: #%(lineno)d - %(message)s')

# Associer les formats au handlers
stream_handler.setFormatter(stream_format)
file_handler.setFormatter(file_format)