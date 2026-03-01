"""
Fix indentation for Capital Stack section in financing_page.py
Wraps the entire Capital Stack expander block in Advanced mode conditional.
"""

def fix_indentation():
    filepath = 'ui/financing_page.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    in_capital_stack = False
    capital_stack_start = None
    capital_stack_end = None
    
    # Find the Capital Stack section boundaries
    for i, line in enumerate(lines):
        if 'with st.expander("💼 Acquisition Capital Stack' in line:
            capital_stack_start = i
            in_capital_stack = True
        elif in_capital_stack and 'st.rerun()' in line:
            capital_stack_end = i
            in_capital_stack = False
            break
    
    if capital_stack_start is None or capital_stack_end is None:
        print("ERROR: Could not find Capital Stack section boundaries")
        return False
    
    print(f"Capital Stack section: lines {capital_stack_start + 1} to {capital_stack_end + 1}")
    
    # Rebuild the file
    for i, line in enumerate(lines):
        if i == capital_stack_start - 2:
            # Add the conditional before "# Capital Stack Advisory Layer"
            new_lines.append(line)  # Keep the comment line
        elif i == capital_stack_start - 1:
            # This is the "# Capital Stack Advisory Layer" comment
            new_lines.append("    # Capital Stack Advisory Layer (Collapsible) - Advanced Mode Only\n")
            new_lines.append("    if st.session_state.mode == \"Advanced\":\n")
        elif capital_stack_start <= i <= capital_stack_end:
            # Indent these lines by 4 additional spaces
            if line.strip():  # Not an empty line
                new_lines.append('    ' + line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ Successfully wrapped Capital Stack in Advanced mode conditional")
    print(f"   Indented lines {capital_stack_start + 1} to {capital_stack_end + 1}")
    return True

if __name__ == '__main__':
    success = fix_indentation()
    exit(0 if success else 1)
