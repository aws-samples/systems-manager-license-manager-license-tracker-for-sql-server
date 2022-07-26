## Centrally track Microsoft SQL Server licenses in AWS Organizations using AWS License Manager and AWS Systems Manager

Most enterprises find it hard to maintain control of the commercial
licensing of Microsoft, SAP, Oracle, and IBM products due to limited
visibility. They wind up over-provisioning licenses to avoid the
headache with third-party license providers or under-provisioning
licenses, only to be faced with steep penalties.  
  
To assist enterprises with the challenge of tracking licenses, AWS has
built specific features and services to make this easier for customers.
There are two main use-cases: 

  - Using license-included instances allows you access to fully
    compliant licenses, where AWS handles the tracking and management
    for you.  

  - [AWS License Manager](https://aws.amazon.com/license-manager/) makes
    it easy for you to set rules to manage, discover, and report
    software license usage. 

There are some scenarios or software products (for example, Microsoft
SQL Server editions) that cannot be governed by these two options, which
means you could receive an unwanted surprise in the next audit. In this
first of a two-part post, I show you how to build a solution that
centrally discovers and tracks your SQL Server instances across AWS
accounts and Regions that are part of an organization in [AWS
Organizations](https://aws.amazon.com/organizations/). You can enhance
this approach to target other commercial software such as Oracle, SAP,
or IBM. For single account setups, see the [Use AWS License Manager and
AWS Systems Manager to discover SQL Server BYOL
instances](https://aws.amazon.com/blogs/mt/use-aws-license-manager-and-aws-systems-manager-to-discover-sql-server-byol-instances/)
blog post.

# Prerequisites

To deploy this solution across multiple Regions and/or accounts in 
an organization, **complete** these steps.  

  - **Enable trusted access with AWS Organizations for CloudFormation.** 
    Complete the following tasks as described in [Enable trusted access 
    with AWS Organizations](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-orgs-enable-trusted-access.html)
    - Enable all features in AWS Organizations. With only consolidated billing features enabled, you cannot create a stack set with service-managed permissions.  
    - Enable trusted access with AWS Organizations. After trusted access is enabled, StackSets creates the necessary IAM roles in the organization's management account and target (member) accounts when you create stack sets with service-managed permissions.

  - **Link License Manager to AWS Organizations in all targer Regions.** 
    To share license configurations with member accounts you will need to link 
    License Manager to AWS Organizations.

    In the AWS License Manager console, choose **Settings**, and then select **Link AWS Organizations accounts**, as shown in Figure 1. 

![](images/lm-link-organization.png)
<p align="center">Figure 1: Linking AWS Organizations accounts in the License Manager console</p>

    Once completed, under the Settings section you should see a link to the new Resource Share ARN (Resource Access Manager), 
    as shown in Figure 2.

![](images/lm-settings-wth-resourceshare.png)
<p align="center">Figure 2: License Manager Settings with resource share ARN</p>
    

  - **Create license configurations.** In AWS License Manager, create
    license configurations for the SQL Server editions in each AWS
    Region where you will be deploying this solution. A license
    configuration represents the licensing terms in the agreement with
    your software vendor. Using [AWS CloudShell](https://aws.amazon.com/cloudshell/), 
    run the following command to create the following license configurations (case-sensitive):

    ```
    for r in {REGION-1,REGION-2}; do for i in { SQLServerEELicenseConfiguration, SQLServerSTDLicenseConfiguration, SQLServerDEVLicenseConfiguration, SQLServerWEBLicenseConfiguration, SQLServerEXPLicenseConfiguration};  do aws license-manager create-license-configuration --name "$i" --license-counting-type vCPU --region $r; done; done
    ```

    - SQLServerEELicenseConfiguration for Enterprise Edition

    - SQLServerSTDLicenseConfiguration for Standard Edition

    - SQLServerDEVLicenseConfiguration for Developer Edition

    - SQLServerWEBLicenseConfiguration for Web Edition

    - SQLServerEXPLicenseConfiguration for Express Edition

  - **Share license configurations.** After you have defined your
    configurations, use AWS Organizations or AWS Resource Access Manager
    to share license configurations. For instructions, see the [Tracking
    software usage across multiple AWS accounts using AWS License
    Manager](https://aws.amazon.com/blogs/mt/tracking-software-usage-across-multiple-aws-accounts-using-aws-license-manager/) blog
    post.

    After you share your principals (accounts) and resources (license configurations), you should see them in the AWS Resource Access Manager console:

![](images/ram-lm-shared.png)
<p align="center">Figure 3: Shared principals and resources in the AWS Resource Access Manager console</p>

# Solution overview

AWS License Manager allows you to track your commercial license usage to
stay compliant across your enterprise teams. It associates license
definitions with AMIs from which instances are launched. AWS License
Manager can also auto-discover licensed software (in this solution, SQL
Server) that’s installed on instances after initial instance deployment.
The solution described in this blog post enhances the auto-discovery
capability and provides license edition details for instances deployed
across AWS Regions and accounts in AWS Organizations.

Figure 4 shows the solution architecture. In addition to AWS License
Manager, the solution uses the following Systems Manager features and
capabilities:

  - [Automation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-automation.html)
    to orchestrate the workflow.

  - [State](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-state.html)
    <span class="underline">Manager</span> to invoke the Automation
    document on a user-defined frequency.

  - [Inventory](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-inventory.html)
    to maintain the information collected about the instances and the
    SQL Server editions running on them.

![](images/solution-arch.png )
<p align="center">Figure 4: Solution architecture</p>


# Walkthrough

[![cfn-stack](images/cfn-stack.png)]((https://console.aws.amazon.com/cloudformation/home?region=ap-southeast-2#/stacks/new?stackName=SQLServer-LTS&templateURL=https://bhatprav-blog-artefacts.s3.ap-southeast-2.amazonaws.com/sql-server-lts/template.yaml))

To deploy the solution, launch this CloudFormation template in the
management account of your organization.  

This template deploys the following resources:

1.  **Systems Manager documents**
    
      - The setup Automation document (SetupSQLServerLicenseTrackingSolutionDocument) includes the logic to execute steps 1 and 2 of the walkthrough.
    
      - The secondary Automation document (DiscoverSQLServerLicenseTrackingSolutionDocument) includes the logic to execute steps 3-8 of the walkthrough.

2.  **All the IAM roles required to deploy the solution**
    
    - Automation administration role (for the administration of the Automation documents)
        
    - Automation execution role (for the execution of the Automation documents)
    
    - CloudFormation StackSets administration role (to deploy the solution across multiple accounts and Regions)
    
    - CloudFormation StackSets execution role (to deploy the solution across multiple accounts and Regions)
    
    - Lambda execution role (for the execution of the ModifySQLServerLTSDiscoverDocumentPermission Lambda function)

3.  **S3 bucket**

    This central bucket in the management account stores all the data from resource data syncs across the accounts, as shown in step 8 of Figure 4.

4.  **Lambda**
    
      - The ModifySQLServerLTSDiscoverDocumentPermission function is
        used to maintain permissions of the Discover Automation
        document with the accounts in the organization.
    
      - A [trigger to
        schedule](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-run-lambda-schedule.html)
        the execution of the Lambda function to run once every 30 days
        using [Amazon EventBridge](https://aws.amazon.com/eventbridge/)
        to ensure that the secondary document is shared with the latest
        set of accounts.
    
Once your template has been deployed, using AWS CloudShell 
invoke the lambda function to share the Discover document with all the members
accounts within the organization. Replace REGION with your target regions:

```
for i in {REGION-1,REGION-2}; do aws lambda invoke --function-name ModifySQLServerLTSDiscoverDocumentPermission output.txt --region $i; done
```

**Note**: The lambda function is scheduled to run every day so all subsequent invocations will be performed automatically.

## Centralizing Systems Manager Inventory data using resource data sync

The [resource data sync](https://docs.aws.amazon.com/systems-manager/latest/userguide/Explorer-resource-data-sync.html)
capability in AWS Systems Manager lets you sync inventory data from your
managed instances into an [Amazon Simple Storage
Service](https://aws.amazon.com/s3/) (Amazon S3) bucket. *The resource
data sync* then updates the S3 bucket whenever new Inventory data is
collected. You can also sync Inventory data from multiple AWS accounts
into a single S3 bucket, making the bucket an inventory data lake for
multiple AWS accounts. You can then use the data lake for advanced
queries and analysis of inventory data across multiple accounts. For
more information, refer to the instructions under Create an inventory 
resource data sync for accounts defined in AWS Organizations in [Use resource 
data sync to aggregate inventory data](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-inventory-resource-data-sync.html).

## Invoking the solution using a State Manager association

Because CloudFormation doesn’t currently support *target-locations*, use
the AWS CLI to create the association. Update the highlighted parameters
and then execute this command in the management or root account of your
organization.

  - **Management account ID**: Specify your management account ID for
    the SQLServerLTS-SystemsManager-AutomationAdministrationRole ARN.

  - **Organizational unit IDs**: Enter an organizational unit ID (for
    example, ou-abcd-1qwert43).

  - **Regions**: Specify all AWS Regions (for example, us-east-1) where
    your SQL Server instances are running.

  - **TargetLocationMaxConcurrency** and **TargetLocationMaxErrors**:
    Specify these values based on the number of accounts and error
    thresholds described in
    [TargetLocation](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_TargetLocation.html)
    in the AWS Systems Manager API Reference.

```
aws ssm create-association \
    --association-name "SQLServerLicenseTrackingSolutionAssociation" \
    --name "SetupSQLServerLicenseTrackingSolutionDocument" \
    --parameters '{"AutomationAssumeRole":["arn:aws:iam::MANAGEMENT-ACCOUNT-ID:role/SQLServerLTS-SystemsManager-AutomationAdministrationRole"]}' \
    --no-apply-only-at-cron-interval \
    --target-locations '[{"Accounts": ["OU1-ID LIKE ou-abcd-1qwert43","OU2-ID","OU3-ID"],"Regions": ["REGION-1 like us-east-1","REGION-2"],"TargetLocationMaxConcurrency": "4","TargetLocationMaxErrors": "4","ExecutionRoleName": "SQLServerLTS-SystemsManager-AutomationExecutionRole"}]'
```

**Note:** This command will invoke the system to run it once immediately after it
is created. To ensure that the solution can track licenses on an on-going schedule, 
update the above command using --schedule-expression, see
[create-association](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/ssm/create-association.html)
in the AWS CLI Command Reference. 


### Validating the execution ran successfully

After the association has triggered the automation, open the Systems
Manager console and from the left navigation pane, choose
***Automation***. In **Automation executions**, choose the most recent
execution of the *SetupSQLServerLicenseTrackingSolutionDocument*, as
shown in Figure 5.

![](images/ssm-automation-execution-result.png)
<p align="center">Figure 5: Automation executions (management account)</p>

Depending on the number of Regions, accounts, and instances you execute
this solution against, a successful run of the execution looks like the
following:

![](images/ssm-automation-dashboard.png)
<p align="center">Figure 6: Automation execution detail (management account)</p>

On the details page for the execution, choose any of the **step ID**s,
and then under **Outputs**, choose the **execution ID.** Under **Executed steps** 
click on step #2 ID, you can find the *Automation execution ID* of the
discover document in the member account, as shown in Figure 7.

![](images/execution-id.png)
<p align="center">Figure 7: Automation outputs (management account)</p>


In the Systems Manager console, search for this ID in the member account
and Region. Choose the execution ID link to get more information about
the execution.

![](images/member-account-ssm-dashboard.png)
<p align="center">Figure 8: Automation executions (member account)</p>


To confirm that the license utilization data has been updated in AWS
License Manager, using the management account and selected Region, open
the **License Manager** console. Depending on the licenses consumed, the
**Customer managed licenses** list will look something like Figure 9 in 
each region:


![](images/customer-managed-licenses.png)
<p align="center">Figure 9: Customer managed licenses</p>


## Adding new accounts and Regions

The solution will automatically cover any new AWS accounts that you provision 
under the OUs you specified when you created the association 
(Note: Lambda function that shares the Discover document with member accounts 
is invoked every day). If you create new OUs or add Regions, you will need to 
update the following solution components:

**CloudFormation**:

1.  In the CloudFormation console, choose the original template you
    deployed and then choose **Update**.

2.  Leave the **Use the current template** option selected.

3.  Under **Automation Documents**, update the **TargetRegions** and
    **TargetOUs** parameters with the new values.

**Association**:

Use
[update-association](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/ssm/update-association.html)
to update the current association. Specify the accounts and Regions in
--target-locations.

**Resource data sync**
Add new resource data sync in the account and Region as described earlier 
in the post in “Centralizing Systems Manager Inventory data using resource data sync.”

## Setup databases in Athena
Athena will help us query the aggregated data in the centralized S3
bucket created in the resource data sync step in part 1.

1.  In the Athena console, copy and paste the following statement into
    the query editor and then choose **Run Query**.

```CREATE DATABASE ssminventory```

The console creates a database named ssminventory*, *a logical grouping
for the three tables you will be creating:

  - AWS_InstanceDetailedInformation: Consists of an instance’s metadata
    like CPU, cores, and so on.

  - AWS_Tag: Consists of all the tags defined for an instance.

  - Custom_SQLServer: Consists of the SQL Server metadata, including
    edition and version, running on an instance.

For more information, see [Metadata collected by inventory](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-inventory-schema.html)
in the AWS Systems Manager User Guide.

If you want to set up more inventory tables in Athena, see [Walkthrough:
Use resource data sync to aggregate inventory
data](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-inventory-resource-data-sync.html). 

2.  Copy and the following statement and paste it into the query editor.
    Replace DOC-EXAMPLE-BUCKET and bucket_prefix **with the name and
    prefix of the central Amazon S3 target created in part 1.
    Choose **Run Query**.

```
CREATE EXTERNAL TABLE IF NOT EXISTS
ssminventory.AWS_InstanceDetailedInformation (  
`Cpus` string,  
`osservicepack` string,  
`cpuhyperthreadenabled` string,  
`cpuspeedmhz` string,  
`cpusockets` string,  
`cpucores` string,  
`cpumodel` string,  
`resourceid` string,  
`capturetime` string,  
`schemaversion` string  
)  
PARTITIONED BY (AccountId string, Region string, ResourceType
string)  
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'  
WITH SERDEPROPERTIES (  
'serialization.format' = '1'  
) LOCATION
's3://DOC-EXAMPLE-BUCKET/bucket_prefix/AWS:InstanceDetailedInformation/'
```

3.  To partition the table, copy the following statement, paste it into
    the query editor, and then choose **Run Query**.

```
MSCK REPAIR TABLE ssminventory.AWS_InstanceDetailedInformation
```

**Note:** You will need to run this statement again as the partition
changes (for example, for new accounts, regions, or resource types).
Depending on how often these change in your organization, consider using
the [AWS Glue
crawler](https://docs.aws.amazon.com/glue/latest/dg/add-crawler.html) to
automate this step.

4.  To preview your data, choose **…** and then next to
    the AWS_InstanceDetailedInformation table, choose **Preview
    table**.

5.  Run the following queries individually in the Athena console to set
    up the AWS_Tag and Custom_SQLServer tables.

```
CREATE EXTERNAL TABLE IF NOT EXISTS ssminventory.AWS_Tag (  
`key` string,  
`value` string,  
`resourceid` string,  
`capturetime` string,  
`schemaversion` string  
)  
PARTITIONED BY (AccountId string, Region string, ResourceType
string)  
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'  
WITH SERDEPROPERTIES (  
'serialization.format' = '1'  
) LOCATION 's3://DOC-EXAMPLE-BUCKET/bucket_prefix/AWS:Tag/'
```

```
MSCK REPAIR TABLE ssminventory.AWS\_Tag
```

```
CREATE EXTERNAL TABLE IF NOT EXISTS ssminventory.Custom_SQLServer (  
`name` string,  
`edition` string,  
`version` string,  
`resourceid` string,  
`capturetime` string,  
`schemaversion` string  
)  
PARTITIONED BY (AccountId string, Region string, ResourceType
string)  
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'  
WITH SERDEPROPERTIES (  
'serialization.format' = '1'  
) LOCATION 's3://DOC-EXAMPLE-BUCKET/bucket_prefix/Custom:SQLServer/'
```

```
MSCK REPAIR TABLE ssminventory.Custom_SQLServer
```

## Visualize the data using QuickSight

Now that the data is available to access using Athena, you will use QuickSight to visualize it. 

### Prepare the dataset

Amazon QuickSight provides out-of-the-box integration with Athena. For
more information, see [Creating a Dataset Using Amazon Athena
Data](https://docs.aws.amazon.com/quicksight/latest/user/create-a-data-set-athena.html).

Use the ssminventory database that you created in the previous step. To
try out different combinations for analysis and visualization, create
three datasets in QuickSight. To simplify the experience of visualizing
data in QuickSight, you can build
[views](https://docs.aws.amazon.com/athena/latest/ug/views.html) in
Athena.

1.  In the Amazon QuickSight console, select **custom\_sqlserver** and
    then choose **Edit/Preview data**.

![](images/dataset-in-quicksight.png)
<p align="center">Figure 9: Creating a dataset in QuickSight</p>


2.  In the editor view, choose **Add data**, and then select the other
    tables as shown in Figure 3.

![](images/quicksight-data-editor.png)
<p align="center">Figure 10: QuickSight dataset editor</p>


3.  Update the join configuration using **resourceid** as the join
    clause, as shown in Figure 4.

![](images/quicksight-data-editor.png)
<p align="center">Figure 11: Specifying the join configuration</p>

4.  Before you apply the changes, exclude all duplicate fields and
    update the data types as shown in Figure 5. 

![](images/excluded-fields.png)
<p align="center">Figure 12: Excluded fields</p>

You can use the dataset you just created to build your own analysis and
create visualizations as shown in Figure 6. To stay informed about
important changes in your data, you can create threshold alerts using
KPI and Gauge visuals in an Amazon QuickSight dashboard. For
information, see [Working with Threshold Alerts in Amazon QuickSight](https://docs.aws.amazon.com/quicksight/latest/user/threshold-alerts.html).
With these alerts, you can set thresholds for your data and be notified
by email when your data crosses them. 

![](images/quicksight-analysis.png )
<p align="center">Figure 13: QuickSight analysis</p>


# Conclusion

In this solution, I showed how you can use AWS License
Manager and AWS Systems Manager to automate the process of tracking
your [Microsoft SQL Server
licenses](https://aws.amazon.com/windows/resources/licensing/) across
multiple accounts and Regions that are part of AWS Organizations. I also
showed you how to use Amazon Athena and Amazon QuickSight to visualize
the aggregated license consumption data across your AWS accounts. You
can easily expand on the analysis and dashboards described in this post
to meet your organization’s needs. With improved visibility of your
license consumption across your organization, you can ensure you are
compliant with your commercial licensing agreements and avoid steep
penalties.
