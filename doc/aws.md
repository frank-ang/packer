# Filecoin Packer Appliance on AWS

![Filecoin Packer Appliance on AWS](./PackerAWS.drawio.png)

## Purpose

To archive source data from AWS S3, AWS EFS, into a CAR set that can be downloaded via HTTP.  

## Usage.

To launch:

> Deploy the Cloudformation stack into an AWS account: 
> [TODO: Console quick-launch link to CloudFormation yaml on S3](TODO-insert-link)

Enter parameters into the cloudformation stack:

[TODO screenshot of cloudformation stack parameters](TODO-insert-link)

The AWS Cloudformation stack creation time should be well within 10 minutes. 
Upon successful creation the instance IP address of the appliance can be found in the stack output.


## Security

Encryption keys should be stored in AWS Secrets Manager in RSA PEM format.

## Cost of operation

Time required to pack 1PiB of data using 1 instance of r5d.2xlarge type, source data from EFS, @120GB/hr.
* 
* 