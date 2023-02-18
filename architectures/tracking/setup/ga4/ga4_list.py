# this file, ga4_list.py, will list all the files in the repository with ga4 tracking

import os
import json
import urllib.parse

# this file is in: /vertex-ai-mlops/architectures/tracking/setup/ga4/ga4_list.py
for root, dirs, files in os.walk('../../../../.'):
    for file in files:
        if file.endswith(('.md', '.ipynb')) and not root.endswith('.ipynb_checkpoints'):
            
            if file.endswith('.md'):
                
                # read file contents
                with open(os.path.join(root, file), 'r') as reader:
                    content = reader.readlines()
                
                # check for ga4
                if content[0].startswith('![ga4](https://www.google-analytics.com'):
                    print('File: ', os.path.join(root, file))

            elif file.endswith('.ipynb'):
                
                # read file contents
                with open(os.path.join(root, file), 'r') as reader:
                    content = json.loads(reader.read())
                    
                # check for ga4
                for cell in content['cells']:
                    if cell['cell_type'] == 'markdown':
                        if cell['source'][0].startswith('![ga4](https://www.google-analytics.com'):
                            print('File: ', os.path.join(root, file))
                        # only review the first markdown cell the break for loop
                        break