#!/usr/bin/env python
import yaml
import sys
import io
import os
import re

buffer = io.StringIO()
for line in sys.stdin:
    buffer.write(line)
buffer.seek(0)

def get_num_docs(contents):
    num_docs = 1
    for line in contents.split('\n'):
        result = re.search("---", line)
        if result:
            num_docs = num_docs + 1
    return num_docs

# pyyaml cannot process multi-document files, so we're just passing the original contents back if we detect one
contents = buffer.getvalue()
if get_num_docs(contents) > 1:
    buffer.seek(0)
    for line in buffer:
        sys.stdout.write(line)
else:
    config = yaml.load(buffer, Loader=yaml.FullLoader)
    check_envs = {
        "CI_MERGE_REQUEST_ID": "ci.corp.com/merge-request-id",
        "DEPLOY_TEAM": "ci.corp.com/deploy-team",
        "CI_PIPELINE_ID": "ci.corp.com/pipeline-id",
        "CI_PROJECT_NAMESPACE": "ci.corp.com/project-namespace",
        "CI_PROJECT_NAME": "ci.corp.com/project-name",
        "GITLAB_USER_EMAIL": "ci.corp.com/committer"
    }
    if config['kind'] == "Deployment":
        # TODO evaluate if we can/should do this same action on statefulsets and daemonsets
        if 'annotations' not in config['spec']['template']['metadata']:
            tmpdict = config['spec']['template']['metadata']
            tmpdict['annotations'] = {}
            tmpdict = tmpdict['annotations']
        else:
            tmpdict = config['spec']['template']['metadata']['annotations']
        tmpdict['ad.datadoghq.com/tolerate-unready'] = "true"
        for var in check_envs.keys():
            env_val = os.getenv(var, None)
            if env_val:
                tmpdict[check_envs[var]] = str(env_val)
        config['spec']['template']['metadata']['annotations'] = tmpdict
        print(yaml.dump(config))
    # elif config['kind'] == "Ingress":
    #     if 'annotations' not in config['metadata']:
    #         tmpdict = config['metadata']
    #         tmpdict['annotations'] = {}
    #         tmpdict = tmpdict['annotations']
    #     else:
    #         tmpdict = config['metadata']['annotations']
    #     if 'kubernetes.io/ingress.class' not in tmpdict:
    #         tmpdict['kubernetes.io/ingress.class'] = "nginx"
    #     config['metadata']['annotations'] = tmpdict
    #     print(yaml.dump(config))
    else:
        buffer.seek(0)
        for line in buffer:
            sys.stdout.write(line)
