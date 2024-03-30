# vertex-ai-mlops/architectures/tracking/setup/pixel/pixel_list.py
# this file, pixel_list.py, will list all the files in the repository
# to remove the tracking from this files, run pixel_remove.py

import os
import json

# this file is in: /vertex-ai-mlops/architectures/tracking/setup/pixel/pixel_list.py
for root, dirs, files in os.walk('../../../../.'):
    for file in files:
        if file.endswith(('.md', '.ipynb')) and not root.endswith('.ipynb_checkpoints'):
            
            if file.endswith('.md'):
                
                # read file contents
                with open(os.path.join(root, file), 'r') as reader:
                    content = reader.readlines()
                
                # check for pixel track
                if content[0].startswith('![tracker](https://'):
                    print('File: ', os.path.join(root, file))

            elif file.endswith('.ipynb'):
                
                # read file contents (as JSON rather than nbformat)
                with open(os.path.join(root, file), 'r') as reader:
                    content = json.loads(reader.read())
                    
                # check for pixel track
                for cell in content['cells']:
                    if cell['cell_type'] == 'markdown':
                        if cell['source'][0].startswith('![tracker](https://'):
                            print('File: ', os.path.join(root, file))
                        # only review the first markdown cell the break for loop
                        break
