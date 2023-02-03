import os
import json
import urllib.parse

for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith(('.md', '.ipynb')) and not root.endswith('.ipynb_checkpoints'):
            print(os.path.join(root, file))
            
            if file.endswith('.md'):
                # read file contents
                with open(os.path.join(root, file), 'r') as reader:
                    content = reader.readlines()
                if content[0].startswith('![ga4](https://www.google-analytics.com'):
                    print('update: ', file)
                    #write back here
                    
            elif file.endswith('.ipynb'):
                # read file contents
                with open(os.path.join(root, file), 'r') as reader:
                    content = json.loads(reader.read())
                    
                for cell in content['cells']:
                    if cell['cell_type'] == 'markdown':
                        if cell['source'][0].startswith('![ga4](https://www.google-analytics.com'):
                            print('update: ', file)
                