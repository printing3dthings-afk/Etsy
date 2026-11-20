"""Lesson 008 carousel: five 1080 x 1350 slides cut from the video's own stills, with
Lesson 007's layout (explained_lesson007/carousel.py).

    python3 carousel.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "explained_lesson007"))
from carousel import main  # noqa: E402

if __name__ == "__main__":
    main(HERE, "008", ["5.6", "9.8", "21.0", "25.8", "41.2"])
