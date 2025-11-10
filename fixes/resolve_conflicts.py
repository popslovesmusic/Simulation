#!/usr/bin/env python
import sys

def resolve_conflicts(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    resolved = []
    in_conflict = False
    in_ours = False
    in_theirs = False
    theirs_content = []
    
    for line in lines:
        if line.startswith('<<<<<<< ours'):
            in_conflict = True
            in_ours = True
            continue
        elif line.startswith('======='):
            in_ours = False
            in_theirs = True
            continue
        elif line.startswith('>>>>>>> theirs'):
            # End of conflict, keep theirs content
            resolved.extend(theirs_content)
            theirs_content = []
            in_conflict = False
            in_theirs = False
            continue
        
        if in_conflict:
            if in_theirs:
                theirs_content.append(line)
            # Skip ours content
        else:
            resolved.append(line)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(resolved)
    
    print("Resolved conflicts in " + filename)

if __name__ == '__main__':
    resolve_conflicts('dase_cli/src/engine_manager.cpp')
    resolve_conflicts('dase_cli/src/command_router.cpp')
    print("Done! All conflicts resolved.")
