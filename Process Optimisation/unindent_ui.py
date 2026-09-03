import sys
file_path = r'c:\Users\HP\Desktop\Process Optimisation\Epoxy_myselate.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_global_block = False
for i, line in enumerate(lines):
    if 'st.subheader("📄 Upload Global Process Document (ROS)")' in line:
        # found the global block
        # the previous line should be 'st.markdown("---")'
        # let's go back and turn on unindenting for that line as well
        if i > 0 and 'st.markdown("---")' in lines[i-1]:
            if new_lines[-1].startswith('    '):
                new_lines[-1] = new_lines[-1][4:]
            
        in_global_block = True
    
    if 'st.header("🤖 AI Analysis & Chat")' in line:
        in_global_block = False
        
    if in_global_block:
        if line.startswith('    '):
            new_lines.append(line[4:])
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done!')
