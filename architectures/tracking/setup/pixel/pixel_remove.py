# vertex-ai-mlops/architectures/tracking/setup/pixel/pixel_remove.py
# this file, pixel_remove.py, will remove the tracking from files in the repository
# to see files this will impact, first run pixel_list.py

import os
import json

# this file is in: vertex-ai-mlops/architectures/tracking/setup/pixel/pixel_remove.py
for root, dirs, files in os.walk('../../../../.'):
    for file in files:
        if file.endswith(('.md', '.ipynb')) and not root.endswith('.ipynb_checkpoints'):
            print('Evaluating: ', os.path.join(root, file))
            
            if file.endswith('.md'):
                update = False
                
                # read file contents
                with open(os.path.join(root, file), 'r') as reader:
                    content = reader.readlines()
                
                # check for pixel track
                if content[0].startswith('![tracker](https://'):
                    content = content[1:]
                    update = True
                    # remove any blank lines at the start of the file (these were empty spaces/lines after the tracker)
                    while True:
                        if content[0] == '\n':
                            content = content[1:]
                        else:
                            break
                    
                # update files with pixel track - remove the tracking
                if update:
                    print('Remove tracking from: ', file)
                    with open(os.path.join(root, file), 'w') as writer:
                        writer.writelines(content)
                    
            elif file.endswith('.ipynb'):
                update = False
                
                # read file contents
                with open(os.path.join(root, file), 'r') as reader:
                    content = json.loads(reader.read())
                    
                # check for pixel track
                for cell in content['cells']:
                    if cell['cell_type'] == 'markdown':
                        if cell['source'][0].startswith('![tracker](https://'):
                            cell['source'] = cell['source'][1:]
                            update = True
                            # remove any blank lines at the start of the file/cell (these were empty spaces/lines after the tracker)
                            while True:
                                if cell['source'][0] == '\n':
                                    cell['source'] = cell['source'][1:]
                                else:
                                    break
                        # only review the first markdown cell then break the for loop
                        break
                
                # update files with pixel track - remove the tracking
                if update:
                    print('Remove tracking from: ', file)
                    with open(os.path.join(root, file), 'w') as writer:
                        writer.write(json.dumps(content))
                    
            print('Done with evaluation.')
