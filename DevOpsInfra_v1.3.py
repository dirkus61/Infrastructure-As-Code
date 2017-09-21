#!/usr/bin/python

##Super Simple Build DEVOps Demo using Python, Boto3 and AWS   

#Create VPC 
#Create 2 Subnets, One Public and one Private 
#Create 1 Internet Gateway (IGW)
#Associate 1 Elastic IP (EIP) 
#Create 1 NAT Gateway 
#Modify Route Tables to Include 1 per Subnet 
#Create DevOpsInstances within Subnet


#IMPORT NECESSARY LIBARIES 
import boto3
import ConfigParser
import time

#SETUP SESSION INFO FOR BOTH CLIENT MODE AND RESOURCE MODE 
#NOTE: There are a couple of options to store and consume AWS credentials. 
#NOTE: This example uses a local file to store aws_access_key and aws_secret_access. 

configParser = ConfigParser.RawConfigParser()
configFilePath = r'<your-path>.aws/creds'
configParser.read(configFilePath)

mykey = configParser.get('global','key')
mysecretkey = configParser.get('global','secretkey')
myregion = configParser.get('config','region')

ec2client = boto3.client('ec2',
                aws_access_key_id=mykey,
                aws_secret_access_key=mysecretkey,
                region_name=myregion)

ec2resource = boto3.resource('ec2',
                aws_access_key_id=mykey,
                aws_secret_access_key=mysecretkey,
                region_name=myregion)

ec2 = boto3.resource('ec2',
                aws_access_key_id=mykey,
                aws_secret_access_key=mysecretkey,
                region_name=myregion)

##Create VPC 
#Use ec2 client method to create new VPC

vpc_response = ec2client.create_vpc(CidrBlock='10.50.0.0/16')

#Store VPC ID n variable for later use 

new_vpc_id = vpc_response["Vpc"]["VpcId"]

#Create a VPC object using ec2 resource object method 

new_vpc = ec2resource.Vpc(new_vpc_id) 

##Create Subnets 
###Reuse the VPC object created above to create Private and Public Subnets 

public_subnet = new_vpc.create_subnet(
  CidrBlock='10.50.1.0/24'
)
private_subnet = new_vpc.create_subnet(
  CidrBlock='10.50.2.0/24'
)

##Create InternetGateway (IGW) using ec2 client method and store new igw id.  Then attach to VPC.

igw_response = ec2client.create_internet_gateway()

igw_id = (igw_response["InternetGateway"]["InternetGatewayId"])

new_vpc.attach_internet_gateway(InternetGatewayId=igw_id)

##Allocate Elastic IP (EIP) using ec2 client method and store EIP allocation ID  

elip_response = ec2client.allocate_address(Domain='vpc')

elip_allocationid = elip_response["AllocationId"]

##Create NAT Gateway (NGW)using ec2 client method, assoc EIP with NAT Gateway using Public subnet 
#Store NGW ID 

ngw_response = ec2client.create_nat_gateway(
  SubnetId=public_subnet.subnet_id,
  AllocationId = elip_allocationid
)

ngw_id = ngw_response["NatGateway"]["NatGatewayId"]

##Modify Route Tables using ec2 client method.  Create 2 new tables on subnets
#Modify Public Route Table

public_rtb_response = ec2client.create_route_table(
  VpcId=new_vpc_id
)

public_rtb_id = public_rtb_response["RouteTable"]["RouteTableId"]

#Create resource object for Public routing table using resource object method

public_rtb = ec2resource.RouteTable(public_rtb_id)

#Add route entries to each table, Public subnet. Traffic goes to Internet Gateway 

pub_route1 = public_rtb.create_route(
  DestinationCidrBlock='0.0.0.0/0',
  GatewayId=igw_id
)

#Associate Public route table to Public subnet

pub_assoc = public_rtb.associate_with_subnet(
  SubnetId=public_subnet.subnet_id
)

##Modify Public Route Table

private_rtb_response = ec2client.create_route_table(
  VpcId=new_vpc_id
)

private_rtb_id = private_rtb_response["RouteTable"]["RouteTableId"]

#Create resource object for Private routing table using resource object method 

private_rtb = ec2resource.RouteTable(private_rtb_id)

##Allow hosts on Private subnet to access outbound access thru NAT Gateway 
#Meanwhile add a sleep to allow NAT Gatway to finish building before invoked below...

time.sleep(60)

priv_route1 = private_rtb.create_route(
  DestinationCidrBlock='0.0.0.0/0',
  NatGatewayId=ngw_id
)

priv_assoc = private_rtb.associate_with_subnet(
 SubnetId=private_subnet.subnet_id
)

#Create DevOps Server Instances in Private Subnet 
#NOTE: Substitute your keypair name - KeyName='<your-AWS-key>'

instances = ec2.create_instances(
	ImageId='ami-1efdd908',
	MinCount=1,
	MaxCount=5,
	KeyName='<your-AWS-key>',
	InstanceType='t2.nano',
	SubnetId=private_subnet.subnet_id
)


##Tag all the "taggable" resources created nice and neat 
#Create a tag list
tag_list = [
  {'Key':'Creator','Value':'NateB'},
  {'Key':'Project','Value':'DevOpsInfra v1.3'}
]

# Tag resources using ec2 client method 

ec2client.create_tags(
  Resources=[
   new_vpc_id, 
   public_subnet.subnet_id,
   private_subnet.subnet_id,
   igw_id,
   public_rtb_id,
   private_rtb_id
  ],
  Tags=tag_list
)
 
