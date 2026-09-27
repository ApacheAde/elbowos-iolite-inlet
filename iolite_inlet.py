#!/usr/bin/env python3
"""Iolite Inlet — neon tide-hopper arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "IOLITE INLET"
HANDLE = "x.com/ElbowOS"
NAVY, INK = (8, 10, 28), (236, 240, 255)
VIOLET, LILAC = (132, 72, 255), (196, 164, 255)
CYAN, ICE = (48, 230, 255), (180, 250, 255)
GOLD, AMBER = (255, 210, 72), (255, 156, 48)
ROSE, TEAL = (255, 88, 148), (48, 220, 176)
ROW_H = 148
ROWS = 9
PLAY_TOP = 280
PLAY_BOT = PLAY_TOP + ROWS * ROW_H


class Pad:
    __slots__ = ("row", "x", "w", "vx", "kind")

    def __init__(self, row, x, w, vx, kind):
        self.row, self.x, self.w, self.vx, self.kind = row, x, w, vx, kind


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=5):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 64)
        self.font_md = pygame.font.Font(None, 44)
        self.font_sm = pygame.font.Font(None, 32)
        self.reset()

    def reset(self) -> None:
        self.row = 0
        self.px = W * 0.5
        self.score = 0
        self.lives = 3
        self.cool = 0.0
        self.pulse = 0.0
        self.hop_t = 0.0
        self.from_x = self.px
        self.from_row = 0
        self.pads: list[Pad] = []
        self.sparks: list[Spark] = []
        self.shards: list[tuple[float, int]] = []
        self.over = False
        self.shake = 0.0
        self.seed_rows()

    def row_y(self, row: int) -> float:
        return PLAY_BOT - row * ROW_H - ROW_H * 0.5

    def seed_rows(self) -> None:
        self.pads.clear()
        self.shards.clear()
        for r in range(ROWS):
            if r == 0:
                self.pads.append(Pad(0, W * 0.5, 420, 0.0, "dock"))
                continue
            n = 3
            kind = "ice" if r % 2 else "barge"
            vx = (70 + r * 8) * (1 if r % 2 else -1)
            gap = W / n
            for i in range(n):
                w = random.uniform(210, 300)
                x = (i + 0.5) * gap + random.uniform(-20, 20)
                self.pads.append(Pad(r, x, w, vx, kind))
            if r > 1 and random.random() < 0.7:
                self.shards.append((random.uniform(180, W - 180), r))

    def burst(self, x, y, col, n=12) -> None:
        for _ in range(n):
            a = random.random() * 6.283
            s = random.uniform(70, 320)
            self.sparks.append(
                Spark(x, y, s * math.cos(a), s * math.sin(a),
                      random.uniform(0.2, 0.55), col, random.randint(3, 8))
            )

    def pads_on(self, row: int) -> list[Pad]:
        return [p for p in self.pads if p.row == row]

    def standing(self) -> Pad | None:
        for p in self.pads_on(self.row):
            if abs(self.px - p.x) < p.w * 0.5 + 6:
                return p
        return None

    def hop(self, direction: int) -> None:
        if self.cool > 0 or self.over or self.hop_t > 0:
            return
        nxt = self.row + direction
        if nxt < 0 or nxt >= ROWS:
            return
        self.from_x, self.from_row = self.px, self.row
        self.row = nxt
        self.hop_t = 1.0
        self.cool = 0.12
        self.burst(self.px, self.row_y(self.from_row), LILAC, 8)

    def drown(self) -> None:
        self.lives -= 1
        self.shake = 0.4
        self.burst(self.px, self.row_y(self.row), ROSE, 22)
        if self.lives <= 0:
            self.over = True
            self.cool = 1.6
        else:
            self.row, self.px = 0, W * 0.5
            self.hop_t = 0.0

    def autoplay(self) -> None:
        if self.over:
            if self.cool <= 0:
                self.reset()
            return
        if self.hop_t > 0:
            return
        target = min(ROWS - 1, self.row + 1)
        best, best_d = None, 1e9
        for p in self.pads_on(target):
            pred = p.x + p.vx * 0.18
            d = abs(pred - self.px)
            if d < best_d:
                best, best_d = p, d
        if best is None:
            return
        if best.x > self.px + 8:
            self.px = min(W - 60, self.px + 14)
        elif best.x < self.px - 8:
            self.px = max(60, self.px - 14)
        if best_d < best.w * 0.42:
            self.hop(+1)

    def update(self, dt: float) -> None:
        self.pulse += dt
        self.cool = max(0.0, self.cool - dt)
        self.shake = max(0.0, self.shake - dt)
        if self.record:
            self.autoplay()
        for p in self.pads:
            if p.kind == "dock":
                continue
            p.x += p.vx * dt
            half = p.w * 0.5
            if p.x < -half:
                p.x = W + half
            elif p.x > W + half:
                p.x = -half
        if self.hop_t > 0:
            self.hop_t = max(0.0, self.hop_t - dt * 5.2)
            t = 1.0 - self.hop_t
            self.px = self.from_x + (self._aim_x() - self.from_x) * t
        else:
            pad = self.standing()
            if pad is None and not self.over:
                self.drown()
            elif pad is not None:
                self.px += pad.vx * dt
                self.px = max(40, min(W - 40, self.px))
        keep_sh = []
        for x, r in self.shards:
            if r == self.row and abs(x - self.px) < 46 and self.hop_t <= 0:
                self.score += 35
                self.burst(x, self.row_y(r), GOLD, 16)
            else:
                keep_sh.append((x, r))
        self.shards = keep_sh
        if self.row == ROWS - 1 and self.hop_t <= 0 and not self.over:
            self.score += 120
            self.burst(self.px, self.row_y(self.row), CYAN, 28)
            self.row, self.px = 0, W * 0.5
            self.seed_rows()
        alive = []
        for sp in self.sparks:
            sp.life -= dt
            if sp.life <= 0:
                continue
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            sp.vy += 240 * dt
            alive.append(sp)
        self.sparks = alive

    def _aim_x(self) -> float:
        pads = self.pads_on(self.row)
        if not pads:
            return self.px
        return min(pads, key=lambda p: abs(p.x - self.px)).x

    def handle(self, ev) -> None:
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
            self.hop(+1)
        elif ev.key in (pygame.K_DOWN, pygame.K_s):
            self.hop(-1)
        elif ev.key in (pygame.K_LEFT, pygame.K_a):
            self.px = max(50, self.px - 70)
        elif ev.key in (pygame.K_RIGHT, pygame.K_d):
            self.px = min(W - 50, self.px + 70)
        elif ev.key == pygame.K_r:
            self.reset()

    def draw(self, s: pygame.Surface) -> None:
        s.fill(NAVY)
        ox = int(math.sin(self.pulse * 38) * 12 * self.shake)
        for i in range(22):
            y = int((self.pulse * 55 + i * 96) % (H + 30)) - 15
            pygame.draw.line(s, (16, 18, 48), (0, y), (W, y), 2)
        pygame.draw.rect(s, (14, 16, 44), (20, PLAY_TOP - 16, W - 40, PLAY_BOT - PLAY_TOP + 32), border_radius=26)
        pygame.draw.rect(s, VIOLET, (20, PLAY_TOP - 16, W - 40, PLAY_BOT - PLAY_TOP + 32), 3, border_radius=26)
        for r in range(ROWS):
            y = int(self.row_y(r))
            tint = (22, 18, 52) if r % 2 else (18, 22, 50)
            pygame.draw.rect(s, tint, (36, y - ROW_H // 2 + 8, W - 72, ROW_H - 16), border_radius=12)
        for p in self.pads:
            y = int(self.row_y(p.row))
            col = GOLD if p.kind == "dock" else (ICE if p.kind == "ice" else AMBER)
            rect = pygame.Rect(int(p.x - p.w * 0.5) + ox, y - 28, int(p.w), 56)
            pygame.draw.rect(s, col, rect, border_radius=18)
            pygame.draw.rect(s, INK, rect, 2, border_radius=18)
            if p.kind != "dock":
                pygame.draw.circle(s, (255, 255, 255), (int(p.x) + ox, y), 7)
        for x, r in self.shards:
            y = int(self.row_y(r))
            pygame.draw.polygon(
                s, GOLD,
                [(int(x) + ox, y - 18), (int(x) + 14 + ox, y), (int(x) + ox, y + 18), (int(x) - 14 + ox, y)],
            )
        t = self.hop_t
        py = self.row_y(self.row)
        if t > 0:
            py = self.row_y(self.from_row) + (self.row_y(self.row) - self.row_y(self.from_row)) * (1 - t)
            py -= math.sin((1 - t) * math.pi) * 36
        px = int(self.px) + ox
        pygame.draw.circle(s, VIOLET, (px, int(py)), 30)
        pygame.draw.circle(s, CYAN, (px, int(py)), 16)
        pygame.draw.circle(s, INK, (px - 6, int(py) - 4), 4)
        pygame.draw.circle(s, INK, (px + 6, int(py) - 4), 4)
        for sp in self.sparks:
            pygame.draw.circle(s, sp.col, (int(sp.x) + ox, int(sp.y)), max(1, int(sp.r * sp.life * 2)))
        title = self.font_lg.render(TITLE, True, CYAN)
        s.blit(title, title.get_rect(center=(W // 2, 78)))
        handle = self.font_sm.render(HANDLE, True, LILAC)
        s.blit(handle, handle.get_rect(center=(W // 2, 128)))
        meta = self.font_md.render(f"SCORE  {self.score}    LIVES  {max(0, self.lives)}", True, GOLD)
        s.blit(meta, meta.get_rect(center=(W // 2, 188)))
        hint = self.font_sm.render("\u2190 \u2192 drift   SPACE hop   R reset", True, TEAL)
        s.blit(hint, hint.get_rect(center=(W // 2, H - 48)))
        if self.over:
            over = self.font_md.render("SWEPT OUT TO SEA", True, ROSE)
            s.blit(over, over.get_rect(center=(W // 2, 232)))

    def play(self) -> None:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle(ev)
            keys = pygame.key.get_pressed()
            if self.hop_t <= 0 and not self.over:
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.px = max(50, self.px - 420 * dt)
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.px = min(W - 50, self.px + 420 * dt)
            self.update(dt)
            self.draw(self.surf)
            screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    play = "--play" in sys.argv
    if record or not play:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record or not play)
    if record or not play:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/IOLITE_INLET_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
