# teacher_pay_dash

Go to https://teacher-pay-dash.apps.sjtrny.com/

# Instructions

## Build

`docker build -t teacher-pay-dash .`

## Run

`docker run --name teacher-pay-dash -d -p 8080:80 teacher-pay-dash`

## tar

`tar --exclude-vcs -czf file.tar --exclude file.tar .`
