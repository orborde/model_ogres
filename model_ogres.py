# We almost died fighting some ogres! That was pretty scary. Let's
# simulate that encounter a few zillion times to see how likely it was
# that we'd have died (assuming we were stupid, which we kinda were).

import collections
import random

def dN(n):
    return random.randint(1, n)
d4 = lambda: dN(4)
d6 = lambda: dN(6)
d8 = lambda: dN(8)
d10 = lambda: dN(10)
d20 = lambda: dN(20)

# damage is a function that returns a value when called.
# crit_min is an int representing the attack roll for a critical hit.
# crit_mult is the number to multiply damage by on a critical.
Weapon = collections.namedtuple(
    'Weapon', ['name', 'damage', 'crit_min', 'crit_mult'])

LightCrossbow = Weapon('Light Crossbow', d8, 19, 2)
Scimitar = Weapon('Scimitar', d6, 18, 2)
ShortSpear = Weapon('Short Spear', d6, 20, 2)
BastardSword = Weapon('Bastard Sword', d10, 19, 2)
GreatClub = Weapon('Great Club', lambda: d8()+d8()+7, 20, 2)

mansattrs = ['name', 'weapon', 'initiative_mod', 'hp', 'ac',
             'atk_bonus', 'dmg_bonus', 'attacks_per_round']
def Mans(*arg):
    assert len(arg) == len(mansattrs)
    return dict(zip(mansattrs, arg))

def is_active(mans):
    return mans['hp'] > 0

def roll_initiative(mod):
    return d10() + mod


def run_match(PRINT=True):
    players = [
        #                             I  HP  AC ATK DMG APR
        Mans('Jimmy',  LightCrossbow, 4, 10, 16,  7,  1,  1),
        Mans('Erie',   Scimitar,      1, 16, 13,  0,  0,  1),
        Mans('SaucyD', LightCrossbow, 2, 12, 15,  5,  0,  1),
        Mans('Sully',  ShortSpear,    2, 16, 12,  2,  0,  2),
        # Forgot to write down Lancelot's STR mod :(. Guessing it's 2?
        Mans('Lance',  BastardSword,  1, 28, 15,  6,  2,  1)
    ]

    # TODO: Vary the enemy stats across runs, since they're random.
    badguys = [
        # Attack mod differs from the one in the SRD.
        Mans('Ogre %d' % i, GreatClub, -1,
             d8()+d8()+d8()+d8()+11,
             16, 7, 0, 1)
        for i in range(1, 4+1)
    ]

    def run_turn():
        initiatives = collections.defaultdict(list)
        for mans in players + badguys:
            roll = roll_initiative(mans['initiative_mod'])
            initiatives[roll].append(mans)

        # TODO: Make all the enemies act at once?
        init_order = sorted(initiatives.keys(), reverse=True)
        if PRINT:
            print 'Initiative order:'
            for t in init_order:
                print '%5d:' % t, ', '.join(
                    '%s (%d)' % (m['name'], m['hp'])
                    for m in initiatives[t])

        # Process actual actions. They're all attacks.
        for t in init_order:
            # Keep a queue of damages to apply at the end of each
            # initiative order, since a mans acting at the same time as
            # the person who strikes them down will still get an attack
            # off. This also has the helpful property that there's a
            # simple place to put all the "he dies" logic.
            damages = []
            for mans in initiatives[t]:
                # Incapacitated people can't do anything.
                if mans['hp'] <= 0:
                    # TODO: Bleedout?
                    if PRINT:
                        print mans['name'], 'is down for the count.'
                    continue

                # Select an active target at random.
                # TODO: See what happens if we do intelligently
                # concentrated fire.
                if mans in badguys:
                    enemies = players
                else:
                    enemies = badguys
                enemies = [e for e in enemies if is_active(e)]
                if not enemies:
                    if PRINT:
                        print mans['name'], 'twiddles their thumbs.'
                    continue
                target = random.choice(enemies)

                # Try to attack it.
                for i in range(mans['attacks_per_round']):
                    base_roll = d20()
                    base_damage = mans['weapon'].damage() + mans['dmg_bonus']
                    if PRINT:
                        print mans['name'], 'attacks', target['name'],
                        print 'with their', mans['weapon'].name,
                        print '(%d + %d vs %d)' % (
                            base_roll, mans['atk_bonus'], target['ac']),
                        print 'and',
                    if base_roll >= mans['weapon'].crit_min:
                        if PRINT:
                            print 'scores a CRITICAL HIT!',
                            print '(%dx%d)' % (base_damage,
                                               mans['weapon'].crit_mult)
                        damages.append(
                            (target, base_damage * mans['weapon'].crit_mult))
                    elif base_roll + mans['atk_bonus'] >= target['ac']:
                        if PRINT:
                            print 'scores a hit!'
                        damages.append((target, base_damage))
                    else:
                        if PRINT:
                            print 'misses.'

                # Apply damages.
                for mans, damage in damages:
                    was_active = is_active(mans)
                    mans['hp'] -= damage
                    if PRINT:
                        print mans['name'], 'takes', damage,
                        print 'damage and is now at', mans['hp'], 'HP.'
                        if was_active and not is_active(mans):
                            print mans['name'], 'has died.'

    turn = 0
    while (any(is_active(m) for m in players) and
           any(is_active(m) for m in badguys)):
        turn += 1
        if PRINT:
            print '=== TURN %d ===' % turn
        run_turn()

    players_left = any(is_active(m) for m in players)
    badguys_left = any(is_active(m) for m in badguys)
    if PRINT:
        if not players_left:
            print 'Players are ALL DEAD.'
        if not badguys_left:
            print 'Monsters have all died.'

    return players_left, badguys_left

import sys
if len(sys.argv) > 1:
    RUNS = int(sys.argv[1])
    wins = 0
    losses = 0
    ties = 0
    for i in range(RUNS):
        p, m = run_match(PRINT=False)
        assert not (p and m)
        if p == m:
            ties += 1
        elif p:
            wins += 1
        elif m:
            losses += 1

    print wins, losses, ties
else:
    p, m = run_match(PRINT=True)
    assert not (p and m)

    
