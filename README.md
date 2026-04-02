# stegg-lab

Exploration personnelle de la stéganographie avec [stegg](https://ste.gg) (v3.0).

## Ce qu'est la stéganographie

**Cacher que l'information existe** — contrairement au chiffrement qui cache son contenu.

Combinés, les deux offrent une sécurité maximale :
- Chiffrement → le message est illisible même si trouvé
- Stéganographie → personne ne cherche le message

## Usage personnel

- Stocker des données sensibles dans des images d'archives
- Envoyer des informations discrètes via canaux publics (email, réseaux sociaux)
- Projets artistiques : images qui contiennent des couches invisibles

## Installation

```bash
pip install stegg
```

## Méthodes disponibles

### Image

| Méthode | Description | Résiste compression JPEG ? |
|---------|-------------|---------------------------|
| **LSB** | 1 bit par canal dans les bits de poids faible | Non |
| **F5** | Coefficients DCT du JPEG | Oui |
| **PVD** | Différences entre paires de pixels | Partiellement |
| **CHROMA** | Canaux couleur Cb/Cr | Non |
| **SPECTER** | Saut entre canaux RGB (clé = pattern) | Non |
| **MATRYOSHKA** | Images dans images (jusqu'à 11 couches) | Non |
| **GHOST MODE** | AES-256-GCM + LSB + bruit décoy | Non |

### Texte (13 méthodes)

| Méthode | Principe |
|---------|----------|
| ZERO-WIDTH | Caractères invisibles entre les lettres |
| INVISIBLE INK | Unicode Tag Characters (U+E0000) |
| HOMOGLYPHS | 'a' → 'а' cyrillique (identique visuellement) |
| VARIATION SELECTORS | Modificateurs invisibles après caractères |
| COMBINING MARKS | Joiners invisibles |
| CONFUSABLE WHITESPACE | En-space/em-space/thin-space = bits |
| DIRECTIONAL OVERRIDES | Caractères bidi invisibles |
| HANGUL FILLER | Caractère coréen invisible |
| MATH BOLD | 'a' → '𝐚' (aspect gras, encodage différent) |
| BRAILLE | Chaque octet = motif braille |
| EMOJI SUBSTITUTION | 🔵=0, 🔴=1 |
| EMOJI SKIN TONE | 4 modificateurs = 2 bits chacun |

## Utilisation CLI

```bash
# Encoder un message dans une image
stegg encode-cmd --input image.png --message "secret" --output out.png

# Décoder
stegg decode-cmd --input out.png

# Analyser une image (est-ce qu'elle cache quelque chose ?)
stegg analyze --input image.png
```

## Utilisation Python (API)

Voir `tools/` pour des scripts prêts à l'emploi.

```python
from PIL import Image
from steg_core import encode, decode, StegConfig

# Encoder
img = Image.open("carrier.png")
config = StegConfig()  # LSB RGB par défaut
result = encode(img, b"message secret", config, "output.png")

# Décoder
decoded = decode(Image.open("output.png"))
print(decoded)
```

## Structure du repo

```
stegg-lab/
├── docs/          # Documentation des méthodes
├── examples/      # Fichiers exemples (non inclus dans git)
├── tools/         # Scripts Python
└── art/           # Expérimentations artistiques
```

## Projets artistiques

→ voir `art/README.md`
