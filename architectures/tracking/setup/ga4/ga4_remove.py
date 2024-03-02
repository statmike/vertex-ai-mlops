# this file, ga4_remove.py, will remove the tracking from files in the repository
# to see files this will impact first run ga4_list.py

import os
import json
import urllib.parse

# this file is in: /vertex-ai-mlops/architectures/tracking/setup/ga4/ga4_remove.py
for root, dirs, files in os.walk('../../../../.'):
    for file in files:
        if file.endswith(('.md', '.ipynb')) and not root.endswith('.ipynb_checkpoints'):
            print('evaluating: ', os.path.join(root, file))
            
            if file.endswith('.md'):
                update = False
                
                # read file contents
                with open(os.path.join(root, file), 'r') as reader:
                    content = reader.readlines()
                
                # check for ga4
                if content[0].startswith('![ga4](https://www.google-analytics.com'):
                    content = content[1:]
                    update = True
                    while True:
                        if content[0] == '\n':
                            content = content[1:]
                        else:
                            break
                    
                # update file if ga4 present
                if update:
                    print('make change here: ', file)
                    with open(os.path.join(root, file), 'w') as writer:
                        writer.writelines(content)
                    
            elif file.endswith('.ipynb'):
                update = False
                
                # read file contents
                with open(os.path.join(root, file), 'r') as reader:
                    content = json.loads(reader.read())
                    
                # check for ga4
                for cell in content['cells']:
                    if cell['cell_type'] == 'markdown':
                        if cell['source'][0].startswith('![ga4](https://www.google-analytics.com'):
                            cell['source'] = cell['source'][1:]
                            update = True
                            while True:
                                if cell['source'][0] == '\n':
                                    cell['source'] = cell['source'][1:]
                                else:
                                    break
                        # only review the first markdown cell the break for loop
                        break
                
                # update file if ga4 present
                if update:
                    print('make change here: ', file)
                    with open(os.path.join(root, file), 'w') as writer:
                        writer.write(json.dumps(content))
                    
            print('done with evaluation.')