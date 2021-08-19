# Use AWS License Manager and AWS Systems Manager to track Microsoft SQL Server licenses


Most enterprises find it hard to maintain control of the commercial licensing of Microsoft, SAP, Oracle, and IBM products due to limited visibility. They wind up over-provisioning licenses to avoid any hassle or under-provisioning licenses, only to be faced with steep penalties. 

If your enterprise uses AWS, you can address this challenge in two ways:

* Using license-included instances allows you access to fully compliant licenses, where AWS handles the tracking and management for you. With this option, you pay as you go, with no upfront costs or long-term investment.
* AWS License Manager [AWS License Manager](https://aws.amazon.com/systems-manager/features/) makes it easy for you to set rules to manage, discover, and report software license usage. When you use AWS License Manager to associate an Amazon Machine Image (AMI) with a licensing configuration, you can track the use of licenses in AWS or your on-premises environment. You can also set rules in AWS License Manager to prevent licensing violations to help you stay compliant.

It’s still possible that your teams might provision software products not governed by these two options, which means you could receive an unwanted surprise in the next audit. 

We show you how to build a solution that discovers and tracks your Microsoft SQL Server BYOL instances. You can enhance this approach to target other commercial software such as Oracle, SAP, or IBM. There are two solutions that you could leverage depending your environment and use-case:
* [Tracking in a single account](https://github.com/aws-samples/systems-manager-license-manager-license-tracker-for-sql-server/tree/main/single-account)
* [Tracking across multiple accounts and regions](https://github.com/aws-samples/systems-manager-license-manager-license-tracker-for-sql-server/tree/main/multi-account-region)
