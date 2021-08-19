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
    for you. With this option, you either pay as you go, with no upfront
    costs or long-term investment, or purchase [reserved
    instances](https://aws.amazon.com/aws-cost-management/aws-cost-optimization/reserved-instances/) or [savings
    plans](https://aws.amazon.com/savingsplans/) for cost savings in
    exchange for a commitment to a consistent amount of usage. 

  - [AWS License Manager](https://aws.amazon.com/license-manager/) makes
    it easy for you to set rules to manage, discover, and report
    software license usage. When you use AWS License Manager to
    associate an Amazon Machine Image (AMI) with a licensing
    configuration, you can track the use of licenses in AWS or your
    on-premises environment. You can also set rules in AWS License
    Manager to prevent licensing violations to help you stay compliant.

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

In part 2 of this post, I’ll show you how to query and centralize your
data so you have a unified view of your license utilization across AWS.

# Prerequisites

To deploy this solution in a multi-account or multi-region architecture
in an organization , **complete **these steps in each AWS Region where
your workloads are running. 

  - **Link License Manager or share license configurations between
    accounts.** Depending on your current setup and requirements, you
    can either link License Manager to AWS Organizations or use [AWS
    Resource Access Manager](https://aws.amazon.com/ram/) to share
    license configurations between accounts. For more information, see
    the [Tracking software usage across multiple AWS accounts using AWS
    License
    Manager](https://aws.amazon.com/blogs/mt/tracking-software-usage-across-multiple-aws-accounts-using-aws-license-manager/)
    blog post. I recommend the first option, as it allows for a shared
    inventory and a seamless transition when accounts are added or
    removed from the organization. However, the AWS RAM method provides
    maximum flexibility and allows you to share license configurations
    outside your organization.

> If you prefer the first option, in the AWS License Manager console,
> choose **Settings**, and then select **Link AWS Organizations
> accounts**, as shown in Figure 1. 
> 
> **Note:** For this solution, you can leave cross-account inventory
> search disabled unless you want to discover other software license
> usage.

![](media/image1.png)

*Figure 1: Linking AWS Organizations accounts in the License Manager
console*

\[ALT TEXT: On the Settings page, under Account management, the Link AWS
Organizations accounts checkbox is selected.\]

  - **Create license configurations.** In AWS License Manager, create
    license configurations for the SQL Server editions in each AWS
    Region where you will be deploying this solution. A license
    configuration represents the licensing terms in the agreement with
    your software vendor. For instructions, see Create a license
    configuration in the AWS License Manager User Guide.

> Use the following names for the license configurations:

  - SQLServerENTLicenseConfiguration for Enterprise Edition

  - SQLServerSTDLicenseConfiguration for Standard Edition

  - SQLServerDEVLicenseConfiguration for Developer Edition

  - SQLServerWEBLicenseConfiguration for Web Edition

  - SQLServerEXPLicenseConfiguration for Express Edition

> If you already have license configurations, edit the names to match. 

  - **Share license configurations.** After you have defined your
    configurations, use AWS Organizations or AWS Resource Access Manager
    to share license configurations. For instructions, see the [Tracking
    software usage across multiple AWS accounts using AWS License
    Manager](https://aws.amazon.com/blogs/mt/tracking-software-usage-across-multiple-aws-accounts-using-aws-license-manager/) blog
    post.

> After you share your principals (accounts) and resources (license
> configurations), you should see them in the AWS Resource Access
> Manager console:

![](media/image2.png)

*Figure 2: Shared principals and resources in the AWS Resource Access
Manager console*

\[ALT TEXT: The AWS Resource Access Manager console displays shared
resources and shared principals in lists organized by ID, type, and
status.\]

# Solution overview

AWS License Manager allows you to track your commercial license usage to
stay compliant across your enterprise teams. It associates license
definitions with AMIs from which instances are launched. AWS License
Manager can also auto-discover licensed software (in this solution, SQL
Server) that’s installed on instances after initial instance deployment.
The solution described in this blog post enhances the auto-discovery
capability and provides license edition details for instances deployed
across AWS Regions and accounts in AWS Organizations.

Figure 3 shows the solution architecture. In addition to AWS License
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

![](media/image3.png)

*Figure 3: Solution architecture*

\[ALT TEXT: In step 1, the primary Automation document is invoked, which
in step 2 removes old custom Inventory data. In step 3, the secondary
Automation document is invoked. In step 4, old AWS License Manager data
is removed. In step 5, the instances are discovered. In step 6,
Inventory is updated. In step 7, AWS License Manager is updated. In step
8, the Inventory data is aggregated using resource data sync. In steps 9
and 10, the Inventory data is queried and visualized using Athena and
QuickSight.\]

# Walkthrough

![](media/image4.png)  
To deploy the solution, launch this CloudFormation template in the
management account of your organization.  

This template deploys the following resources:

1.  **Systems Manager documents**
    
      - The primary Automation document
        (Primary-SQLServerLicenseTrackingSolution-Document) includes the
        logic to execute steps 1 and 2 of the walkthrough.
    
    <!-- end list -->
    
      - The secondary Automation document
        (Secondary-SQLServerLicenseTrackingSolution-Document) includes
        the logic to execute steps 3-8 of the walkthrough.

2.  **All the IAM roles required to deploy the solution**
    
    1.  Automation administration role (for the administration of the
        Automation documents)
    
    2.  Automation execution role (for the execution of the Automation
        documents)
    
    3.  CloudFormation StackSets administration role (to deploy the
        solution across multiple accounts and Regions)
    
    4.  CloudFormation StackSets execution role (to deploy the solution
        across multiple accounts and Regions)
    
    5.  Lambda execution role (for the execution of the
        Modify-SQLServerSecondaryDocument-Permission Lambda function)

3.  **S3 bucket**

> This central bucket in the management account stores all the data from
> resource data syncs across the accounts, as shown in step 8 of Figure
> 3.

4.  **Lambda**
    
      - The Modify-SQLServerSecondaryDocument-Permission function is
        used to maintain permissions of the secondary Automation
        document with the accounts in the organization.
    
      - A [trigger to
        schedule](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-run-lambda-schedule.html)
        the execution of the Lambda function to run once every 30 days
        using [Amazon EventBridge](https://aws.amazon.com/eventbridge/)
        to ensure that the secondary document is shared with the latest
        set of accounts.
    
      - A custom resource is created for the initial invocation of the
        Lambda function.

## Centralizing Systems Manager Inventory data using resource data sync

The [resource data
sync](https://docs.aws.amazon.com/systems-manager/latest/userguide/Explorer-resource-data-sync.html)
capability in AWS Systems Manager lets you sync inventory data from your
managed instances into an [Amazon Simple Storage
Service](https://aws.amazon.com/s3/) (Amazon S3) bucket. *The resource
data sync* then updates the S3 bucket whenever new Inventory data is
collected. You can also sync Inventory data from multiple AWS accounts
into a single S3 bucket, making the bucket an inventory data lake for
multiple AWS accounts. You can then use the data lake for advanced
queries and analysis of inventory data across multiple accounts. For
more information, see [Use resource data sync to aggregate inventory
data](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-inventory-resource-data-sync.html)
in the AWS Systems Manager User Guide.

To use resource data sync, execute the following [AWS
CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
command in each account across the AWS Regions where your workloads are
running.

**Note**: *DestinationDataSharing* is currently available with the AWS
CLI and SDK only.

aws ssm create-resource-data-sync --sync-name
SQLServerLTS-ResourceDataSync --s3-destination
"BucketName=**CENTRAL-S3-BUCKET-NAME**,SyncFormat=JsonSerDe,Region=**S3-BUCKET-REGION
like
ap-southeast-2**,DestinationDataSharing={DestinationDataSharingType=Organization}"
--region **RESOURCEDATASYNC-REGION-LIKE ap-southeast-2**

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

  - **TargetLocationMaxConcurrency** and** TargetLocationMaxErrors:
    Specify** these values based on the number of accounts and error
    thresholds described in
    [TargetLocation](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_TargetLocation.html)
    in the AWS Systems Manager API Reference.

aws ssm create-association \\  
    --association-name "SQLServerLicenseTrackingSolution-Association"
\\  
    --name "Primary-SQLServerLicenseTrackingSolution-Document" \\  
    --parameters
'{"AutomationAssumeRole":\["arn:aws:iam::**MANAGEMENT-ACCOUNT-ID**:role/SQLServerLTS-SystemsManager-AutomationAdministrationRole"\]}'
\\  
    --no-apply-only-at-cron-interval \\  
    --target-locations '\[{"Accounts": \["**OU1-ID LIKE
ou-abcd-1qwert43**","**OU2-ID**","**OU3-ID**"\],"Regions": \["**REGION-1
like us-east-1**","**REGION-2**"\],"TargetLocationMaxConcurrency":
"4","TargetLocationMaxErrors": "4","ExecutionRoleName":
"SQLServerLTS-SystemsManager-AutomationExecutionRole"}\]'

This command will invoke the system to run it once immediately after it
is created. To update it to run on a scheduled basis using
--schedule-expression, see
[create-association](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/ssm/create-association.html)
in the AWS CLI Command Reference. 

### 

### Validating the execution ran successfully

After the association has triggered the automation, open the Systems
Manager console and from the left navigation pane, choose
***Automation***. In **Automation executions**, choose the most recent
execution of the *Primary-SQLSeverLicenseTrackingSolution-Document*, as
shown in Figure 4.

![](media/image5.png)

*Figure 4: Automation executions (management account)*

\[ALT TEXT: On the Executions tab, the Automation executions are
displayed in a table organized by execution ID, document name, status,
start time, end time, and executed by.\]

Depending on the number of Regions, accounts, and instances you execute
this solution against, a successful run of the execution looks like the
following:

![](media/image6.png)

*Figure 5: Automation execution detail (management account)*

\[ALT TEXT: On the Execution detail page for the primary Automation
document, there are sections for execution description, outputs, status,
and executed steps.\]

On the details page for the execution, choose any of the **step ID**s,
and then under **Outputs,** choose the **execution ID.** In the
**Outputs** section, you can find the *Automation execution ID* of the
secondary document in the member account, as shown in Figure 6.

![](media/image7.png) 

*Figure 6: Automation outputs (management account)*

\[ALT TEXT: In the Outputs section, there is text that says the
Secondary-SQLServerLicenseTrackingSolution-Document has been
successfully invoked. The text includes the AutomationExecutionId of the
secondary Automation document.\]

In the Systems Manager console, search for this ID in the member account
and Region. Choose the execution ID link to get more information about
the execution.

![](media/image8.png)

*Figure 7: Automation executions (member account)*

\[ALT TEXT: On the Executions tab, under Automation executions, the
secondary Automation document has a status of Success to indicate it was
successfully invoked.\]

To confirm that the license utilization data has been updated in AWS
License Manager, using the management account and selected Region, open
the **License Manager** console. Depending on the licenses consumed, the
**Customer managed licenses** list will look something like Figure 8:

![](media/image9.png)

*Figure 8: Customer managed licenses*

\[ALT TEXT: The customer managed licenses are displayed in a list
organized by license configuration name, status, license type, licenses
consumed, and account ID.\]

## Adding new accounts and Regions

The solution will automatically cover any new AWS accounts that you
provision under the OUs you specified when you created the association.
If you create new OUs or add Regions, you will need to update the
following solution components:

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

**Resource data sync**:

Add a new resource data sync in the account and Region as described
earlier in the post in “Centralizing Systems Manager Inventory data
using resource data sync.”

## Setup databases in Athena
Athena will help us query the aggregated data in the centralized S3
bucket created in the resource data sync step in part 1.

1.  In the Athena console, copy and paste the following statement into
    the query editor and then choose **Run Query**.

> CREATE DATABASE ssminventory

The console creates a database named ssminventory*, *a logical grouping
for the three tables you will be creating:

  - AWS\_InstanceDetailedInformation: Consists of an instance’s metadata
    like CPU, cores, and so on.

  - AWS\_Tag: Consists of all the tags defined for an instance.

  - Custom\_SQLServer: Consists of the SQL Server metadata, including
    edition and version, running on an instance.

For more information, see [Metadata collected by
inventory](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-inventory-schema.html)
in the AWS Systems Manager User Guide.

If you want to set up more inventory tables in Athena, see [Walkthrough:
Use resource data sync to aggregate inventory
data](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-inventory-resource-data-sync.html). 

2.  Copy and the following statement and paste it into the query editor.
    Replace DOC-EXAMPLE-BUCKET and bucket\_prefix** **with the name and
    prefix of the central Amazon S3 target created in part 1.
    Choose **Run Query**.

> CREATE EXTERNAL TABLE IF NOT EXISTS
> ssminventory.AWS\_InstanceDetailedInformation (  
> \`Cpus\` string,  
> \`osservicepack\` string,  
> \`cpuhyperthreadenabled\` string,  
> \`cpuspeedmhz\` string,  
> \`cpusockets\` string,  
> \`cpucores\` string,  
> \`cpumodel\` string,  
> \`resourceid\` string,  
> \`capturetime\` string,  
> \`schemaversion\` string  
> )  
> PARTITIONED BY (AccountId string, Region string, ResourceType
> string)  
> ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'  
> WITH SERDEPROPERTIES (  
> 'serialization.format' = '1'  
> ) LOCATION
> 's3://DOC-EXAMPLE-BUCKET/bucket\_prefix/AWS:InstanceDetailedInformation/'

3.  To partition the table, copy the following statement, paste it into
    the query editor, and then choose **Run Query**.

> MSCK REPAIR TABLE ssminventory.AWS\_InstanceDetailedInformation

**Note:** You will need to run this statement again as the partition
changes (for example, for new accounts, regions, or resource types).
Depending on how often these change in your organization, consider using
the [AWS Glue
crawler](https://docs.aws.amazon.com/glue/latest/dg/add-crawler.html) to
automate this step.

4.  To preview your data, choose **…** and then next to
    the AWS\_InstanceDetailedInformation table, choose **Preview
    table**.

5.  Run the following queries individually in the Athena console to set
    up the AWS\_Tag and Custom\_SQLServer tables.

> CREATE EXTERNAL TABLE IF NOT EXISTS ssminventory.AWS\_Tag (  
> \`key\` string,  
> \`value\` string,  
> \`resourceid\` string,  
> \`capturetime\` string,  
> \`schemaversion\` string  
> )  
> PARTITIONED BY (AccountId string, Region string, ResourceType
> string)  
> ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'  
> WITH SERDEPROPERTIES (  
> 'serialization.format' = '1'  
> ) LOCATION 's3://DOC-EXAMPLE-BUCKET/bucket\_prefix/AWS:Tag/'
> 
> MSCK REPAIR TABLE ssminventory.AWS\_Tag
> 
> CREATE EXTERNAL TABLE IF NOT EXISTS ssminventory.Custom\_SQLServer (  
> \`name\` string,  
> \`edition\` string,  
> \`version\` string,  
> \`resourceid\` string,  
> \`capturetime\` string,  
> \`schemaversion\` string  
> )  
> PARTITIONED BY (AccountId string, Region string, ResourceType
> string)  
> ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'  
> WITH SERDEPROPERTIES (  
> 'serialization.format' = '1'  
> ) LOCATION 's3://DOC-EXAMPLE-BUCKET/bucket\_prefix/Custom:SQLServer/'
> 
> MSCK REPAIR TABLE ssminventory.Custom\_SQLServer

## Visualize the data using QuickSight

Now that the data is available to access using Athena, you will use
QuickSight to visualize it. 

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

![](media/image2.png)

*Figure 2: Creating a dataset in QuickSight*

\[ALT TEXT: In the Quicksight console, various data sources are listed
to create a dataset.\]

2.  In the editor view, choose **Add data**, and then select the other
    tables as shown in Figure 3.

![](media/image3.png)

*Figure 3: QuickSight dataset editor*

\[ALT TEXT: In the QuickSight dataset editor, there are three tables
under ssminventory: aws\_tag, aws\_instancedetailedinformation, and
custom\_sqlserver.\]

3.  Update the join configuration using **resourceid** as the join
    clause, as shown in Figure 4.

![](media/image4.png)

*Figure 4: Specifying the join configuration*

\[ALT TEXT: In the QuickSight dataset editor, resourceid is used as the
join clause using an inner join type for aws\_tag,
aws\_instancedetailedinformation, and custom\_sqlserver.\]

4.  Before you apply the changes, exclude all duplicate fields and
    update the data types as shown in Figure 5. 

![](media/image5.png)

*Figure 5: Excluded fields*

\[ALT TEXT: There is a list of the 18 included fields and the 12
excluded fields.\]

You can use the dataset you just created to build your own analysis and
create visualizations as shown in Figure 6. To stay informed about
important changes in your data, you can create threshold alerts using
KPI and Gauge visuals in an Amazon QuickSight dashboard. For
information, see [Working with Threshold Alerts in Amazon
QuickSight](https://docs.aws.amazon.com/quicksight/latest/user/threshold-alerts.html).
With these alerts, you can set thresholds for your data and be notified
by email when your data crosses them. 

![](media/image6.png)

*Figure 6: QuickSight analysis*

\[ALT TEXT: In the QuickSight console, there are example visualization
charts created using the dataset. They include licenses consumed across
accounts, environments, region, and cost centers.\]

# Cleaning up resources

If you would like to remove the resources and solution after testing you
can clean up the resources deployed by the CloudFormation template using
the following instructions:

1.  In all Regions where the solution is deployed, modify the
    permissions for the secondary Automation document. For instructions,
    see [Modify permissions for a shared SSM
    document](https://docs.aws.amazon.com/systems-manager/latest/userguide/ssm-share-modify.html)
    in the AWS Systems Manager User Guide.

2.  Use the AWS CloudFormation console or AWS CLI to delete the main
    CloudFormation stack. When you delete the CloudFormation stack, all
    the solution components will be deleted.

3.  Use the [Systems Manager
    console](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-state-assoc-edit.html)
    or [AWS
    CLI](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/ssm/delete-association.html)
    to delete the association.

4.  Use the [Systems Manager
    console](https://docs.aws.amazon.com/systems-manager/latest/userguide/Explorer-using-resource-data-sync-delete.html)
    or [AWS
    CLI](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/ssm/delete-resource-data-sync.html)
    to delete the resource data syncs in all member accounts. Complete
    this step in each AWS Region where the solution is deployed.

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