import sys, ast
sys.path.insert(0,'C:/g143/q/tools/gates')
import reachability as g1
fs={k:v for k,v in g1.read_tree('C:/g143/q','HEAD',g1.SOURCE_GLOBS).items() if g1._is_source(k)}
g1.G1_STATS.clear(); S=g1.SourceIndex(fs); n0=g1.G1_STATS['ast.parse']
p='skills/analog-gmid-design/assets/stick_diagram.py'
t1=S.tree(p); t2=S.tree(p); S.units(p); S.global_names(p); S.binding_origin(p,'os')
print('files',len(fs),'parse_at_index',n0,'parse_after',g1.G1_STATS['ast.parse'],'same_obj',t1 is t2, isinstance(t1,ast.Module), 'missing',S.tree('nope.py'))
print([u[1] for u in S.units(p) if u[0]=='stmt'][:3])
mv=g1.moved_defs(S,S); print('self-move', len(mv['units']), g1.G1_STATS['ast.parse'])
