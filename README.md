# Iolite Inlet

Full-colour **Python 3 + pygame** tide-hopper arcade for [ElbowOS](https://x.com/ElbowOS).
Hop a violet iolite skiff up drifting ice floes and amber barges. Scoop gold shards. Miss a pad and the inlet takes a life.

Featured: **https://x.com/ElbowOS**

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 iolite_inlet.py --play
```

Controls: **← →** drift on a pad, **SPACE / ↑** hop up, **↓** hop down, **R** reset, **Esc** quit.

## Record a 9:16 reel (headless)

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 iolite_inlet.py --record
```

Writes `/home/workdir/artifacts/IOLITE_INLET_ElbowOS.mp4` (1080×1920, 15s, 30fps, H.264).

## Links

- Reel on Drive: https://drive.google.com/file/d/1--jh4p0zbRXp7_U73jeANnvhN0VXsdGM/view?usp=drivesdk
- x.com/ElbowOS: https://x.com/ElbowOS
