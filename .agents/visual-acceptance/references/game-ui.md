# Game UI reference

Load when reviewing HUDs, menus, in-world interfaces or any UI that sits over
moving imagery. Game UI is judged in motion, against changing backgrounds, while
the player's attention is elsewhere — a static screenshot flatters it enormously.

## Review conditions

Judge against the worst realistic case, not a convenient one:

- brightest and darkest scene backgrounds the UI can appear over;
- highest visual-noise scene (particles, foliage, explosions, weather);
- during motion — capture mid-movement, not paused, wherever the engine allows;
- at the intended viewing distance (couch distance for console, not monitor distance).

If only static captures are possible, say so; readability conclusions from a paused
frame are weaker evidence and should be labelled as such.

## Checks

- **Readability against changing backgrounds** — does the element carry its own
  contrast (outline, shadow, scrim, backing plate), or does it rely on the scene
  happening to be dark?
- **Readability during motion** — thin strokes and low-contrast text disappear first.
- **HUD obstruction** — does any element cover the area the player must watch?
  Check the centre, the horizon line, and the direction of travel.
- **Gameplay priority** — critical information (health, ammo, objective, threat) must
  outrank cosmetic elements in visual weight. Verify the ranking matches the stakes.
- **Information density** — how much can be read in a half-second glance? Anything
  requiring sustained reading during play is misplaced.
- **Interaction feedback** — is every input acknowledged visually, and within a frame
  or two? Delayed feedback reads as an unresponsive game, not a slow UI.
- **Controller focus** — is the focused element unambiguous, and does focus movement
  follow spatial intuition? Test every direction from every element.
- **Animation distraction** — does anything animate in the periphery for no
  informational reason?
- **Diegetic consistency** — if the UI is in-world, does it stay in-world everywhere,
  or does it break the convention in one screen?
- **Safe area / title safe** — TV overscan still matters on console.
- **Localisation headroom** — will a string 40% longer still fit? German and Finnish
  routinely break HUD layouts designed against English.
- **Colour-blind safety** — team, threat and status colours must differ in value, not
  only hue. Desaturate the capture and re-check that the distinction survives.

## Scale

Downsample a capture to a quarter size and look again. If the hierarchy survives
and the critical values are still readable, it will survive a busy scene. If it
collapses, the design is relying on the reviewer's attention rather than the
player's.
