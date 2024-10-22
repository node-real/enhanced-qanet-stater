import argparse
import logging
import os
import subprocess
import json
import socket
import calendar
import datetime
import time
import requests
import shutil
import random
import http.client
import re
import glob
from multiprocessing import Process, Queue
import concurrent.futures
from collections import namedtuple


import qanet.log_setup
from dotenv import dotenv_values

pjoin = os.path.join

parser = argparse.ArgumentParser(description='qanet starter')
parser.add_argument('--monorepo-dir', help='Directory of the monorepo', default=os.getcwd())

log = logging.getLogger()



def main():
    args = parser.parse_args()
    env = dotenv_values('./.env')
    log.info(env)
    monorepo_dir = os.path.abspath(args.monorepo_dir)
    qanet_config_path = pjoin(monorepo_dir, 'addresses.json')
    address_json = read_json(qanet_config_path)
    log.info(address_json)
    pr_template_dir = './pr-template/nodereal-app'
    pr_output_dir = './output/nodereal-app'
    shutil.copytree(src=pr_template_dir + '/qa/gitops/qa-us/enhanced-qanet-temp',
                    dst=pr_output_dir + '/qa/gitops/qa-us/enhanced-qanet-temp')
    shutil.copytree(src=pr_template_dir + '/qa/gitops/init-argocd/spec/enhanced-qanet-temp',
                    dst=pr_output_dir + '/qa/gitops/init-argocd/spec/enhanced-qanet-temp')
    shutil.copyfile(src=pr_template_dir + '/qa/gitops/init-argocd/auto-aps/gold-digger-temp.yaml',
                    dst=pr_output_dir + '/qa/gitops/init-argocd/auto-aps/gold-digger-temp.yaml')
    shutil.copyfile(src=pr_template_dir + '/qa/gitops/init-argocd/auto-aps/nebula-apus-temp.yaml',
                    dst=pr_output_dir + '/qa/gitops/init-argocd/auto-aps/nebula-apus-temp.yaml')

    os.rename(pr_output_dir+'/qa/gitops/qa-us/enhanced-qanet-temp', pr_output_dir+'/qa/gitops/qa-us/' + env['QANET_NAME'])
    gold_digger_values = pjoin(pr_output_dir+'/qa/gitops/qa-us/' + env['QANET_NAME'], 'gold-digger', 'values.yaml')
    nebula_apus_values = pjoin(pr_output_dir+'/qa/gitops/qa-us/' + env['QANET_NAME'], 'nebula-apus', 'values.yaml')
    replacePlaceHolderOneFile(gold_digger_values, address_json, env)
    replacePlaceHolderOneFile(nebula_apus_values, address_json, env)

    aps_output_dir = './output/nodereal-app/qa/gitops/init-argocd/auto-aps'
    new_aps_apus_output_dir = pjoin(aps_output_dir, env['QANET_NAME']+'.nebula-apus.yaml')
    new_aps_gold_output_dir = pjoin(aps_output_dir, env['QANET_NAME']+'.gold-digger.yaml')
    os.rename(pjoin(aps_output_dir, 'nebula-apus-temp.yaml'), new_aps_apus_output_dir)
    os.rename(pjoin(aps_output_dir, 'gold-digger-temp.yaml'), new_aps_gold_output_dir)
    replacePlaceHolderOneFile(new_aps_apus_output_dir, address_json, env)
    replacePlaceHolderOneFile(new_aps_gold_output_dir, address_json, env)

    spec_out_put_dir = './output/nodereal-app/qa/gitops/init-argocd/spec/' + env['QANET_NAME']

    os.rename('./output/nodereal-app/qa/gitops/init-argocd/spec/enhanced-qanet-temp' ,spec_out_put_dir)

    spec_gold_put_dir = pjoin(spec_out_put_dir, 'nebula-apus.yaml')
    spec_apus_put_dir = pjoin(spec_out_put_dir, 'gold-digger.yaml')
    replacePlaceHolderOneFile(spec_gold_put_dir, address_json, env)
    replacePlaceHolderOneFile(spec_apus_put_dir, address_json, env)

    run_command(['git', 'checkout', 'main'], cwd=pr_output_dir)
    run_command(['git', 'pull', 'origin', 'main'], cwd=pr_output_dir)
    # git content list
    random_num = random.randint(0, 100)
    new_branch_name = 'opbnb-new-qanet-' + env['QANET_NAME'] + "-" + str(random_num)
    run_command(['git', 'checkout', '-b', new_branch_name], cwd=pr_output_dir)
    run_command(['git', 'add', '--all'], cwd=pr_output_dir)
    run_command(['git', 'commit', '-m', 'New opbnb qanet enhanced api' + env['QANET_NAME']], cwd=pr_output_dir)
    run_command(['git', 'push', 'origin', new_branch_name], cwd=pr_output_dir)

    log.info('config info will loaded in output file, please check')




def replacePlaceHolderOneFile(file_path,json_item,env):
    log.info(f'replace placeholder in file: {file_path}')
    with open(file_path, 'r') as file:
        file_content = file.read()
    # tag
    # dbName
    # optimismPortalProxy
    # l2OutputOracleProxy
    enhanced_tag = env['ENHANCED_TAG']
    db_name = env['DB_NAME']
    l1_rpc_url = env['L1_RPC_URL']
    qanet_name = env['QANET_NAME']
    optimism_portal_proxy = json_item['OptimismPortalProxy']
    l2_output_oracle_proxy = json_item['L2OutputOracleProxy']

    file_content = file_content.replace('${enhanced_tag}', enhanced_tag)
    file_content = file_content.replace('${db_name}', db_name)
    file_content = file_content.replace('${l1_rpc_url}', l1_rpc_url)
    file_content = file_content.replace('${qanet_name}', qanet_name)
    file_content = file_content.replace('${optimism_portal_proxy}', optimism_portal_proxy)
    file_content = file_content.replace('${l2_output_oracle_proxy}', l2_output_oracle_proxy)

    with open(file_path, 'w') as file:
        file.write(file_content)


def read_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def run_command(args, check=True, shell=False, cwd=None, env=None, timeout=None,capture_output=False):
    env = env if env else {}
    return subprocess.run(
        args,
        check=check,
        shell=shell,
        env={
            **os.environ,
            **env
        },
        cwd=cwd,
        timeout=timeout,
        capture_output=capture_output,
        text=True
    )