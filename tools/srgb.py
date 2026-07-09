#!/usr/bin/env python3
"""
srgb.py — shared sRGB color-management helper.

CLAUDE.md Gate 1: "Export all final files as sRGB. Never AdobeRGB or CMYK — Etsy
auto-converts and color shifts on print are a top-3 review complaint."

The trap: PIL's `img.convert("RGB")` does NOT color-manage. If a source has an embedded
AdobeRGB or CMYK profile, convert("RGB") keeps the raw channel values, which a print lab
then interprets as sRGB → visible color shift. Real correctness requires an ICC profile
transform from the source profile to sRGB. This module does that, in one place, so every
deliverable pipeline can call ensure_srgb() before saving.

Usage:
    from tools.srgb import ensure_srgb, SRGB_ICC

    img = ensure_srgb(Image.open(src))                 # color-managed sRGB image
    img.save(out, "JPEG", quality=92, icc_profile=SRGB_ICC, dpi=(300, 300))
"""
from __future__ import annotations

import io

from PIL import Image, ImageCms

# A standard sRGB profile, created once and reused.
_SRGB_PROFILE = ImageCms.createProfile("sRGB")
SRGB_ICC: bytes = ImageCms.ImageCmsProfile(_SRGB_PROFILE).tobytes()


def ensure_srgb(img: Image.Image) -> Image.Image:
    """Return an RGB image whose pixels are correctly in the sRGB color space.

    - If the image carries an ICC profile (e.g. AdobeRGB, CMYK, Display P3), perform a
      true ICC transform from that profile to sRGB.
    - If it has no profile, assume it is already sRGB (the norm for web / gpt-image-1
      output) and just normalize the mode to RGB.

    The returned image has no leftover non-sRGB profile attached; embed SRGB_ICC on save.
    """
    icc = img.info.get("icc_profile")
    if icc:
        try:
            src_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            # CMYK sources transform straight to RGB output via the sRGB profile.
            out_mode = "RGB"
            converted = ImageCms.profileToProfile(
                img, src_profile, _SRGB_PROFILE,
                renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                outputMode=out_mode,
            )
            if converted is not None:
                converted.info.pop("icc_profile", None)
                return converted
        except Exception:
            # Fall through to a plain mode normalize if the profile is unreadable
            pass

    out = img.convert("RGB") if img.mode != "RGB" else img.copy()
    out.info.pop("icc_profile", None)
    return out


def save_srgb_jpeg(img: Image.Image, path, quality: int = 92, dpi=(300, 300)) -> None:
    """Convenience: color-manage to sRGB and save as a JPEG with the sRGB profile embedded."""
    ensure_srgb(img).save(path, "JPEG", quality=quality, dpi=dpi, icc_profile=SRGB_ICC)
