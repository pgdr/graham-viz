"""Minimal pygame visualization of Graham scan."""

import random
import sys
import pygame

from graham_scan import Point, graham as original_graham, right as original_right

N = 50
FPS = 10
WIDTH, HEIGHT = 1200, 900
MARGIN = 70
SEED = 7


class Step:
    def __init__(
        self,
        kind,
        phase,
        message,
        stack,
        lower_hull,
        final_hull,
        a=None,
        b=None,
        c=None,
    ):
        self.kind = kind
        self.phase = phase
        self.message = message
        self.stack = stack
        self.lower_hull = lower_hull
        self.final_hull = final_hull
        self.a = a
        self.b = b
        self.c = c


def make_points(n, seed):
    rng = random.Random(seed)
    points = []
    for idx in range(n):
        points.append(Point(rng.random(), rng.random(), idx))
    return points


def graham_injected(points, right_fn, on_stack_change, on_finish):
    """Callback-injected copy of graham_scan.graham()."""
    points = sorted(set(points))
    S, hull = [], []

    on_stack_change(S, "lower hull", "start lower pass")
    for p in points:
        while len(S) >= 2 and right_fn(S[-2], S[-1], p, S, "lower hull"):
            popped = S.pop()
            on_stack_change(S, "lower hull", f"pop {int(popped.idx)}")
        S.append(p)
        on_stack_change(S, "lower hull", f"push {int(p.idx)}")
    hull += S

    S = []
    on_stack_change(S, "upper hull", "start upper pass")
    for p in reversed(points):
        while len(S) >= 2 and right_fn(S[-2], S[-1], p, S, "upper hull"):
            popped = S.pop()
            on_stack_change(S, "upper hull", f"pop {int(popped.idx)}")
        S.append(p)
        on_stack_change(S, "upper hull", f"push {int(p.idx)}")
    hull += S[1:-1]

    on_finish(hull)
    return hull


def build_steps(points):
    steps = []
    lower_hull = []

    def emit_stack(S, phase, message):
        nonlocal lower_hull
        if phase == "upper hull" and not lower_hull:
            lower_hull = steps[-1].stack[:] if steps else []

        steps.append(
            Step(
                kind="stack",
                phase=phase,
                message=message,
                stack=S[:],
                lower_hull=lower_hull[:],
                final_hull=[],
            )
        )

    def injected_right(a, b, c, S, phase):
        result = original_right(a, b, c)
        steps.append(
            Step(
                kind="right",
                phase=phase,
                message=f"right({int(a.idx)}, {int(b.idx)}, {int(c.idx)}) -> {result}",
                stack=S[:],
                lower_hull=lower_hull[:],
                final_hull=[],
                a=a,
                b=b,
                c=c
            )
        )
        return result

    def finish(hull):
        steps.append(
            Step(
                kind="done",
                phase="done",
                message="convex hull complete",
                stack=[],
                lower_hull=[],
                final_hull=hull[:],
            )
        )

    hull = graham_injected(
        points,
        right_fn=injected_right,
        on_stack_change=emit_stack,
        on_finish=finish,
    )

    assert hull == original_graham(points)
    return steps, hull


def screen_pos(p):
    x = MARGIN + int(p.x * (WIDTH - 2 * MARGIN))
    y = HEIGHT - MARGIN - int(p.y * (HEIGHT - 2 * MARGIN))
    return x, y


def draw_polyline(screen, points, color, width=3, closed=False):
    if len(points) < 2:
        return
    coords = [screen_pos(p) for p in points]
    pygame.draw.lines(screen, color, closed, coords, width)


def draw_points(screen, points, font, highlighted=None):
    highlighted = highlighted or {}

    for p in points:
        pos = screen_pos(p)
        label, color = highlighted.get(p, ("", (35, 35, 35)))
        radius = 11 if p in highlighted else 5
        pygame.draw.circle(screen, color, pos, radius)
        text = font.render(str(int(p.idx)) + label, True, color)
        screen.blit(text, (pos[0] + 8, pos[1] - 8))


def draw_step(screen, points, step, index, count, font, big_font):
    screen.fill((248, 248, 248))

    if step.lower_hull:
        draw_polyline(screen, step.lower_hull, (170, 170, 170), width=3)

    if step.stack:
        draw_polyline(screen, step.stack, (30, 90, 180), width=4)

    if step.final_hull:
        draw_polyline(screen, step.final_hull, (20, 120, 60), width=5, closed=True)

    highlighted = {}
    if step.kind == "right" and step.a and step.b and step.c:
        highlighted = {
            step.a: (" a", (220, 70, 70)),
            step.b: (" b", (60, 130, 220)),
            step.c: (" c", (40, 160, 80)),
        }
        pygame.draw.lines(
            screen,
            (120, 120, 120),
            False,
            [screen_pos(step.a), screen_pos(step.b), screen_pos(step.c)],
            2,
        )

    draw_points(screen, points, font, highlighted)

    title = big_font.render("Graham scan visualization", True, (20, 20, 20))
    screen.blit(title, (25, 20))

    status = font.render(f"step {index + 1}/{count} | {step.phase}", True, (20, 20, 20))
    screen.blit(status, (25, 55))

    msg = font.render(step.message, True, (20, 20, 20))
    screen.blit(msg, (25, 82))

    legend = [
        "2 FPS autoplay",
        "blue polyline = current stack S",
        "gray polyline = completed lower hull",
        "green polygon = final hull",
        "a,b,c are drawn whenever right(a,b,c) is called",
        "Space: pause/resume | </>: step | R: regenerate points",
    ]

    for i, line in enumerate(legend):
        screen.blit(font.render(line, True, (65, 65, 65)), (25, HEIGHT - 145 + 22 * i))


def main_loop(screen, points, steps, font, big_font, clock, seed):
    step_index = 0
    paused = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_RIGHT:
                    paused = True
                    step_index = min(step_index + 1, len(steps) - 1)
                elif event.key == pygame.K_LEFT:
                    paused = True
                    step_index = max(step_index - 1, 0)
                elif event.key == pygame.K_r:
                    seed += 1
                    points = make_points(N, seed)
                    steps, _ = build_steps(points)
                    step_index = 0
                    paused = False
                elif event.key == pygame.K_q:
                    running = False

        draw_step(
            screen,
            points,
            steps[step_index],
            step_index,
            len(steps),
            font,
            big_font,
        )

        pygame.display.flip()

        if not paused:
            step_index = min(step_index + 1, len(steps) - 1)

        clock.tick(FPS)


def run():
    pygame.init()
    pygame.display.set_caption("Graham scan")

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    font = pygame.font.SysFont(None, 22)
    big_font = pygame.font.SysFont(None, 32)
    clock = pygame.time.Clock()

    seed = SEED
    points = make_points(N, seed)
    steps, _ = build_steps(points)

    main_loop(screen, points, steps, font, big_font, clock, seed)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
