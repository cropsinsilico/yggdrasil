import sys
# Import Python module containing model calculation
from shoot import calc_shoot_mass


# Create input/output channels
if len(sys.argv) != 6:
    raise RuntimeError("shoot: 5 input files and 1 output files are required.")
ShootGrowthRate = open(sys.argv[1], 'r')
InitShootMass = open(sys.argv[2], 'r')
TimeStep = open(sys.argv[3], 'r')
NextRootMass = open(sys.argv[4], 'r')
NextShootMass = open(sys.argv[5], 'w')

# Read shoot growth rate
flag = False
while True:
    line = ShootGrowthRate.readline()
    if len(line) == 0:
        break
    if line.startswith('#'):
        continue
    r_s = float(line)
    flag = True
    break
if not flag:
    raise RuntimeError('shoot: Error reading shoot growth rate.')
ShootGrowthRate.close()
print('shoot: Read shoot growth rate: %f' % r_s)

# Read initial shoot mass
flag = False
while True:
    line = InitShootMass.readline()
    if len(line) == 0:
        break
    if line.startswith('#'):
        continue
    S_t = float(line)
    flag = True
    break
if not flag:
    raise RuntimeError('shoot: Error reading initial shoot mass.')
InitShootMass.close()
print('shoot: Read initial shoot mass: %f' % S_t)

# Read inital root mass
flag = False
while True:
    line = NextRootMass.readline()
    if len(line) == 0:
        break
    if line.startswith('#'):
        continue
    R_t = float(line) / 1000.0  # Conversion to kg
    flag = True
    break
if not flag:
    raise RuntimeError('shoot: Error reading initial shoot mass.')
print('shoot: Read initial root mass: %f' % R_t)

# Write initial shoot mass
NextShootMass.write('# shoot_mass\n# %%lf\n%lf\n' % S_t)

# Keep advancing until there arn't any new input times
i = 0
while True:
    
    # Read the time step
    buff = TimeStep.readline()
    if buff.startswith('#'):
        continue
    if len(buff) == 0:
        print('shoot: No more time steps.')
        break
    dt = float(buff) / 24.0  # Conversion from hours to days
    print('shoot: Read next time step: %f' % dt)

    # Read the next root mass
    buff = NextRootMass.readline()
    if buff.startswith('#') or (len(buff) == 0):
        # This raises an error because there must be a root mass for each time step
        raise RuntimeError('shoot: Error reading root mass for timestep %d.' % (i + 1))
    R_tp1 = float(buff) / 1000.0  # Conversion to kg
    print('shoot: Read next root mass: %f' % R_tp1)

    # Calculate shoot mass
    S_tp1 = calc_shoot_mass(r_s, dt, S_t, R_t, R_tp1)
    print('shoot: Calculated next shoot mass: %f' % S_tp1)

    # Output shoot mass
    NextShootMass.write('%lf\n' % S_tp1)

    # Advance masses to next timestep
    S_t = S_tp1
    R_t = R_tp1
    i += 1
    # break  # Only for timing of a single loop
