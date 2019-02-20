# Import Python interface
from yggdrasil.interface import YggInput, YggOutput
# Import Python module containing model calculation
from shoot import calc_shoot_mass


# Create input/output channels
ShootGrowthRate = YggInput('shoot_growth_rate')
InitShootMass = YggInput('init_shoot_mass')
TimeStep = YggInput('shoot_time_step')
NextRootMass = YggInput('next_root_mass')
NextShootMass = YggOutput('next_shoot_mass', '%lf\n')

# Receive shoot growth rate
flag, r_s = ShootGrowthRate.recv()
if not flag:
    raise RuntimeError('shoot: Error receiving shoot growth rate.')
print('shoot: Received shoot growth rate: %s' % str(r_s))

# Receive initial shoot mass
flag, S_t = InitShootMass.recv()
if not flag:
    raise RuntimeError('shoot: Error receiving initial shootmass.')
print('shoot: Received initial shoot mass: %s' % str(S_t))

# Receive inital root mass
flag, R_t = NextRootMass.recv()
if not flag:
    raise RuntimeError('shoot: Error receiving initial root mass.')
print('shoot: Received initial root mass: %s' % str(R_t))

# Send initial shoot mass
flag = NextShootMass.send(S_t)
if not flag:
    raise RuntimeError('shoot: Error sending initial shoot mass.')

# Keep advancing until there arn't any new input times
i = 0
while True:
    
    # Receive the time step
    flag, dt = TimeStep.recv()
    if not flag:
        print('shoot: No more time steps.')
        break
    print('shoot: Received next time step: %s' % str(dt))

    # Receive the next root mass
    flag, R_tp1 = NextRootMass.recv()
    if not flag:
        # This raises an error because there must be a root mass for each time step
        raise RuntimeError('shoot: Error receiving root mass for timestep %d.' % (i + 1))
    print('shoot: Received next root mass: %s' % str(R_tp1))

    # Calculate shoot mass
    S_tp1 = calc_shoot_mass(r_s, dt, S_t, R_t, R_tp1)
    print('shoot: Calculated next shoot mass: %s' % str(S_tp1))

    # Output shoot mass
    flag = NextShootMass.send(S_tp1)
    if not flag:
        raise RuntimeError('shoot: Error sending shoot mass for timestep %d.' % (i + 1))

    # Advance masses to next timestep
    S_t = S_tp1
    R_t = R_tp1
    i += 1
