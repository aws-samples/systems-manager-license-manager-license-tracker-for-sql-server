import sys
import boto3
import json
import botocore

def script_handler(events, context):
  client = boto3.client('ssm')
  
  instanceId = events['instanceId']
  accountId = events['accountId']
  tagKey = events['tagKey']
  tagValue = events['tagValue']
  region = events['region']
  sqlServerEELicenseConfig = events['sqlServerEELicenseConfig']
  sqlServerSTDLicenseConfig = events['sqlServerSTDLicenseConfig']
  sqlServerEXPLicenseConfig = events['sqlServerEXPLicenseConfig']
  sqlServerWEBLicenseConfig = events['sqlServerWEBLicenseConfig']
  sqlServerDEVLicenseConfig = events['sqlServerDEVLicenseConfig']
  accounts = events['accounts']
  regions = events['regions']
  automationAssumeRole = events['automationAssumeRole']
  
  if instanceId == '*':
    key = 'tag:'+tagKey
    values = tagValue
  else:
    key = 'ParameterValues'
    values = instanceId
  
  response = client.start_automation_execution(
    DocumentName='Secondary-SQLServerLicenseTrackingSolution-Document',
    Parameters={
        'InstanceId': [
            instanceId
        ],
        'TagKey': [
            tagKey
        ],
        'TagValue': [
            tagValue
        ],
        'SQLServerEELicenseConfiguration': [
            sqlServerEELicenseConfig
        ],
        'SQLServerSTDLicenseConfiguration': [
            sqlServerSTDLicenseConfig
        ],
        'SQLServerEXPLicenseConfiguration': [
            sqlServerEXPLicenseConfig
        ],
        'SQLServerWEBLicenseConfiguration': [
            sqlServerWEBLicenseConfig
        ],
        'SQLServerDEVLicenseConfiguration': [
            sqlServerDEVLicenseConfig
        ],
        'AutomationAssumeRole': [
            automationAssumeRole
        ]
    },
    TargetParameterName='InstanceId',
    Targets=[
        {
            'Key': key,
            'Values': [
                values
            ]
        },
    ],
    TargetLocations=[
      {
        'Accounts': [
            accounts,
        ],
        'Regions': [
            regions,
        ],
        'TargetLocationMaxConcurrency': '4',
        'TargetLocationMaxErrors': '4'
      }
    ],
  )
  
  if response[\"AutomationExecutionId\"]:
    status = \"Secondary-SQLServerLicenseTrackingSolution-Document has been successfuly invoked. Check AutomationExecutionId - \" + response[\"AutomationExecutionId\"] + \" for more details\"
  else:
    status = \"Secondary-SQLServerLicenseTrackingSolution-Document was not invoked\"
    raise Exception(f\"It appears that this step couldn't be completed due to an unknown error. Please check the logs for more details\") 
  
  return {'message': status}"