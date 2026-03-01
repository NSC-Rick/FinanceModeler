"""Fix indentation in financing_page.py for capital stack block."""

with open('ui/financing_page.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the capital stack block and add 4 spaces to all lines inside the expander
new_lines = []
in_expander = False
expander_indent = 0

for i, line in enumerate(lines):
    if 'with st.expander("💼 Acquisition Capital Stack' in line:
        in_expander = True
        expander_indent = len(line) - len(line.lstrip())
        new_lines.append(line)
    elif in_expander:
        # Check if we've exited the expander (back to original indent level or less)
        current_indent = len(line) - len(line.lstrip())
        
        # Exit condition: we hit the divider after the capital stack block
        if line.strip() == 'st.divider()' and i > 250:
            in_expander = False
            new_lines.append(line)
        # If line is inside expander but not indented enough, add 4 spaces
        elif line.strip() and current_indent == expander_indent + 4:
            new_lines.append('    ' + line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open('ui/financing_page.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fixed indentation in financing_page.py")
