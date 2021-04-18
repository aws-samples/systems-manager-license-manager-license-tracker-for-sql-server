import sys
import boto3
import json
import botocore

def script_handler(events, context):
  organization = boto3.client('organizations')
  ssm = boto3.client('ssm')
  #targets = events['targets'].split(",")
  target = ''
  accountList = []

  # roots = organization.list_roots()
  # if roots['Roots']:
  #   for root in roots['Roots']:
  #     target = root['Id']
  accountListResponse = organization.list_accounts()
  
  if accountListResponse['Accounts']:
    for accountId in accountListResponse['Accounts']:
      accountList.append(accountId['Id'])
  else:
    print('No account IDs found in this account')
  # else:
  #   raise Exception(f"This account doesn't seem to have a valid root/management account in AWS Organization (https://aws.amazon.com/organizations/faqs/)")
  
  # Built this to support OUs and/or accounts
  # for target in targets:
  #   if target.isdigit():
  #     accountList.append(target)
  #   else:
  #     accountListResponse = organization.list_accounts_for_parent(
  #       ParentId=target
  #     )
      
  #Get current document permissions
  oldDocumentPermissionResponse = ssm.describe_document_permission(
    Name='Secondary-SQLServerLicenseTrackingSolution-Document',
    PermissionType='Share'
  )
  
  #Remove old document permissions
  if oldDocumentPermissionResponse['AccountIds']:
    removeOldDocumentPermissionResponse = ssm.modify_document_permission(
      Name='Secondary-SQLServerLicenseTrackingSolution-Document',
      PermissionType='Share',
      AccountIdsToRemove=oldDocumentPermissionResponse['AccountIds']
    )
  
  #Modify the document permissions with the new list of accounts from the specified OUs
  response = ssm.modify_document_permission(
    Name='Secondary-SQLServerLicenseTrackingSolution-Document',
    PermissionType='Share',
    AccountIdsToAdd=accountList
  )
  
  {'ResponseMetadata': {'RequestId': 'ded37a9c-6a9a-4419-afb9-e715bf876708', 'HTTPStatusCode': 200, 'HTTPHeaders': {'server': 'Server', 'date': 'Thu, 15 Apr 2021 04:56:22 GMT', 'content-type': 'application/x-amz-json-1.1', 'content-length': '2', 'connection': 'keep-alive', 'x-amzn-requestid': 'ded37a9c-6a9a-4419-afb9-e715bf876708'}, 'RetryAttempts': 0}}
  if response['ResponseMetadata']:
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
      print(f"Successfully modified Secondary-SQLServerLicenseTrackingSolution-Document permissions to be shared with these accounts: "+','.join(accountList))
    else:
      raise Exception(f"There was a problem modifying the permissions of Secondary-SQLServerLicenseTrackingSolution-Document, check the logs for more details")
  else:
    raise Exception(f"There seems to be a problem, check the logs for more details")