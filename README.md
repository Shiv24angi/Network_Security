### Network Security Projects For Phising Data

Setup github secrets:
AWS_ACCESS_KEY_ID= AKIASFUIR2K7DIOVWS6N

AWS_SECRET_ACCESS_KEY= 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

AWS_REGION = us-east-1

AWS_ECR_LOGIN_URI = 149536494270.dkr.ecr.us-east-1.amazonaws.com/networksecurity
ECR_REPOSITORY_NAME = networkssecurity


Docker Setup In EC2 commands to be Executed
#optinal

sudo apt-get update -y

sudo apt-get upgrade

#required

curl -fsSL https://get.docker.com -o get-docker.sh

sudo sh get-docker.sh

sudo usermod -aG docker ubuntu

newgrp docker