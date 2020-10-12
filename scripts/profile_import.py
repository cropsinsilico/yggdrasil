import cProfile
import re
import pstats
cProfile.run('from yggdrasil.languages.Python import YggInterface', 'restats')
p = pstats.Stats('restats')
p.sort_stats('cumulative').print_stats(50)
