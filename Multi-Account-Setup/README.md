Multi-account SQL Server license tracking

https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-inventory-datasync.html#systems-manager-inventory-resource-data-sync-AWS-Organizations - setting up multi account resource data sync for cross-account inventory veiw

https://aws.amazon.com/blogs/mt/tracking-software-usage-across-multiple-aws-accounts-using-aws-license-manager/ - multi-account license manager setup

Key things to remember -

1. Role in member account to allow for LM configuration updates
2. Role in member accounts for cross-account automation - AWS-SystemsManager-AutomationExecutionRole and AWS-SystemsManager-AutomationAdministrationRole [https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-automation-multiple-accounts-and-regions.html] - we need to create CFn this to make it easy - stacksets to deploy the execution role in each member account 
3. RDS setup in each member account - CLI/API support only since the central bucket isnt in the same account
4. Changes in document to allow for multi-account deployment
5. Association to run it across each member account - console doesnt support it but API and CLI does.
6. What about multi-region? RDS will need to be created in each region, and for the association its just a parameter - supported with APIs/CLIs only
7. Can we build one single solution for a multi-region and single-region - why should the customer have to deploy 2 different solutions?
8.  We can use assertState rather than 60s timer after deleting custom inventory
9. Can you automate the tagging process based on Ralph’s notes?
10. Since the primary document cannot close the loop back to its caller it cannot find the secondary document - the way around this would be to share the secondary document to all the member accounts or make it public. The advantage of making it public is that you dont need to share the document with every new account (we could automate this by making using Org APIs to list all member accounts and update the document permission) but there is a limit of 1000 accounts. Disadvantage of making it public is that it will be public :) 
11. Document sharing for cross-region requires the document to be created in that region


Workflow - 

1. Foundational (one-off steps) -
    1. Link LM to Org (cross account inventory search not required)
    2. Share Secondary document with all the member accounts - can be triggered by EventBridge (addition or deletion of accounts in the Org)
    3. Share license configuration with member accounts (might have to use RAM - even though linking associates the principals)
    4. Create central RDS s3 bucket in master
    5. Glue crawlers
    6. Athena
    7. Quicksight

2. Member accounts -

-----------------------------------------------------------------------------------
In order to deploy this solution in a multi-account and/or multi-region architecture complete these one-off steps -
1.  