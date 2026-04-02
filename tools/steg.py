#!/usr/bin/env python3
"""
steg.py — Interface principale stegg pour Claude Code

Usage:
    python tools/steg.py encode image.png "message secret" output.png
    python tools/steg.py decode output.png
    python tools/steg.py encode-secure image.png "message" output.png --password motdepasse
    python tools/steg.py analyze image.png
    python tools/steg.py text-encode "texte visible" "message caché" --method zero-width
    python tools/steg.py text-decode "texte avec invisible"
    python tools/steg.py capacity image.png
"""

import sys
import os
sys.path.insert(0, os.path.expanduser('~/.local/lib/python3.12/site-packages'))

import argparse
from pathlib import Path
from PIL import Image
from steg_core import encode, decode, StegConfig, Channel, EncodingStrategy


def cmd_encode(args):
    img = Image.open(args.input).convert("RGBA")
    config = StegConfig()
    data = args.message.encode("utf-8")
    result = encode(img, data, config, args.output)
    print(f"Encodé : {len(data)} bytes dans {args.output}")


def cmd_decode(args):
    img = Image.open(args.input)
    data = decode(img)
    print(data.decode("utf-8"))


def cmd_encode_secure(args):
    """LSB + AES-256-GCM via GHOST MODE (chiffrement + stéganographie)"""
    try:
        from stegg.crypto import encrypt_aes_gcm
        img = Image.open(args.input).convert("RGBA")
        encrypted = encrypt_aes_gcm(args.message.encode(), args.password)
        config = StegConfig(
            channels=[Channel.R, Channel.G, Channel.B],
            bits_per_channel=2,
            use_compression=True
        )
        result = encode(img, encrypted, config, args.output)
        print(f"Encodé + chiffré : {args.output}")
    except ImportError:
        # Fallback : chiffrement manuel AES-256-GCM
        import base64
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        import secrets as sec

        salt = sec.token_bytes(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000)
        key = kdf.derive(args.password.encode())
        aesgcm = AESGCM(key)
        nonce = sec.token_bytes(12)
        ciphertext = aesgcm.encrypt(nonce, args.message.encode(), None)
        payload = salt + nonce + ciphertext

        img = Image.open(args.input).convert("RGBA")
        config = StegConfig(
            channels=[Channel.R, Channel.G, Channel.B],
            bits_per_channel=2,
            use_compression=False
        )
        result = encode(img, payload, config, args.output)
        print(f"Encodé + chiffré AES-256-GCM : {args.output}")
        print(f"  Payload : {len(payload)} bytes")


def cmd_analyze(args):
    """Analyse une image pour détecter de la stéganographie"""
    img = Image.open(args.input)
    print(f"Image : {img.size[0]}x{img.size[1]} {img.mode}")
    print(f"Capacité LSB 1bit RGB : ~{(img.size[0] * img.size[1] * 3) // 8} bytes")
    print(f"Capacité LSB 2bit RGB : ~{(img.size[0] * img.size[1] * 3 * 2) // 8} bytes")

    # Tentative de décodage
    try:
        data = decode(img)
        if data and len(data) > 0:
            print(f"\n⚠️  Données détectées ! ({len(data)} bytes)")
            try:
                print(f"Texte : {data[:200].decode('utf-8')}")
            except UnicodeDecodeError:
                print(f"Binaire (hex) : {data[:32].hex()}...")
    except Exception as e:
        print(f"\nAucune donnée stegg standard détectée : {e}")


def cmd_capacity(args):
    """Calcule la capacité de stockage d'une image"""
    img = Image.open(args.input)
    w, h = img.size
    pixels = w * h
    print(f"Image : {w}x{h} = {pixels:,} pixels")
    print()
    print("Capacité par méthode :")
    print(f"  LSB 1bit/canal x1 (R)     : {pixels // 8:,} bytes = {pixels // 8 / 1024:.1f} KB")
    print(f"  LSB 1bit/canal x3 (RGB)   : {pixels * 3 // 8:,} bytes = {pixels * 3 // 8 / 1024:.1f} KB")
    print(f"  LSB 2bit/canal x3 (RGB)   : {pixels * 6 // 8:,} bytes = {pixels * 6 // 8 / 1024:.1f} KB")
    print(f"  LSB 4bit/canal x4 (RGBA)  : {pixels * 16 // 8:,} bytes = {pixels * 16 // 8 / 1024:.1f} KB")


# Stéganographie texte (zero-width, homoglyphes, etc.)
ZERO_WIDTH_CHARS = {
    '0': '\u200b',  # Zero Width Space
    '1': '\u200c',  # Zero Width Non-Joiner
}
ZERO_WIDTH_REVERSE = {v: k for k, v in ZERO_WIDTH_CHARS.items()}


def text_encode_zero_width(cover_text: str, secret: str) -> str:
    bits = ''.join(format(ord(c), '08b') for c in secret)
    hidden = ''.join(ZERO_WIDTH_CHARS[b] for b in bits)
    mid = len(cover_text) // 2
    return cover_text[:mid] + hidden + cover_text[mid:]


def text_decode_zero_width(steg_text: str) -> str:
    bits = ''
    for ch in steg_text:
        if ch in ZERO_WIDTH_REVERSE:
            bits += ZERO_WIDTH_REVERSE[ch]
    chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8)]
    return ''.join(chars)


def cmd_text_encode(args):
    method = getattr(args, 'method', 'zero-width')
    if method == 'zero-width':
        result = text_encode_zero_width(args.cover, args.secret)
        print(result)
        print(f"\n(longueur visible : {len(args.cover)} | longueur totale : {len(result)})", file=sys.stderr)
    else:
        print(f"Méthode '{method}' pas encore implémentée ici. Utiliser ste.gg", file=sys.stderr)
        sys.exit(1)


def cmd_text_decode(args):
    result = text_decode_zero_width(args.text)
    print(result)


def main():
    parser = argparse.ArgumentParser(description="Interface stegg")
    sub = parser.add_subparsers(dest="cmd")

    p_enc = sub.add_parser("encode", help="Encoder dans une image")
    p_enc.add_argument("input")
    p_enc.add_argument("message")
    p_enc.add_argument("output")

    p_dec = sub.add_parser("decode", help="Décoder depuis une image")
    p_dec.add_argument("input")

    p_sec = sub.add_parser("encode-secure", help="Encoder + chiffrer (AES-256-GCM)")
    p_sec.add_argument("input")
    p_sec.add_argument("message")
    p_sec.add_argument("output")
    p_sec.add_argument("--password", required=True)

    p_ana = sub.add_parser("analyze", help="Analyser une image")
    p_ana.add_argument("input")

    p_cap = sub.add_parser("capacity", help="Capacité de stockage d'une image")
    p_cap.add_argument("input")

    p_te = sub.add_parser("text-encode", help="Encoder dans du texte")
    p_te.add_argument("cover", help="Texte de couverture")
    p_te.add_argument("secret", help="Message secret")
    p_te.add_argument("--method", default="zero-width",
                      choices=["zero-width", "homoglyphs", "emoji-skin"])

    p_td = sub.add_parser("text-decode", help="Décoder depuis du texte")
    p_td.add_argument("text")

    args = parser.parse_args()

    dispatch = {
        "encode": cmd_encode,
        "decode": cmd_decode,
        "encode-secure": cmd_encode_secure,
        "analyze": cmd_analyze,
        "capacity": cmd_capacity,
        "text-encode": cmd_text_encode,
        "text-decode": cmd_text_decode,
    }

    if args.cmd in dispatch:
        dispatch[args.cmd](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
